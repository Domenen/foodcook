from django.core.exceptions import ValidationError
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.models import Group
from django.forms import ModelForm
from django.http import HttpRequest
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

    def save_model(self, request, obj, form, change):
        if obj.user == obj.author:
            raise ValidationError('Нельзя подписать пользователя на самого себя!')
        return super().save_model(request, obj, form, change)


admin.site.unregister(Group)
admin.site.unregister(TokenProxy)
