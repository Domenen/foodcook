from django.contrib import admin
from django.contrib.auth.models import Group
from rest_framework import serializers
from rest_framework.authtoken.models import TokenProxy

from .models import User, Subscription


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('pk', 'email', 'username', 'first_name',
                    'last_name', 'password')
    list_filter = ('username', 'email')
    search_fields = ('username', 'email', 'first_name', 'last_name')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author')
    list_filter = ('user', 'author')
    search_fields = ('user', 'author')

    def save_form(self, request, form, formset, change):
        if form.user == form.author:
            return super().save_form(
                request, form, formset=None, change=change
            )
        return super().save_form(request, form, formset, change)


admin.site.unregister(Group)
admin.site.unregister(TokenProxy)
