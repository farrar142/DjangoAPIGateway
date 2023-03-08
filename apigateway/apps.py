from threading import Thread
from django.apps import AppConfig

from .consts import DAY, MINUTE
from .caches import cache, UseSingleCache


def warm_cache():
    from .models import Api

    is_running = cache.get("warm_up", False)
    if is_running:
        print("캐싱작업 진행중 태스크를 종료합니다")
        return
    cache.set("warm_up", True, 2 * MINUTE)
    api_cache = UseSingleCache(0, "api")
    for api in Api.objects.prefetch_related("upstream", "upstream__targets").iterator():
        print("set", api)
        api_cache.set(api, 30 * DAY, path=api.request_path, upstream=api.upstream.pk)


class ApigatewayConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apigateway"

    def ready(self) -> None:
        thread = Thread(target=warm_cache)
        thread.start()
