from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime
import json

from .models import Product, Komplet


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Widok głównej strony (dashboard).
    Wyświetlamy:
     - Produkty "na wyjeździe" (max 5)
     - Wszystkie produkty (z paginacją i sortowaniem)
     - Dane do wykresu (ile w magazynie, ile na wyjeździe)
    """
    template_name = "inventory/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_products'] = Product.objects.count()
        context['total_komplety'] = Komplet.objects.count()

        # 1. Produkty na wyjeździe (max 5 - możesz rozszerzyć mechanizm doładowywania AJAX-em)
        context['on_road_products'] = Product.objects.filter(state='wyjezd').order_by('-created_at')[:5]

        # 2. Lista wszystkich produktów z paginacją i sortowaniem
        sort_by = self.request.GET.get('sort_by', 'created_at')
        product_list = Product.objects.all().order_by(sort_by)
        paginator = Paginator(product_list, 10)
        page = self.request.GET.get('page')
        try:
            products = paginator.page(page)
        except PageNotAnInteger:
            products = paginator.page(1)
        except EmptyPage:
            products = paginator.page(paginator.num_pages)
        context['products'] = products

        # 3. Dane do wykresu - ile produktów w magazynie, ile na wyjeździe
        context['in_warehouse_count'] = Product.objects.filter(state='magazyn').count()
        context['on_road_count'] = Product.objects.filter(state='wyjezd').count()

        # (opcjonalnie) Lista produktów dostępnych do "WYJAZDU" (czyli stan magazyn)
        context['available_products'] = Product.objects.filter(state='magazyn').order_by('brand', 'model')

        return context


@login_required
def product_detail_ajax(request, pk):
    product = get_object_or_404(Product, pk=pk)
    data = {
        'brand': product.brand,
        'model': product.model,
        'code': product.code,
        'custom_name': product.custom_name,
        'serial_number': product.serial_number,
        'description': product.description,
        'photo_url': product.photo_converted.url if product.photo_converted else product.photo_original.url if product.photo_original else ''
    }
    return JsonResponse(data)


@login_required
def borrow_items(request):
    """
    Zmienia stan wybranych produktów na 'wyjezd' i tworzy rekordy w BorrowingRecord.
    Przyjmuje parametry (POST):
      - borrow_start (data)
      - borrow_end (data)
      - items (JSON z listą produktów)
    """
    if request.method == "POST":
        borrow_start = request.POST.get('borrow_start')
        borrow_end = request.POST.get('borrow_end')
        items = request.POST.get('items')  # JSON np. [{"id": 1, "name": "Canon 5D"}...]

        if not (borrow_start and borrow_end and items):
            return HttpResponseForbidden("Niepoprawne dane")

        try:
            borrow_start_date = datetime.strptime(borrow_start, '%Y-%m-%d').date()
            borrow_end_date = datetime.strptime(borrow_end, '%Y-%m-%d').date()
            items_list = json.loads(items)
        except Exception as e:
            return HttpResponseForbidden(f"Błąd parsowania danych: {e}")

        for item_data in items_list:
            product_id = item_data.get('id')
            product = get_object_or_404(Product, pk=product_id)
            # Zmiana stanu na wyjeździe
            product.state = 'wyjezd'
            product.save(update_fields=['state'])
            # Tworzymy wpis w historii
            BorrowingRecord.objects.create(
                product=product,
                user=request.user,
                borrow_start=borrow_start_date,
                borrow_end=borrow_end_date
            )
        return JsonResponse({"status": "ok"})

    return HttpResponseForbidden("Tylko metoda POST dozwolona.")


@login_required
def return_items(request):
    """
    Przyjmuje listę ID produktów do zwrotu, ustawia state='magazyn'
    i uzupełnia return_date w BorrowingRecord.
    """
    if request.method == "POST":
        items = request.POST.getlist('items')
        for prod_id in items:
            product = get_object_or_404(Product, pk=prod_id)
            # Ostatni wypożyczeniowy rekord (bez return_date)
            record = product.history.filter(return_date__isnull=True).order_by('-borrow_date').first()
            if record:
                record.return_date = timezone.now()
                record.save(update_fields=['return_date'])
            product.state = 'magazyn'
            product.save(update_fields=['state'])
        return JsonResponse({"status": "ok"})

    return HttpResponseForbidden("Tylko metoda POST dozwolona.")


class KompletListView(LoginRequiredMixin, ListView):
    """
    Przykładowy widok listy kompletów, jeśli potrzebujesz linku 'Zestawy'.
    """
    model = Komplet
    template_name = 'inventory/komplety_list.html'
    context_object_name = 'komplety'


from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .models import Product


class AddProductView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Product
    template_name = 'inventory/add_product_form.html'  # Plik szablonu, który zaraz stworzymy
    fields = ['brand', 'model', 'custom_name', 'serial_number', 'description', 'photo_original']
    success_url = reverse_lazy('inventory:dashboard')

    def test_func(self):
        # Tylko superuser może wyświetlać ten widok
        return self.request.user.is_superuser


from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Product


def product_detail_ajax(request, pk):
    product = get_object_or_404(Product, pk=pk)
    data = {
        'brand': product.brand,
        'model': product.model,
        'code': product.code,
        'custom_name': product.custom_name,
        'serial_number': product.serial_number,
        'description': product.description,
        'state': product.get_state_display(),
        # Jeśli zdjęcie istnieje, zwracamy URL:
        'photo_url': product.photo_original.url if product.photo_original else '',
    }
    return JsonResponse(data)


from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Order, Product
from .forms import OrderForm  # musisz stworzyć w forms.py


class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    template_name = 'inventory/order_form.html'
    form_class = OrderForm  # musisz zdefiniować form z polami: name, pickup_date, return_date, products
    success_url = reverse_lazy('inventory:dashboard')

    def form_valid(self, form):
        # Ustaw usera na bieżącego
        form.instance.user = self.request.user
        # Ustaw domyślnie reservation_date = today
        form.instance.reservation_date = form.instance.reservation_date or timezone.now().date()
        return super().form_valid(form)


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


@login_required
def early_return(request):
    # Tylko rezerwacje usera
    orders = Order.objects.filter(user=request.user).exclude(status__in=['completed', 'canceled'])
    # user wybiera z listy, w GET/POST

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        order = Order.objects.get(pk=order_id, user=request.user)
        # Ustaw status 'completed'
        order.status = 'completed'
        order.save()  # co spowoduje, że set_products_in_out ustawi produkty na magazyn
        return redirect('inventory:dashboard')

    return render(request, 'inventory/early_return.html', {'orders': orders})
