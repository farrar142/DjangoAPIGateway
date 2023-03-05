from django.contrib import admin, messages

from django.template.response import TemplateResponse
from django.urls import path
from django.shortcuts import redirect, get_object_or_404

# Register your models here.

from .models import Api, Consumer, Upstream, Target


class APIAdmin(admin.ModelAdmin):
    ordering = ("upstream", "request_path")
    list_filter = ("upstream", "plugin")


class TargetInline(admin.TabularInline):
    model = Target


class UpstreamAdmin(admin.ModelAdmin):
    inlines = [
        TargetInline,
    ]
    readonly_fields = ("total_weight",)
    fields = ("total_weight", "alias", "host", "scheme", "weight", "load_balance")

    def get_queryset(self, request):
        queryset = super(UpstreamAdmin, self).get_queryset(request)
        queryset = queryset.prefetch_related("targets")
        return queryset

    def __init__(self, model, admin_site) -> None:
        super().__init__(model, admin_site)


class TargetAdmin(admin.ModelAdmin):
    ordering = ("upstream",)
    list_filter = ("upstream",)
    list_display = ("__str__", "enabled", "toggle_button")

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "<int:pk>/toggle-enabled",
                self.toggle_enabled,
                name="admin_toggle_enabled",
            ),
        ]
        return my_urls + urls

    def toggle_enabled(self, request, pk):
        # ...
        context = dict(
            # Include common variables for rendering the admin template.
            self.admin_site.each_context(request),
            # Anything else you want in the context...
        )

        # Get the scenario to activate
        target = get_object_or_404(Target, pk=pk)
        # It is already activated
        target.enabled = not target.enabled
        target.save()
        result = "Activated" if target.enabled else "Deactivated"
        msg = f"{result} Target '{target}'"
        self.message_user(request, msg, level=messages.INFO)
        return redirect(request.META.get("HTTP_REFERER"))


# Register your models here.
admin.site.register(Api, APIAdmin)
admin.site.register(Consumer)
# admin.site.register(Upstream)
admin.site.register(Upstream, UpstreamAdmin)
admin.site.register(Target, TargetAdmin)
