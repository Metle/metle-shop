from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from accounts.models import Customer
from cart.models import Cart, CartItem
from store.models import CurrencyRate, Product

from .forms import CheckoutForm
from .models import Order, OrderItem

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


def checkout(request):
    cart = _get_or_create_cart(request)
    items = cart.items.select_related('product')
    if not items.exists():
        return redirect(reverse('cart_detail'))

    customer = None
    if request.session.get('customer_id'):
        customer = Customer.objects.filter(id=request.session.get('customer_id')).first()

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                customer, _ = Customer.objects.get_or_create(
                    email=form.cleaned_data['email'],
                    defaults={'full_name': form.cleaned_data['full_name']},
                )
                if customer.full_name != form.cleaned_data['full_name']:
                    customer.full_name = form.cleaned_data['full_name']
                    customer.save(update_fields=['full_name'])

                order = Order.objects.create(
                    customer=customer,
                    email=customer.email,
                    full_name=customer.full_name,
                    status='pending',
                )

                for item in items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        unit_price=item.product.price,
                    )

                cart.items.all().delete()

            request.session['customer_id'] = customer.id
            return redirect(reverse('order_success', kwargs={'order_id': order.id}))
    else:
        initial = {}
        if customer:
            initial = {'full_name': customer.full_name, 'email': customer.email}
        form = CheckoutForm(initial=initial)

    return render(request, 'orders/checkout.html', {'form': form, 'items': items})


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/order_success.html', {'order': order})


def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    customer_id = request.session.get('customer_id')
    if order.customer_id and order.customer_id != customer_id:
        return redirect(reverse('product_list'))
    if request.method == 'POST':
        delivery_option = request.POST.get('delivery_option', '').strip()
        delivery_address = request.POST.get('delivery_address', '').strip()
        payment_option = request.POST.get('payment_option', '').strip()
        order.delivery_option = delivery_option
        order.delivery_address = delivery_address if delivery_option == 'delivery' else ''
        order.payment_option = payment_option
        order.save(update_fields=['delivery_option', 'delivery_address', 'payment_option'])
        return redirect(reverse('order_detail', kwargs={'order_id': order.id}))
    items = order.items.select_related('product')
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

    subtotal = Decimal('0.00')
    for item in items:
        product_discount = item.product.discount if item.product else Decimal('0.00')
        line_total = item.line_total() * (Decimal('1.00') - (product_discount / Decimal('100.00')))
        line_total = (line_total * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        subtotal += line_total
    order_discount = order.discount or Decimal('0.00')
    total = subtotal * (Decimal('1.00') - (order_discount / Decimal('100.00')))
    total = total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return render(
        request,
        'orders/order_detail.html',
        {'order': order, 'items': items, 'total': total, 'currency_symbol': symbol},
    )
