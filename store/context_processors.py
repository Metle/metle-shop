from .models import Brand


def brands_nav(request):
    return {'nav_brands': Brand.objects.order_by('name')}
