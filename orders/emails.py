import logging
from decimal import Decimal

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import Context, Template
from django.utils.html import strip_tags

from .email_defaults import DEFAULT_TEMPLATES

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


def _render(key, context_dict):
    from .models import EmailTemplate

    defaults = DEFAULT_TEMPLATES.get(key, {'subject': '', 'body': ''})
    template = EmailTemplate.objects.filter(key=key).first()
    subject_src = template.subject if template else defaults['subject']
    body_src = template.body if template else defaults['body']
    subject = Template(subject_src).render(Context(context_dict)).strip()
    html_body = Template(body_src).render(Context(context_dict))
    return subject, html_body


def _send(key, context_dict, recipient):
    if not recipient:
        return
    try:
        subject, html_body = _render(key, context_dict)
        message = EmailMultiAlternatives(
            subject=subject,
            body=strip_tags(html_body),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        message.attach_alternative(html_body, 'text/html')
        message.send()
    except Exception:
        logger.exception("Failed to send '%s' email to %s", key, recipient)


def _order_context(order):
    return {
        'order': order,
        'items': list(order.items.select_related('product')),
        'total': _order_total(order),
    }


def send_order_notification(order):
    """Notify the shop owner that a new order was placed."""
    recipient = getattr(settings, 'ORDER_NOTIFICATION_EMAIL', '')
    _send('new_order', _order_context(order), recipient)


def send_status_update(order):
    """Email the customer when the order reaches a fulfilment status."""
    if order.status not in ('ready for pickup', 'delivery scheduled'):
        return
    _send(order.status, _order_context(order), order.email)
