from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Product, Komplet, BorrowingRecord

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'code', 'state', 'created_at')
    search_fields = ('brand', 'model', 'code', 'custom_name', 'serial_number')
    list_filter = ('state', 'brand')
    readonly_fields = ('code', 'created_at',)

@admin.register(Komplet)
class KompletAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('products',)

@admin.register(BorrowingRecord)
class BorrowingRecordAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'borrow_start', 'borrow_end', 'borrow_date', 'return_date')
    search_fields = ('product__brand', 'product__model', 'user__username')
    list_filter = ('borrow_start', 'borrow_end', 'user')
