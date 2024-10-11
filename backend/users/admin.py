from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import TokenProxy

from .models import User, Subscription


@admin.register(User)
class UserAdmin(DefaultUserAdmin):
    list_display = ('pk', 'email', 'username', 'first_name',
                    'last_name', 'password')
    list_filter = ('username', 'email')
    search_fields = ('username', 'email', 'first_name', 'last_name')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author')
    list_filter = ('user', 'author')
    search_fields = ('user', 'author')


admin.site.unregister(Group)
admin.site.unregister(TokenProxy)
