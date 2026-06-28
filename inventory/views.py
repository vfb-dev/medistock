from datetime import timedelta

from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import F, Q

from .models import Medicine, Supplier, StockBatch, StockMovement
from .forms import MedicineForm, SupplierForm, StockBatchForm

def dashboard(request):
    today = timezone.now().date()
    soon = today + timedelta(days=30)

    total_medicines = Medicine.objects.count()
    total_suppliers = Supplier.objects.count()
    total_batches = StockBatch.objects.count()
    recent_movements = StockMovement.objects.order_by('-created_at')[:5]

    low_stock_batches = StockBatch.objects.filter(quantity__lte=F('medicine__reorder_level'))

    expiring_soon_batches = StockBatch.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=soon
    ).order_by('expiry_date')

    context = {
        'total_medicines': total_medicines,
        'total_suppliers': total_suppliers,
        'total_batches': total_batches,
        'recent_movements': recent_movements,
        'low_stock_batches': low_stock_batches,
        'expiring_soon_batches': expiring_soon_batches,
    }

    return render(request, 'inventory/dashboard.html', context)

def medicine_list(request):
    query = request.GET.get('q', '')

    medicines = Medicine.objects.select_related('supplier').order_by('name')

    if query:
        medicines = medicines.filter(
            Q(name__icontains=query) |
            Q(generic_name__icontains=query) |
            Q(category__icontains=query)
        )

    context = {
        'medicines': medicines,
        'query': query,
    }

    return render(request, 'inventory/medicine_list.html', context)

def medicine_create(request):
    if request.method == 'POST':
        form = MedicineForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('medicine_list')
    else:
        form = MedicineForm()

    context = {
        'form': form,
    }

    return render(request, 'inventory/medicine_form.html', context)

def medicine_update(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)

    if request.method == 'POST':
        form = MedicineForm(request.POST, instance=medicine)

        if form.is_valid():
            form.save()
            return redirect('medicine_list')
    else:
        form = MedicineForm(instance=medicine)

    context = {
        'form': form,
        'medicine': medicine,
    }

    return render(request, 'inventory/medicine_form.html', context)

def medicine_delete(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)

    if request.method == 'POST':
        medicine.delete()
        return redirect('medicine_list')

    context = {
        'medicine': medicine,
    }

    return render(request, 'inventory/medicine_confirm_delete.html', context)

def supplier_list(request):
    suppliers = Supplier.objects.order_by('name')

    context = {
        'suppliers': suppliers,
    }

    return render(request, 'inventory/supplier_list.html', context)

def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('supplier_list')
    else:
        form = SupplierForm()

    context = {
        'form': form,
    }

    return render(request, 'inventory/supplier_form.html', context)

def supplier_update(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)

    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)

        if form.is_valid():
            form.save()
            return redirect('supplier_list')
    else:
        form = SupplierForm(instance=supplier)

    context = {
        'form': form,
        'supplier': supplier,
    }

    return render(request, 'inventory/supplier_form.html', context)

def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)

    if request.method == 'POST':
        supplier.delete()
        return redirect('supplier_list')

    context = {
        'supplier': supplier,
    }

    return render(request, 'inventory/supplier_confirm_delete.html', context)

def batch_list(request):
    batches = StockBatch.objects.select_related('medicine').order_by('expiry_date')

    context = {
        'batches': batches,
    }

    return render(request, 'inventory/batch_list.html', context)

def batch_create(request):
    if request.method == 'POST':
        form = StockBatchForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('batch_list')
    else:
        form = StockBatchForm()

    context = {
        'form': form,
    }

    return render(request, 'inventory/batch_form.html', context)

def batch_update(request, pk):
    batch = get_object_or_404(StockBatch, pk=pk)

    if request.method == 'POST':
        form = StockBatchForm(request.POST, instance=batch)

        if form.is_valid():
            form.save()
            return redirect('batch_list')
    else:
        form = StockBatchForm(instance=batch)

    context = {
        'form': form,
        'batch': batch,
    }

    return render(request, 'inventory/batch_form.html', context)

def batch_delete(request, pk):
    batch = get_object_or_404(StockBatch, pk=pk)

    if request.method == 'POST':
        batch.delete()
        return redirect('batch_list')

    context = {
        'batch': batch,
    }

    return render(request, 'inventory/batch_confirm_delete.html', context)