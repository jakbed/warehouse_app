from django import forms
from .models import Order, Product


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['name', 'pickup_date', 'return_date', 'products']
        # 'products' jest ManyToManyField, więc w formie będzie MultiSelect lub widget oparty na checkboxach

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Możesz np. filtrować tylko produkty w magazynie:
        self.fields['products'].queryset = Product.objects.filter(state='magazyn')
