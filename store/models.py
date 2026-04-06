from django.conf import settings
from django.apps import apps
from django.db import models
from django.db.models import Sum
import decimal


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=140, unique=True)

    def __str__(self) -> str:
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=200, unique=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    sku = models.CharField(max_length=255, unique=True)
    image_url = models.CharField(max_length=255, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    weight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    unit_weight = models.CharField(max_length=32, blank=True)
    quantity = models.PositiveIntegerField(null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    calculated_weight_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sales_price_calc = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sales_price_round = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    item_stock = models.PositiveIntegerField(null=True, blank=True)
    subtract_from = models.DateTimeField(null=True, blank=True)
    total_gifts = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.sku})"

    def discounted_price(self):
        discount_percent = self.discount or 0
        return max(self.price * (decimal.Decimal(1.00) - (decimal.Decimal(discount_percent) / decimal.Decimal(100.00))), 0)

    def purchased_quantity_since_subtract_from(self) -> int:
        if not self.pk:
            return 0
        PurchaseLog = apps.get_model('orders', 'PurchaseLog')
        logs = PurchaseLog.objects.filter(product_id=self.pk)
        if self.subtract_from:
            logs = logs.filter(created_at__gte=self.subtract_from)
        total = logs.aggregate(total=Sum('quantity')).get('total') or 0
        return int(total)

    @property
    def in_stock(self) -> int:
        base_stock = self.item_stock or 0
        if hasattr(self, '_purchased_since_subtract_from'):
            purchased = self._purchased_since_subtract_from or 0
        else:
            purchased = self.purchased_quantity_since_subtract_from()
        return max(0, int(base_stock) - int(purchased))

    @property
    def image_src(self) -> str:
        first_uploaded_image = self.images.filter(image__isnull=False).order_by('sort_order', 'id').first()
        if first_uploaded_image and first_uploaded_image.image:
            return first_uploaded_image.image.url
        if not self.image_url:
            return ''
        if self.image_url.startswith('/'):
            return f"{settings.STATIC_URL.rstrip('/')}{self.image_url}"
        return self.image_url


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('sort_order', 'id')

    def __str__(self) -> str:
        return f"{self.product.name} image #{self.id}"


class CurrencyRate(models.Model):
    code = models.CharField(max_length=3, unique=True)
    symbol = models.CharField(max_length=4, default='$')
    rate = models.DecimalField(max_digits=12, decimal_places=6, help_text='USD to currency rate')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.code} ({self.rate})"
