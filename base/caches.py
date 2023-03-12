from typing import Protocol, Generic, List, Optional
from typing import TypeVar, Generic
from .wrappers import cache


class QueryBase(Protocol):
    pk: int


# T = TypeVar("T", bound=Union[Mapping[str, Any], QueryBase])
T = TypeVar("T", bound=QueryBase)
LT = TypeVar("LT", bound=List[QueryBase])


class CacheBase:
    def __init__(self, user_id: int, model_name: str):
        self.user_id = user_id
        self.model_name = model_name
        self.global_key = f"*/{model_name}:*:end"

    def _make_key(self, key: str):
        return f"{self.user_id}/{self.model_name}:{key}:end"

    def get_global_keys(self):
        # 글로벌 키스토어의 모든 키 추가
        # 해당 모델의 유저에 대한 모든 키들을 반환
        return cache.keys(self.global_key)

    def key(self, kwargs: dict):
        _dict = {}
        translated: List[str] = []
        for k, v in sorted(kwargs.items(), key=lambda x: x[0]):
            try:
                _dict[k] = str(v)
                translated.append(f"{k}={str(v)}")
            except:
                _dict[k] = v
        return self._make_key(":".join(translated))

    def purge(self, **kwargs):
        # 캐시된 데이터를 지웁니다
        key = self.key(kwargs)
        # self.purge_global_keys(key)
        cache.delete(key)

    def purge_by_regex(self, **kwargs):
        key = self.key(kwargs)
        cache.delete_many(cache.keys(key))

    def purge_global_key(self):
        # 해당 모델의 유저에 대한 모든 키들을 삭제
        cache.delete_many(self.get_global_keys())


class UseSingleCache(CacheBase, Generic[T]):
    def get(self, **kwargs) -> Optional[T]:
        key = self.key(kwargs)
        # self.add_global_keys(key)
        search = cache.keys(key)
        if 0 < len(search):
            search_key = search[0]
        else:
            search_key = key
        return cache.get(search_key, None)

    def set(self, value: T, timeout: Optional[int] = None, **kwargs) -> T:
        # 모든 캐시 데이터를 오버라이드합니다
        key = self.key(kwargs)
        # self.add_global_keys(key)
        cache.set(key, value=value, timeout=timeout)
        return value

    def add(self, value: T, timeout: Optional[int] = None, **kwargs) -> T:
        # 모든 캐시 데이터를 오버라이드합니다
        key = self.key(kwargs)
        # self.add_global_keys(key)
        cache.add(key, value=value, timeout=timeout)
        return value
