from django.contrib import admin
from django.contrib.auth.models import Group
from django.forms import BaseModelFormSet, ModelForm
from django.http import HttpRequest
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

    def save_formset(self, request: HttpRequest, form: ModelForm, formset: BaseModelFormSet, change: bool) -> None:
        if formset.user == formset.author:
            return formset.save(commit=False)
        else: 
            return super().save_formset(request, form, formset, change)


admin.site.unregister(Group)
admin.site.unregister(TokenProxy)
