import logging
from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _order_total(order):
    subtotal = Decimal('0.00')
    for item in order.items.all():
        line_total = item.line_total()
        product_discount = item.product.discount if item.product else Decimal('0.00')
        subtotal += line_total * (Decimal('1.00') - (product_discount / Decimal('100.00')))
    order_discount = order.discount or Decimal('0.00')
    total = subtotal * (Decimal('1.00') - (order_discount / Decimal('100.00')))
    return max(total, Decimal('0.00')).quantize(Decimal('0.01'))


def send_order_notification(order):
    """Notify the shop owner that a new order was placed.

    Failures are logged but never interrupt the checkout flow.
    """
    recipient = getattr(settings, 'ORDER_NOTIFICATION_EMAIL', '')
    if not recipient:
        return

    items = order.items.select_related('product')
    lines = [
        f"- {item.product.name} x {item.quantity} @ {item.unit_price}"
        for item in items
    ]
    delivery = order.delivery_option or '-'
    if order.delivery_option == 'delivery' and order.delivery_address:
        delivery = f"delivery to {order.delivery_address}"

    body = "\n".join([
        f"New order {order.order_number}",
        f"Customer: {order.full_name} <{order.email}>",
        f"Fulfilment: {delivery}",
        "",
        "Items:",
        *lines,
        "",
        f"Total: {_order_total(order)}",
    ])

    try:
        send_mail(
            subject=f"New order {order.order_number}",
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Failed to send order notification for order %s", order.pk)
