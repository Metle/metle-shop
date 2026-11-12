from django.db import migrations

from orders.email_defaults import DEFAULT_TEMPLATES


def seed_templates(apps, schema_editor):
    EmailTemplate = apps.get_model('orders', 'EmailTemplate')
    for key, data in DEFAULT_TEMPLATES.items():
        EmailTemplate.objects.get_or_create(
            key=key,
            defaults={'subject': data['subject'], 'body': data['body']},
        )


def remove_templates(apps, schema_editor):
    EmailTemplate = apps.get_model('orders', 'EmailTemplate')
    EmailTemplate.objects.filter(key__in=list(DEFAULT_TEMPLATES)).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0006_emailtemplate'),
    ]

    operations = [
        migrations.RunPython(seed_templates, remove_templates),
    ]
