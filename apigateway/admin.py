from django.contrib import admin

# Register your models here.

from .models import Api, Consumer,Upstream

# Register your models here.
admin.site.register(Api)
admin.site.register(Consumer)
admin.site.register(Upstream)
