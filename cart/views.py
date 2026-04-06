from decimal import Decimal, ROUND_HALF_UP

from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.models import Customer
from orders.models import Order
from store.models import CurrencyRate, Product

from .models import Cart, CartItem


def _get_or_create_cart(request):
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    customer_id = request.session.get('customer_id')
    customer = Customer.objects.filter(id=customer_id).first() if customer_id else None
    cart, _ = Cart.objects.get_or_create(session_key=session_key, defaults={'customer': customer})
    if customer and cart.customer_id is None:
        cart.customer = customer
        cart.save(update_fields=['customer'])
    return cart


@require_POST
def add_to_cart(request, product_id):
    cart = _get_or_create_cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if created:
        item.quantity = max(1, quantity)
    else:
        item.quantity += max(1, quantity)
    if product.in_stock > 0:
        item.quantity = min(item.quantity, product.in_stock)
    item.save()
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect(reverse('cart_detail'))


def cart_detail(request):
    cart = _get_or_create_cart(request)
    items = cart.items.select_related('product')
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

    total = Decimal('0.00')
    for item in items:
        unit_price = (item.product.price * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        unit_discounted = (item.product.discounted_price() * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        line_price = (item.line_total() * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        line_discounted = (item.line_total_discounted() * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        item.display_unit_price = unit_price
        item.display_unit_discounted = unit_discounted
        item.display_line_total = line_price
        item.display_line_discounted = line_discounted
        if item.product.discount:
            total += line_discounted
        else:
            total += line_price
    cart_total = total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    customer = None
    orders = []
    customer_id = request.session.get('customer_id')
    if customer_id:
        customer = Customer.objects.filter(id=customer_id).first()
    if customer:
        orders = list(Order.objects.filter(customer=customer).order_by('-created_at')[:5])
        for order in orders:
            order_items = order.items.select_related('product')
            subtotal = Decimal('0.00')
            for order_item in order_items:
                product_discount = order_item.product.discount if order_item.product else Decimal('0.00')
                line_total = order_item.line_total() * (Decimal('1.00') - (product_discount / Decimal('100.00')))
                line_total = (line_total * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                subtotal += line_total
            order_discount = order.discount or Decimal('0.00')
            total = subtotal * (Decimal('1.00') - (order_discount / Decimal('100.00')))
            order.display_total = total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return render(
        request,
        'cart/cart_detail.html',
        {
            'cart': cart,
            'items': items,
            'total': cart_total,
            'currency_symbol': symbol,
            'orders': orders,
        },
    )


@require_POST
def remove_cart_item(request, item_id):
    cart = _get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect(reverse('cart_detail'))


def cart_count(request):
    session_key = request.session.session_key
    if not session_key:
        return JsonResponse({'count': 0})
    cart = Cart.objects.filter(session_key=session_key).first()
    if not cart:
        return JsonResponse({'count': 0})
    count = cart.items.count()
    return JsonResponse({'count': count})
