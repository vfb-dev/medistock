from django import forms

from .models import Medicine, StockBatch, StockMovement, Supplier


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
            'batch',
            'movement_type',
            'quantity',
            'note',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['batch'].required = True
        self.fields['batch'].queryset = StockBatch.objects.select_related('medicine').order_by(
            'medicine__name',
            'expiry_date',
            'batch_number',
        )
        self.fields['batch'].label_from_instance = (
            lambda batch: f'{batch.medicine.name} - {batch.batch_number} '
            f'({batch.quantity} available, expires {batch.expiry_date})'
        )
