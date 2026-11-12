"""Default email template contents.

Used as the fallback when no EmailTemplate row exists, and to seed the
editable rows via a data migration.
"""

DEFAULT_TEMPLATES = {
    'new_order': {
        'subject': 'New order {{ order.order_number }}',
        'body': (
            '<p>New order <strong>{{ order.order_number }}</strong></p>\n'
            '<p>Customer: {{ order.full_name }} ({{ order.email }})</p>\n'
            '<p>Fulfilment: {{ order.delivery_option }}'
            '{% if order.delivery_address %} &mdash; {{ order.delivery_address }}{% endif %}</p>\n'
            '<h3>Items</h3>\n'
            '<ul>{% for item in items %}'
            '<li>{{ item.product.name }} &times; {{ item.quantity }} @ {{ item.unit_price }}</li>'
            '{% endfor %}</ul>\n'
            '<p><strong>Total: {{ total }}</strong></p>'
        ),
    },
    'ready for pickup': {
        'subject': 'Your order {{ order.order_number }} is ready for pickup',
        'body': (
            '<p>Hi {{ order.full_name }},</p>\n'
            '<p>Your order <strong>{{ order.order_number }}</strong> is ready for pickup.</p>\n'
            '{% if order.window_start and order.window_end %}'
            '<p>Pickup window: {{ order.window_start }} &ndash; {{ order.window_end }}</p>\n'
            '{% endif %}'
            '<p>Thank you for shopping with Utsukushi.</p>'
        ),
    },
    'delivery scheduled': {
        'subject': 'Your order {{ order.order_number }} has been scheduled for delivery',
        'body': (
            '<p>Hi {{ order.full_name }},</p>\n'
            '<p>Your order <strong>{{ order.order_number }}</strong> has been scheduled for delivery.</p>\n'
            '{% if order.delivery_address %}'
            '<p>Delivery address: {{ order.delivery_address }}</p>\n'
            '{% endif %}'
            '{% if order.window_start and order.window_end %}'
            '<p>Delivery window: {{ order.window_start }} &ndash; {{ order.window_end }}</p>\n'
            '{% endif %}'
            '<p>Thank you for shopping with Utsukushi.</p>'
        ),
    },
}
