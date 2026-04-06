from django.shortcuts import redirect, render
from django.urls import reverse
import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST

from .forms import CustomerRegistrationForm
from .models import Customer
from store.models import Product


def register(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        existing = Customer.objects.filter(email=email).first() if email else None
        form = CustomerRegistrationForm(request.POST, instance=existing)
        if form.is_valid():
            customer = form.save()
            request.session['customer_id'] = customer.id
            return redirect(reverse('product_list'))
    else:
        form = CustomerRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


@require_POST
def logout_customer(request):
    request.session.pop('customer_id', None)
    return redirect(reverse('product_list'))


@require_POST
def update_preferences(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        payload = {}
    language = str(payload.get('language', '')).strip()
    currency = str(payload.get('currency', '')).strip()
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return JsonResponse({'updated': False})
    customer = Customer.objects.filter(id=customer_id).first()
    if not customer:
        return JsonResponse({'updated': False})
    if language:
        customer.language = language
    if currency:
        customer.currency = currency
    customer.save(update_fields=['language', 'currency'])
    return JsonResponse({'updated': True})


def session_status(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return JsonResponse({'authenticated': False})
    customer = Customer.objects.filter(id=customer_id).first()
    if not customer:
        return JsonResponse({'authenticated': False})
    return JsonResponse(
        {
            'authenticated': True,
            'full_name': customer.full_name,
        }
    )


@require_http_methods(['POST'])
def add_to_wishlist(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        payload = {}
    product_id = payload.get('product_id')
    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        product_id = None
    if not product_id:
        return JsonResponse({'added': False}, status=400)
    if not Product.objects.filter(id=product_id).exists():
        return JsonResponse({'added': False}, status=404)
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return JsonResponse({'added': False, 'error': 'not_authenticated'}, status=401)
    customer = Customer.objects.filter(id=customer_id).first()
    if not customer:
        return JsonResponse({'added': False, 'error': 'not_authenticated'}, status=401)
    wishlist = []
    for item in customer.wishlist or []:
        try:
            wishlist.append(int(item))
        except (TypeError, ValueError):
            continue
    if product_id in wishlist:
        wishlist = [item for item in wishlist if item != product_id]
        customer.wishlist = wishlist
        customer.save(update_fields=['wishlist'])
        return JsonResponse({'removed': True})
    wishlist.append(product_id)
    customer.wishlist = wishlist
    customer.save(update_fields=['wishlist'])
    return JsonResponse({'added': True})
