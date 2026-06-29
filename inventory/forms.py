from django import forms

from .models import Medicine, Supplier, StockBatch, StockMovement


class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = [
            'name',
            'generic_name',
            'category',
            'unit_price',
            'reorder_level',
            'supplier',
        ]

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            'name',
            'phone',
            'email',
            'address',
        ]

class StockBatchForm(forms.ModelForm):
    class Meta:
        model = StockBatch
        fields = [
            'medicine',
            'batch_number',
            'quantity',
            'expiry_date',
        ]

        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }

class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = [
            'medicine',
            'batch',
            'movement_type',
            'quantity',
            'note',
        ]