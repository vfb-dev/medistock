from django import forms

from .models import Medicine


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