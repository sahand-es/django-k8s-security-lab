from django.contrib import admin

from .models import Org, Report, User

admin.site.register(Org)
admin.site.register(Report)
admin.site.register(User)
