from django import forms


class CheckoutForm(forms.Form):
    DELIVERY_CHOICES = [
        ('pick-up', 'Pick-up'),
        ('delivery', 'Delivery'),
    ]

    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('bank transfer', 'Bank transfer'),
    ]

    full_name = forms.CharField(max_length=200)
    email = forms.EmailField()
    delivery_option = forms.ChoiceField(choices=DELIVERY_CHOICES)
    delivery_address = forms.CharField(required=False, widget=forms.Textarea)
    payment_option = forms.ChoiceField(choices=PAYMENT_CHOICES)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('delivery_option') == 'delivery' and not (cleaned_data.get('delivery_address') or '').strip():
            self.add_error('delivery_address', 'An address is required for delivery.')
        return cleaned_data
