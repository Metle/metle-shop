import json
from decimal import Decimal, ROUND_HALF_UP

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.templatetags.static import static
from django.views.decorators.http import require_POST

from accounts.models import Customer
from cart.models import Cart
from orders.models import OrderItem
from .models import Category, CurrencyRate, Product


def _product_image_sources(product):
    related_sources = []
    for image in product.images.all():
        if image.image:
            related_sources.append(image.image.url)
    if related_sources:
        return related_sources

    image_url = (product.image_url or '').strip()
    if not image_url:
        return [static('img/placeholder-product.svg')]

    candidates = [image_url]
    for separator in ('\n', '|', ';', ','):
        if separator in image_url:
            candidates = [chunk.strip() for chunk in image_url.split(separator)]
            break

    sources = []
    seen = set()
    for candidate in candidates:
        if not candidate:
            continue
        if candidate.startswith(('http://', 'https://')):
            src = candidate
        else:
            src = static(candidate.lstrip('/'))
        if src in seen:
            continue
        seen.add(src)
        sources.append(src)

    return sources or [static('img/placeholder-product.svg')]


def _get_currency(request):
    code = request.session.get('currency', 'USD')
    rate = Decimal('1.0')
    symbol = '$'
    if code != 'USD':
        record = CurrencyRate.objects.filter(code=code).first()
        if record:
            rate = record.rate
            symbol = record.symbol or symbol
        else:
            code = 'USD'
    return code, symbol, rate


def _apply_currency(products, rate, symbol):
    for product in products:
        base = (product.price * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        discounted = (product.discounted_price() * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        product.display_price = base
        product.display_discounted_price = discounted
        product.display_symbol = symbol
    return products


def product_list(request):
    categories = Category.objects.order_by('name')
    category_slug = request.GET.get('category')
    brand_id = request.GET.get('brand')
    sale_only = request.GET.get('sale')
    products = Product.objects.select_related('category').all().order_by('name')
    if category_slug:
        products = products.filter(category__slug=category_slug)
    if brand_id:
        products = products.filter(brand_id=brand_id)
    if sale_only:
        products = products.filter(discount__gt=0)
    code, symbol, rate = _get_currency(request)
    products = _apply_currency(products, rate, symbol)
    paginator = Paginator(products, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    customer_id = request.session.get('customer_id')
    session_key = request.session.session_key
    cart_has_items = False
    if session_key:
        cart = Cart.objects.filter(session_key=session_key).first()
        cart_has_items = bool(cart and cart.items.exists())
    previous_products = Product.objects.none()
    wishlist_ids = []
    if customer_id:
        customer = Customer.objects.filter(id=customer_id).first()
        if customer and customer.wishlist:
            cleaned_ids = []
            seen = set()
            for item in customer.wishlist:
                try:
                    value = int(item)
                except (TypeError, ValueError):
                    continue
                if value in seen:
                    continue
                seen.add(value)
                cleaned_ids.append(value)
            wishlist_ids = cleaned_ids
        previous_products = (
            Product.objects.filter(orderitem__order__customer_id=customer_id)
            .select_related('category')
            .distinct()
            .order_by('name')
        )
        previous_products = _apply_currency(previous_products, rate, symbol)

    return render(
        request,
        'store/product_list.html',
        {
            'products': page_obj,
            'page_obj': page_obj,
            'categories': categories,
            'active_category': category_slug,
            'active_brand': brand_id,
            'active_sale': sale_only,
            'currency_code': code,
            'previous_products': previous_products,
            'wishlist_ids': wishlist_ids,
            'cart_has_items': cart_has_items,
        },
    )


def product_detail(request, product_id):
    product = get_object_or_404(Product.objects.prefetch_related('images'), id=product_id)
    product_images = _product_image_sources(product)
    wishlist_ids = []
    customer_id = request.session.get('customer_id')
    if customer_id:
        customer = Customer.objects.filter(id=customer_id).first()
        if customer and customer.wishlist:
            for item in customer.wishlist:
                try:
                    wishlist_ids.append(int(item))
                except (TypeError, ValueError):
                    continue
    code, symbol, rate = _get_currency(request)
    product.display_price = (product.price * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    product.display_discounted_price = (product.discounted_price() * rate).quantize(
        Decimal('0.01'),
        rounding=ROUND_HALF_UP,
    )
    product.display_symbol = symbol
    return render(
        request,
        'store/product_detail.html',
        {
            'product': product,
            'product_images': product_images,
            'is_wishlisted': product.id in wishlist_ids,
        },
    )


def wishlist(request):
    customer_id = request.session.get('customer_id')
    wishlist_ids = []
    wishlist_products = Product.objects.none()
    if customer_id:
        customer = Customer.objects.filter(id=customer_id).first()
        if customer and customer.wishlist:
            cleaned_ids = []
            seen = set()
            for item in customer.wishlist:
                try:
                    value = int(item)
                except (TypeError, ValueError):
                    continue
                if value in seen:
                    continue
                seen.add(value)
                cleaned_ids.append(value)
            wishlist_ids = cleaned_ids
    code, symbol, rate = _get_currency(request)
    if wishlist_ids:
        wishlist_products = (
            Product.objects.filter(id__in=wishlist_ids)
            .select_related('category')
            .order_by('name')
        )
        wishlist_products = _apply_currency(wishlist_products, rate, symbol)
    return render(
        request,
        'store/wishlist.html',
        {
            'wishlist_products': wishlist_products,
            'wishlist_ids': wishlist_ids,
            'currency_code': code,
        },
    )


@require_POST
def set_currency(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        payload = {}
    code = str(payload.get('currency', 'USD')).upper()
    if code != 'USD' and not CurrencyRate.objects.filter(code=code).exists():
        code = 'USD'
    request.session['currency'] = code
    return JsonResponse({'currency': code})
