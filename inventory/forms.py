from django import forms

from .models import Medicine, Supplier


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