import requests
from itertools import accumulate
from random import randint
from typing import TYPE_CHECKING, TypeVar, Callable

from django.db import models

from base.consts import SCHEME_DELIMETER
from base.exceptions import TimeoutException
from base.caches import cache, UseSingleCache

if TYPE_CHECKING:
    from .models import Api


class SchemeType(models.TextChoices):
    HTTP = "http"
    HTTPS = "https"


class LoadBalancingType(models.TextChoices):
    ROUND_ROBIN = "round_robin"
    WEIGHT_ROBIN = "weight_robin"


"""
1. 로드 밸런싱 기능
2. 다른 Target으로 Retry기능
"""

# 연결중인 커넥션의 수를 컨트롤하는 믹스인 클래스
class ServerConnectionRecorder:
    pk: int

    @property
    def conn_key(self):
        return f"upstream:{self.pk}-connection"

    def get_conn(self):
        return cache.get(self.conn_key, 0)

    def incr_conn(self):
        # 현재 업스트림에 연결된 커넥션 수를 증가시킵니다
        cache.add(self.conn_key, 0)
        return cache.incr(self.conn_key, 1)

    def decr_conn(self):
        # 현재 업스트림에 연결된 커넥션 수를 감소시킵니다
        try:
            cache.add(self.conn_key, 1)
            return cache.decr(self.conn_key, 1)
        except:
            return 0


class Node(models.Model):
    class Meta:
        abstract = True

    host = models.CharField(
        max_length=255
    )  # ex) 192.168.0.14,localhost,172.17.0.1,host.docker.internal
    scheme = models.CharField(
        max_length=64, choices=SchemeType.choices, default=SchemeType.HTTP
    )
    weight = models.PositiveIntegerField(default=100)  # 가중치 기반의 분산 알고리즘에 사용될 가중치

    @property
    def full_path(self):
        return f"{self.scheme}{SCHEME_DELIMETER}{self.host}"  # 해당 노드의 전체 url

    def save(self, *args, **kwargs) -> None:
        res = super().save(*args, **kwargs)
        single_cache = UseSingleCache(0, "api")
        # 해당 모델에 변경이 가해지면 해당 업스트림에 연결된 모든 api 캐시를 삭제
        single_cache.purge_by_regex(upstream=self.pk, path="*")
        return res

    def delete(self, *args, **kwargs):
        result = super().delete(*args, **kwargs)
        single_cache = UseSingleCache(0, "api")
        # 해당 모델에 변경이 가해지면 해당 업스트림에 연결된 모든 api 캐시를 삭제
        single_cache.purge_by_regex(upstream=self.pk, path="*")
        return result


# 분산부하의 타겟이 될 노드
class ChildNode(Node):
    class Meta:
        abstract = True

    enabled = models.BooleanField("활성화", default=True)


TNode = TypeVar("TNode", bound=Node)
TCNode = TypeVar("TCNode", bound=ChildNode)


# 실제 로드밸런싱을 수행하는 로직을 담은 베이스 클래스
class LoadBalancer(ServerConnectionRecorder, Node):
    class Meta:
        abstract = True

    load_balance = models.CharField(
        max_length=64,
        default=LoadBalancingType.ROUND_ROBIN,
        choices=LoadBalancingType.choices,
    )

    retries = models.PositiveIntegerField(default=0)
    timeout = models.PositiveIntegerField(default=10)

    targets: models.Manager["TCNode"]  # type:ignore

    method_map: dict[str, Callable[..., requests.Response]] = {
        "get": requests.get,
        "post": requests.post,
        "put": requests.put,
        "patch": requests.patch,
        "delete": requests.delete,
    }

    @property
    def req_key(self):
        return f"upstream:{self.pk}-called"

    # round_robin을 수행하기위해 현재 node가 불린 횟수를 기록
    def call(self):
        cache.add(self.req_key, 0)
        return cache.incr(self.req_key, 1)

    # 모든 노드들을 순차적으로 반환
    def round_robin(
        self, req_count: int, targets: list["TNode"], target_count: int
    ) -> Node:
        cur_idx = req_count % target_count + 1
        return [*targets, self][cur_idx - 1]

    # 모든 노드들의 가중치를 누적하고 [50, 100, 250, 300] - > [50, 150, 400, 700]
    # 0~최대 누적값 사이의 랜덤숫자를 생성해 해당 범위에 포함되는 노드를 반환
    def weight_round(
        self, req_count: int, targets: list["TNode"], target_count: int
    ) -> Node:
        max = sum(map(lambda x: x.weight, targets))
        accs = accumulate(map(lambda x: x.weight, targets))
        zipped = list(zip(accs, targets))

        rand = randint(0, max)

        def find(node: tuple[int, Node]):
            weight = node[0]
            return rand < weight

        node = next(filter(find, zipped), (0, self))
        return node[1]

    # 실제 로드밸런싱을 수행하는 로직
    def load_balancing(self) -> Node:
        req_count = self.call()
        # 이미 prefetch_related로 쿼리를 해왔기 때문에 filter를 사용하여 다시 쿼리를 발생시키지 않음
        # 활성화 되어있는 타겟 노드들만 반환
        targets = list(filter(lambda x: x.enabled, self.targets.all()))
        target_count = len(targets)
        if target_count == 0:
            return self  # 모든 타겟 노드가 비 활성화 상태 일 시 자신을 반환
        func = self.round_robin
        if self.load_balance == LoadBalancingType.WEIGHT_ROBIN:
            func = self.weight_round
        return func(req_count, targets, target_count)

    # API 요청,반환 로직을 수행하는 메서드
    # retry를 실행하는 메서드
    def send_request(
        self,
        api: "Api",
        trailing_path: str,
        method: str,
        headers=None,
        data=None,
        files=None,
    ):
        retries = -1

        def sender(retries=0) -> requests.Response:
            # timeout되면 504에러를 반환
            if self.retries < retries:
                raise TimeoutException
            try:
                node = self.load_balancing()  # LB로직을 수행하여 나온 노드를 반환
                url = node.full_path + api.wrapped_path + trailing_path
                # 노드의 전체 url과 랩된 주소, 나머지 주소를 결합하여 실제 요청을 보낼 주소를 반환
                return self.method_map[method](
                    url, headers=headers, data=data, files=files, timeout=self.timeout
                )
            except Exception as e:
                print("error", e)
                return sender(retries + 1)

        return sender(retries)
