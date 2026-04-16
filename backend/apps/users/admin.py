from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.users.models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    '''Extends Django's built-in UserAdmin with the role field'''

    fieldsets = UserAdmin.fieldsets + (  # type: ignore[operator]
        ('Role', {'fields': ('role',)}),
    )
    list_display = ['username', 'email', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email']
