from decimal import Decimal

from django.contrib import admin

from .models import Order, OrderItem, PurchaseLog, PurchaseLogOrder


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


class PurchaseLogItemInline(admin.TabularInline):
    model = PurchaseLog
    extra = 0
    can_delete = False
    fields = ('product', 'quantity', 'created_at')
    readonly_fields = ('product', 'quantity', 'created_at')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(PurchaseLogOrder)
class PurchaseLogAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'email', 'full_name', 'logged_items', 'created_at')
    search_fields = ('order_number', 'email', 'full_name')
    list_filter = ('created_at',)
    fields = ('order_number', 'full_name', 'email', 'status', 'created_at')
    readonly_fields = ('order_number', 'full_name', 'email', 'status', 'created_at')
    inlines = [PurchaseLogItemInline]

    def get_queryset(self, request):
        return super().get_queryset(request).filter(purchase_logs__isnull=False).distinct()

    @admin.display(description='Items')
    def logged_items(self, obj):
        return obj.purchase_logs.count()

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
