from django.apps import AppConfig
from common_module.caches import UseSingleCache


def warm_cache():
    from .models import Api

    api_cache = UseSingleCache(0, "api")
    for api in Api.objects.prefetch_related("upstream", "upstream__targets").iterator():
        print("set", api)
        api_cache.set(
            api, 3600 * 24 * 30, path=api.request_path, upstream=api.upstream.pk
        )


class ApigatewayConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apigateway"

    def ready(self) -> None:
        warm_cache()
