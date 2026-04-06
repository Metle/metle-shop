from django.db import IntegrityError, models, transaction
from django.utils import timezone

from accounts.models import Customer
from store.models import Product


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('cancelled', 'Cancelled'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    order_number = models.CharField(max_length=13, unique=True, editable=False, blank=True)
    email = models.EmailField()
    full_name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    delivery_option = models.CharField(max_length=20, blank=True)
    delivery_address = models.TextField(blank=True)
    payment_option = models.CharField(max_length=20, blank=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.order_number or f"Order {self.id}"

    @classmethod
    def _generate_next_order_number(cls) -> str:
        year = timezone.now().year
        prefix = f"00{year}"
        last_order_number = (
            cls.objects.filter(order_number__startswith=prefix)
            .order_by('-order_number')
            .values_list('order_number', flat=True)
            .first()
        )
        last_increment = int(last_order_number[-4:]) if last_order_number else 0
        return f"{prefix}{last_increment + 1:04d}"

    def _record_purchase_log(self):
        items = self.items.select_related('product')
        if not items.exists():
            return
        with transaction.atomic():
            PurchaseLog.objects.bulk_create(
                [
                    PurchaseLog(order=self, product=item.product, quantity=item.quantity)
                    for item in items
                ]
            )

    def save(self, *args, **kwargs):
        previous_status = None
        if self.pk:
            previous_status = Order.objects.filter(pk=self.pk).values_list('status', flat=True).first()

        if self._state.adding and not self.order_number:
            for _ in range(10):
                self.order_number = self._generate_next_order_number()
                try:
                    with transaction.atomic():
                        super().save(*args, **kwargs)
                    break
                except IntegrityError:
                    self.order_number = ''
            else:
                raise
        else:
            super().save(*args, **kwargs)

        if self.status == 'paid' and previous_status != 'paid':
            self._record_purchase_log()

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def line_total(self):
        return self.quantity * self.unit_price


class PurchaseLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='purchase_logs')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Order {self.order_id} - {self.product} ({self.quantity})"
