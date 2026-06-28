from django.shortcuts import render

from .models import Medicine, Supplier, StockBatch, StockMovement

def dashboard(request):
    total_medicines = Medicine.objects.count()
    total_suppliers = Supplier.objects.count()
    total_batches = StockBatch.objects.count()
    recent_movements = StockMovement.objects.order_by('-created_at')[:5]

    context = {
        'total_medicines': total_medicines,
        'total_suppliers': total_suppliers,
        'total_batches': total_batches,
        'recent_movements': recent_movements,
    }

    return render(request, 'inventory/dashboard.html', context)