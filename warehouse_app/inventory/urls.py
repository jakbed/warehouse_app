from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.contrib.auth import views as auth_views

from . import views
from .views import AddProductView

app_name = 'inventory'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Szczegóły produktu (AJAX)
    path('product/<int:pk>/detail/', views.product_detail_ajax, name='product_detail_ajax'),

    # Obsługa wypożyczeń i zwrotów
    path('borrow/', views.borrow_items, name='borrow_items'),
    path('return/', views.return_items, name='return_items'),

    # Ekrany logowania i wylogowania
    path('login/', auth_views.LoginView.as_view(template_name='inventory/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Lista kompletów
    path('komplety/', views.KompletListView.as_view(), name='komplety'),
    path('add_product/', AddProductView.as_view(), name='add_product'),

    # Szczegoly produktu
    path('product/<int:pk>/detail_ajax/', views.product_detail_ajax, name='product_detail_ajax'),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)