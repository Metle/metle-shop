from .models import CurrencyRate

def default_currency():
    def create(**kwargs):
        CurrencyRate.objects.get_or_create(**kwargs)

    create(code="SRD", symbol="SR$", rate=36.95)
    create(code="EUR", symbol="€", rate=0.86)