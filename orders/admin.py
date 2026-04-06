from decimal import Decimal

from django.contrib import admin

from .models import Order, OrderItem, PurchaseLog


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'full_name', 'status', 'order_total', 'delivery_option', 'payment_option', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('email', 'full_name')
    inlines = [OrderItemInline]

    @admin.display(description='Total')
    def order_total(self, obj):
        subtotal = Decimal('0.00')
        for item in obj.items.all():
            line_total = item.line_total()
            product_discount = item.product.discount if item.product else Decimal('0.00')
            discounted_line = line_total * (1 - (product_discount / 100))
            subtotal += discounted_line
        order_discount = obj.discount or Decimal('0.00')
        total = subtotal * (1 - (order_discount / 100))
        return max(total, Decimal('0.00'))


@admin.register(PurchaseLog)
class PurchaseLogAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'created_at')
    search_fields = ('order__id', 'product__name', 'product__sku')
    list_filter = ('created_at',)
