from decimal import Decimal

from django import forms
from django.contrib import admin, messages
from django.middleware.csrf import get_token
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html

from .models import Order, OrderItem, PurchaseLog, PurchaseLogOrder

# Statuses that lock the order from further edits.
LOCKED_STATUSES = ('completed', 'canceled')


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


class DateTimeLocalInput(forms.DateTimeInput):
    input_type = 'datetime-local'

    def __init__(self, attrs=None, format=None):
        super().__init__(attrs=attrs, format=format or '%Y-%m-%dT%H:%M')


class PurchaseLogOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseLogOrder
        fields = ('status', 'window_start', 'window_end')
        widgets = {
            'window_start': DateTimeLocalInput(),
            'window_end': DateTimeLocalInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Accept the value the datetime-local input posts back.
        for name in ('window_start', 'window_end'):
            self.fields[name].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S']

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        start = cleaned_data.get('window_start')
        end = cleaned_data.get('window_end')
        if status in ('ready for pickup', 'delivery scheduled') and not (start and end):
            raise forms.ValidationError(
                'A start and end time are required when the status is '
                '"ready for pickup" or "delivery scheduled".'
            )
        if start and end and end <= start:
            self.add_error('window_end', 'The end time must be after the start time.')
        return cleaned_data


@admin.register(PurchaseLogOrder)
class PurchaseLogAdmin(admin.ModelAdmin):
    form = PurchaseLogOrderForm
    list_display = (
        'order_number', 'email', 'full_name', 'status', 'delivery_option',
        'window_start', 'window_end', 'logged_items', 'created_at',
        'complete_button', 'cancel_button',
    )
    search_fields = ('order_number', 'email', 'full_name')
    list_filter = ('status', 'created_at')
    fields = (
        'order_number', 'full_name', 'email', 'delivery_option', 'delivery_address',
        'status', 'window_start', 'window_end', 'created_at',
    )
    readonly_fields = (
        'order_number', 'full_name', 'email', 'delivery_option', 'delivery_address',
        'created_at',
    )
    inlines = [PurchaseLogItemInline]

    def get_queryset(self, request):
        self._request = request
        return super().get_queryset(request).filter(purchase_logs__isnull=False).distinct()

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                '<int:pk>/mark-completed/',
                self.admin_site.admin_view(self.mark_completed),
                name='orders_purchaselogorder_mark_completed',
            ),
            path(
                '<int:pk>/mark-canceled/',
                self.admin_site.admin_view(self.mark_canceled),
                name='orders_purchaselogorder_mark_canceled',
            ),
        ]
        return custom + urls

    def mark_completed(self, request, pk):
        if request.method == 'POST':
            order = Order.objects.filter(pk=pk).first()
            if order is None:
                self.message_user(request, 'Order not found.', messages.ERROR)
            elif order.status == 'completed':
                self.message_user(request, 'Order is already completed.', messages.WARNING)
            elif order.status == 'canceled':
                self.message_user(request, 'A canceled order cannot be completed.', messages.ERROR)
            else:
                order.status = 'completed'
                order.save(update_fields=['status'])
                self.message_user(
                    request, f'Order {order.order_number} marked as completed.', messages.SUCCESS
                )
        return redirect('admin:orders_purchaselogorder_changelist')

    def mark_canceled(self, request, pk):
        if request.method == 'POST':
            order = Order.objects.filter(pk=pk).first()
            if order is None:
                self.message_user(request, 'Order not found.', messages.ERROR)
            elif order.status == 'canceled':
                self.message_user(request, 'Order is already canceled.', messages.WARNING)
            elif order.status == 'completed':
                self.message_user(request, 'A completed order cannot be canceled.', messages.ERROR)
            else:
                order.status = 'canceled'
                order.save(update_fields=['status'])
                self.message_user(
                    request,
                    f'Order {order.order_number} canceled; stock returned.',
                    messages.SUCCESS,
                )
        return redirect('admin:orders_purchaselogorder_changelist')

    @admin.display(description='Items')
    def logged_items(self, obj):
        return obj.purchase_logs.count()

    @admin.display(description='Complete')
    def complete_button(self, obj):
        if obj.status in ('completed', 'canceled'):
            return obj.get_status_display()
        url = reverse('admin:orders_purchaselogorder_mark_completed', args=[obj.pk])
        return format_html(
            '<form method="post" action="{}" style="margin:0;">'
            '<input type="hidden" name="csrfmiddlewaretoken" value="{}">'
            '<button type="submit" class="button">Completed</button>'
            '</form>',
            url, get_token(self._request),
        )

    @admin.display(description='Cancel')
    def cancel_button(self, obj):
        if obj.status in ('completed', 'canceled'):
            return ''
        url = reverse('admin:orders_purchaselogorder_mark_canceled', args=[obj.pk])
        return format_html(
            '<form method="post" action="{}" style="margin:0;">'
            '<input type="hidden" name="csrfmiddlewaretoken" value="{}">'
            '<button type="submit" class="button" style="background:#ba2121;">Cancel</button>'
            '</form>',
            url, get_token(self._request),
        )

    def get_readonly_fields(self, request, obj=None):
        if obj is not None and obj.status in LOCKED_STATUSES:
            return self.fields
        return self.readonly_fields

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.status in LOCKED_STATUSES:
            return False
        return super().has_change_permission(request, obj)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
