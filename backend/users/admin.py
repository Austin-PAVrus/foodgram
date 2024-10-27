from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import FoodgramUser, Subscription


class FoodgramUserAdmin(UserAdmin):
    search_fields = ('username', 'email')
    fieldsets = UserAdmin.fieldsets + (
        ('Разграничение прав', {'fields': ('role',)}),
    )


admin.site.register(FoodgramUser, FoodgramUserAdmin)
admin.site.register(Subscription)
