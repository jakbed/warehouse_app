from django.contrib import admin
from .models import Product, Komplet, Category
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.conf.locale.es import formats as es_formats

es_formats.DATETIME_FORMAT = "d M Y H:i:s"


class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        # Opcjonalnie: określ pola, które chcesz importować/eksportować
        fields = ('id', 'brand', 'model', 'custom_name', 'serial_number', 'description', 'state', 'category__name')


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('brand', 'model', 'code', 'state', 'ean', 'category')
    search_fields = ('brand', 'model', 'code', 'custom_name', 'serial_number', 'ean')
    list_filter = ('state', 'brand')
    readonly_fields = ('code', 'created_at',)


@admin.register(Komplet)
class KompletAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('products',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_count')
    def product_count(self, obj):
        return obj.products.count()

    product_count.short_description = "Liczba produktów"
