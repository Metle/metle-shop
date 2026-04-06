from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('email', 'full_name', 'mobile_number', 'language', 'currency', 'created_at')
    search_fields = ('email', 'full_name', 'mobile_number', 'language', 'currency')
