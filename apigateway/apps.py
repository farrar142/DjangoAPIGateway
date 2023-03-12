from threading import Thread
from django.apps import AppConfig

from base.consts import DAY, MINUTE
from base.caches import cache, UseSingleCache


def warm_cache():
    from .models import Api

    is_running = cache.get("warm_up", False)
    if is_running:
        print("최근에 수행된 캐시 작업이 있습니다.")
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
