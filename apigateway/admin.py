from django.contrib import admin

# Register your models here.

from .models import Api, Consumer

# Register your models here.
admin.site.register(Api)
admin.site.register(Consumer)
