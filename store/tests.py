import errno
from unittest.mock import Mock, patch

from django.contrib.admin.sites import AdminSite
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.files.uploadedfile import SimpleUploadedFile
from django.templatetags.static import static
from django.test import RequestFactory, TestCase

from .admin import ProductAdmin, _read_only_media_error_message
from .models import Brand, Category, Product, ProductImage
from .views import _product_image_sources


class ProductImageSourceTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Skincare', slug='skincare')
        self.brand = Brand.objects.create(name='Utsukushi')

    def create_product(self, **overrides):
        data = {
            'name': 'Badge Serum',
            'sku': 'badge-serum',
            'category': self.category,
            'brand': self.brand,
            'price': '12.00',
            'image_url': '/img/placeholder-product.svg',
        }
        data.update(overrides)
        return Product.objects.create(**data)

    def test_product_image_sources_uses_related_image_urls(self):
        product = self.create_product()
        ProductImage.objects.create(product=product, image_url='https://cdn.example.com/badge.png', sort_order=0)
        ProductImage.objects.create(product=product, image_url='/img/products/badge-detail.png', sort_order=1)

        self.assertEqual(
            _product_image_sources(product),
            [
                'https://cdn.example.com/badge.png',
                static('img/products/badge-detail.png'),
            ],
        )

    def test_product_image_src_prefers_related_image_source(self):
        product = self.create_product(image_url='/img/products/fallback.png')
        ProductImage.objects.create(product=product, image_url='https://cdn.example.com/badge.png', sort_order=0)

        self.assertEqual(product.image_src, 'https://cdn.example.com/badge.png')


class ProductAdminTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin = ProductAdmin(Product, AdminSite())
        self.category = Category.objects.create(name='Skincare', slug='skincare')
        self.brand = Brand.objects.create(name='Utsukushi')
        self.product = Product.objects.create(
            name='Badge Serum',
            sku='badge-serum',
            category=self.category,
            brand=self.brand,
            price='12.00',
        )

    def _build_request(self):
        request = self.factory.post('/admin/store/product/1/change/')
        SessionMiddleware(lambda response: response).process_request(request)
        request.session.save()
        setattr(request, '_messages', FallbackStorage(request))
        return request

    def test_save_related_shows_message_when_media_storage_is_read_only(self):
        request = self._build_request()
        upload = SimpleUploadedFile('badge.png', b'filecontent', content_type='image/png')
        request.FILES.setlist('additional_images', [upload])
        form = Mock(instance=self.product, save_m2m=Mock())

        with patch(
            'store.admin.ProductImage.objects.create',
            side_effect=OSError(errno.EROFS, 'Read-only file system'),
        ):
            self.admin.save_related(request, form, [], change=True)

        self.assertEqual([message.message for message in get_messages(request)], [_read_only_media_error_message()])
