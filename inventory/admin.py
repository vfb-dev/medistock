from django.contrib import admin
from .models import Supplier, Medicine, StockBatch, StockMovement


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email')
    search_fields = ('name', 'phone', 'email')

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'unit_price', 'reorder_level', 'supplier')
    search_fields = ('name', 'generic_name', 'category')
    list_filter = ('category', 'supplier')

@admin.register(StockBatch)
class StockBatchAdmin(admin.ModelAdmin):
    list_display = ('medicine', 'batch_number', 'quantity', 'expiry_date', 'received_date')
    search_fields = ('medicine__name', 'batch_number')
    list_filter = ('expiry_date',)

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('medicine', 'movement_type', 'quantity', 'created_by', 'created_at')
    list_filter = ('movement_type', 'created_at')