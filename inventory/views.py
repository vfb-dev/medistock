from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import MedicineForm, StockBatchForm, StockMovementForm, SupplierForm
from .models import Medicine, StockBatch, StockMovement, Supplier


def apply_movement_to_batch(movement):
    if not movement.batch:
        raise ValidationError('Choose a stock batch for this movement.')

    if movement.movement_type == 'IN':
        movement.batch.quantity += movement.quantity
    elif movement.movement_type == 'OUT':
        if movement.batch.quantity < movement.quantity:
            raise ValidationError('Not enough stock in this batch.')
        movement.batch.quantity -= movement.quantity

    movement.batch.save()


def reverse_movement_from_batch(movement):
    if not movement.batch:
        return

    if movement.movement_type == 'IN':
        if movement.batch.quantity < movement.quantity:
            raise ValidationError(
                'This movement cannot be changed because some of that stock was already used.'
            )
        movement.batch.quantity -= movement.quantity
    elif movement.movement_type == 'OUT':
        movement.batch.quantity += movement.quantity

    movement.batch.save()


@login_required
def dashboard(request):
    today = timezone.now().date()
    soon = today + timedelta(days=30)

    total_medicines = Medicine.objects.count()
    total_suppliers = Supplier.objects.count()
    total_batches = StockBatch.objects.count()
    recent_movements = StockMovement.objects.select_related(
        'medicine',
        'batch',
    ).order_by('-created_at')[:5]

    low_stock_batches = StockBatch.objects.filter(quantity__lte=F('medicine__reorder_level'))
    expiring_soon_batches = StockBatch.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=soon,
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


@login_required
def medicine_list(request):
    query = request.GET.get('q', '')
    medicines = Medicine.objects.select_related('supplier').order_by('name')

    if query:
        medicines = medicines.filter(
            Q(name__icontains=query)
            | Q(generic_name__icontains=query)
            | Q(category__icontains=query)
        )

    return render(request, 'inventory/medicine_list.html', {'medicines': medicines, 'query': query})


@login_required
def medicine_create(request):
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('medicine_list')
    else:
        form = MedicineForm()

    return render(request, 'inventory/medicine_form.html', {'form': form})


@login_required
def medicine_update(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)

    if request.method == 'POST':
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            return redirect('medicine_list')
    else:
        form = MedicineForm(instance=medicine)

    return render(request, 'inventory/medicine_form.html', {'form': form, 'medicine': medicine})


@login_required
def medicine_delete(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)

    if request.method == 'POST':
        medicine.delete()
        return redirect('medicine_list')

    return render(request, 'inventory/medicine_confirm_delete.html', {'medicine': medicine})


@login_required
def supplier_list(request):
    suppliers = Supplier.objects.order_by('name')
    return render(request, 'inventory/supplier_list.html', {'suppliers': suppliers})


@login_required
def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('supplier_list')
    else:
        form = SupplierForm()

    return render(request, 'inventory/supplier_form.html', {'form': form})


@login_required
def supplier_update(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)

    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            return redirect('supplier_list')
    else:
        form = SupplierForm(instance=supplier)

    return render(request, 'inventory/supplier_form.html', {'form': form, 'supplier': supplier})


@login_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)

    if request.method == 'POST':
        supplier.delete()
        return redirect('supplier_list')

    return render(request, 'inventory/supplier_confirm_delete.html', {'supplier': supplier})


@login_required
def batch_list(request):
    batches = StockBatch.objects.select_related('medicine').order_by('expiry_date')
    return render(request, 'inventory/batch_list.html', {'batches': batches})


@login_required
def batch_create(request):
    if request.method == 'POST':
        form = StockBatchForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('batch_list')
    else:
        form = StockBatchForm()

    return render(request, 'inventory/batch_form.html', {'form': form})


@login_required
def batch_update(request, pk):
    batch = get_object_or_404(StockBatch, pk=pk)

    if request.method == 'POST':
        form = StockBatchForm(request.POST, instance=batch)
        if form.is_valid():
            form.save()
            return redirect('batch_list')
    else:
        form = StockBatchForm(instance=batch)

    return render(request, 'inventory/batch_form.html', {'form': form, 'batch': batch})


@login_required
def batch_delete(request, pk):
    batch = get_object_or_404(StockBatch, pk=pk)

    if request.method == 'POST':
        batch.delete()
        return redirect('batch_list')

    return render(request, 'inventory/batch_confirm_delete.html', {'batch': batch})


@login_required
def movement_list(request):
    movements = StockMovement.objects.select_related(
        'medicine',
        'batch',
        'created_by',
    ).order_by('-created_at')
    return render(request, 'inventory/movement_list.html', {'movements': movements})


@login_required
def movement_create(request):
    if request.method == 'POST':
        form = StockMovementForm(request.POST)
        if form.is_valid():
            movement = form.save(commit=False)
            movement.created_by = request.user
            movement.medicine = movement.batch.medicine

            try:
                with transaction.atomic():
                    apply_movement_to_batch(movement)
                    movement.save()
                return redirect('movement_list')
            except ValidationError as error:
                form.add_error('quantity', error.message)
    else:
        form = StockMovementForm()

    return render(request, 'inventory/movement_form.html', {'form': form})


@login_required
def movement_update(request, pk):
    movement = get_object_or_404(StockMovement.objects.select_related('batch'), pk=pk)

    if request.method == 'POST':
        old_movement = StockMovement.objects.select_related('batch').get(pk=pk)
        form = StockMovementForm(request.POST, instance=movement)

        if form.is_valid():
            updated_movement = form.save(commit=False)
            updated_movement.medicine = updated_movement.batch.medicine

            try:
                with transaction.atomic():
                    reverse_movement_from_batch(old_movement)
                    apply_movement_to_batch(updated_movement)
                    updated_movement.save()
                return redirect('movement_list')
            except ValidationError as error:
                form.add_error('quantity', error.message)
    else:
        form = StockMovementForm(instance=movement)

    return render(request, 'inventory/movement_form.html', {'form': form, 'movement': movement})


@login_required
def movement_delete(request, pk):
    movement = get_object_or_404(StockMovement.objects.select_related('batch', 'medicine'), pk=pk)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                reverse_movement_from_batch(movement)
                movement.delete()
            return redirect('movement_list')
        except ValidationError as error:
            return render(
                request,
                'inventory/movement_confirm_delete.html',
                {'movement': movement, 'error': error.message},
            )

    return render(request, 'inventory/movement_confirm_delete.html', {'movement': movement})
