# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib import admin

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_groups')

    def get_groups(self, obj):
        return "\n".join([g.name for g in obj.groups.all()])

    get_groups.short_description = 'Groups'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

