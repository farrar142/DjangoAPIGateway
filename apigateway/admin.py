from django.contrib import admin

# Register your models here.

from .models import Api, Consumer, Upstream


class APIAdmin(admin.ModelAdmin):
    ordering = ("upstream", "request_path")
    list_filter = ("upstream",)


# Register your models here.
admin.site.register(Api, APIAdmin)
admin.site.register(Consumer)
admin.site.register(Upstream)
