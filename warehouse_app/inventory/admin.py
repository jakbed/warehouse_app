from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Product, Komplet

from django.conf.locale.es import formats as es_formats

es_formats.DATETIME_FORMAT = "d M Y H:i:s"
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'code', 'state', 'ean')
    search_fields = ('brand', 'model', 'code', 'custom_name', 'serial_number', 'ean')
    list_filter = ('state', 'brand')
    readonly_fields = ('code', 'created_at',)

@admin.register(Komplet)
class KompletAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('products',)


