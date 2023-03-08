import requests
from itertools import accumulate
from random import randint
from typing import TYPE_CHECKING, TypeVar, Callable

from django.db import models

from .consts import SCHEME_DELIMETER
from .caches import cache
from .exceptions import TimeoutException

if TYPE_CHECKING:
    from .models import Api


class SchemeType(models.TextChoices):
    HTTP = "http"
    HTTPS = "https"
    UNITX = "http+unix"


class LoadBalancingType(models.TextChoices):
    ROUND_ROBIN = "round_robin"
    WEIGHT_ROBIN = "weight_robin"


"""
1. 로드 밸런싱 기능
2. 다른 Target으로 Retry기능
"""


class ServerConnectionRecord:
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

    host = models.CharField(max_length=255)
    scheme = models.CharField(
        max_length=64, choices=SchemeType.choices, default=SchemeType.HTTP
    )
    weight = models.PositiveIntegerField(default=100)

    @property
    def full_path(self):
        return f"{self.scheme}{SCHEME_DELIMETER}{self.host}"


class ChildNode(Node):
    class Meta:
        abstract = True

    enabled = models.BooleanField("활성화", default=True)


TNode = TypeVar("TNode", bound=Node)
TCNode = TypeVar("TCNode", bound=ChildNode)


class LoadBalancer(ServerConnectionRecord, Node):
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

    def call(self):
        cache.add(self.req_key, 0)
        return cache.incr(self.req_key, 1)

    def round_robin(
        self, req_count: int, targets: list["TNode"], target_count: int
    ) -> Node:
        cur_idx = req_count % target_count
        return targets[cur_idx - 1]

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

    def load_balancing(self) -> Node:
        req_count = self.call()
        targets = list(filter(lambda x: x.enabled, self.targets.all()))
        target_count = len(targets)
        if target_count == 0:
            return self
        func = self.round_robin
        if self.load_balance == LoadBalancingType.WEIGHT_ROBIN:
            func = self.weight_round
        return func(req_count, targets, target_count)

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
            if self.retries < retries:
                raise TimeoutException
            try:
                node = self.load_balancing()
                url = node.full_path + api.wrapped_path + trailing_path
                return self.method_map[method](
                    url, headers=headers, data=data, files=files, timeout=self.timeout
                )
            except Exception as e:
                print("error", e)
                return sender(retries + 1)

        return sender(retries)
