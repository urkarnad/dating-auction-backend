from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'is_staff',)
    list_filter = ('is_banned', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    fieldsets = UserAdmin.fieldsets + (
        ("Moderation", {"fields": ("is_banned",)}),
    )