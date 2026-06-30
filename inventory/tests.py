from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .forms import StockMovementForm
from .models import Medicine, StockBatch, StockMovement, Supplier
from .views import apply_movement_to_batch, reverse_movement_from_batch


class InventoryFactoryMixin:
    def make_supplier(self, name='Good Health Supplies'):
        return Supplier.objects.create(
            name=name,
            phone='555-0100',
            email='orders@example.com',
            address='123 Pharmacy Lane',
        )

    def make_medicine(self, name='Amoxicillin', supplier=None, reorder_level=10):
        return Medicine.objects.create(
            name=name,
            generic_name='Amoxicillin',
            category='Antibiotic',
            unit_price=Decimal('12.50'),
            reorder_level=reorder_level,
            supplier=supplier or self.make_supplier(),
        )

    def make_batch(self, medicine=None, batch_number='B-100', quantity=50, expiry_date=None):
        return StockBatch.objects.create(
            medicine=medicine or self.make_medicine(),
            batch_number=batch_number,
            quantity=quantity,
            expiry_date=expiry_date or date.today() + timedelta(days=90),
        )

    def make_movement(self, medicine=None, batch=None, movement_type='OUT', quantity=5, **kwargs):
        batch = batch or self.make_batch(medicine=medicine)
        return StockMovement.objects.create(
            medicine=medicine or batch.medicine,
            batch=batch,
            movement_type=movement_type,
            quantity=quantity,
            **kwargs,
        )


class InventoryModelTests(InventoryFactoryMixin, TestCase):
    def test_model_string_representations_are_human_readable(self):
        supplier = self.make_supplier(name='Acme Medical')
        medicine = self.make_medicine(name='Paracetamol', supplier=supplier)
        batch = self.make_batch(medicine=medicine, batch_number='P-001')
        movement = self.make_movement(medicine=medicine, batch=batch, movement_type='IN', quantity=12)

        self.assertEqual(str(supplier), 'Acme Medical')
        self.assertEqual(str(medicine), 'Paracetamol')
        self.assertEqual(str(batch), 'Paracetamol - P-001')
        self.assertEqual(str(movement), 'IN - Paracetamol - 12')


class StockMovementFormTests(InventoryFactoryMixin, TestCase):
    def test_batch_is_required_for_stock_movements(self):
        form = StockMovementForm(
            data={
                'movement_type': 'OUT',
                'quantity': 1,
                'note': 'Sale',
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn('batch', form.errors)

    def test_batch_choices_are_ordered_and_show_available_stock(self):
        zinc = self.make_medicine(name='Zinc')
        aspirin = self.make_medicine(name='Aspirin')
        later_batch = self.make_batch(
            medicine=zinc,
            batch_number='Z-2',
            quantity=8,
            expiry_date=date(2027, 1, 1),
        )
        earlier_batch = self.make_batch(
            medicine=aspirin,
            batch_number='A-1',
            quantity=15,
            expiry_date=date(2026, 8, 1),
        )

        form = StockMovementForm()
        batches = list(form.fields['batch'].queryset)

        self.assertEqual(batches, [earlier_batch, later_batch])
        self.assertEqual(
            form.fields['batch'].label_from_instance(earlier_batch),
            'Aspirin - A-1 (15 available, expires 2026-08-01)',
        )


class StockMovementBatchAdjustmentTests(InventoryFactoryMixin, TestCase):
    def setUp(self):
        self.medicine = self.make_medicine()
        self.batch = self.make_batch(medicine=self.medicine, quantity=50)

    def unsaved_movement(self, movement_type='OUT', quantity=5, batch=None):
        return StockMovement(
            medicine=self.medicine,
            batch=self.batch if batch is None else batch,
            movement_type=movement_type,
            quantity=quantity,
        )

    def test_apply_stock_in_increases_batch_quantity(self):
        movement = self.unsaved_movement(movement_type='IN', quantity=15)

        apply_movement_to_batch(movement)

        self.batch.refresh_from_db()
        self.assertEqual(self.batch.quantity, 65)

    def test_apply_stock_out_decreases_batch_quantity(self):
        movement = self.unsaved_movement(movement_type='OUT', quantity=20)

        apply_movement_to_batch(movement)

        self.batch.refresh_from_db()
        self.assertEqual(self.batch.quantity, 30)

    def test_apply_stock_out_rejects_more_than_available(self):
        movement = self.unsaved_movement(movement_type='OUT', quantity=75)

        with self.assertRaisesMessage(ValidationError, 'Not enough stock in this batch.'):
            apply_movement_to_batch(movement)

        self.batch.refresh_from_db()
        self.assertEqual(self.batch.quantity, 50)

    def test_apply_requires_a_batch(self):
        movement = self.unsaved_movement(batch=None)
        movement.batch = None

        with self.assertRaisesMessage(ValidationError, 'Choose a stock batch for this movement.'):
            apply_movement_to_batch(movement)

    def test_reverse_stock_in_removes_original_quantity(self):
        self.batch.quantity = 80
        self.batch.save()
        movement = self.unsaved_movement(movement_type='IN', quantity=30)

        reverse_movement_from_batch(movement)

        self.batch.refresh_from_db()
        self.assertEqual(self.batch.quantity, 50)

    def test_reverse_stock_out_restores_original_quantity(self):
        movement = self.unsaved_movement(movement_type='OUT', quantity=30)

        reverse_movement_from_batch(movement)

        self.batch.refresh_from_db()
        self.assertEqual(self.batch.quantity, 80)

    def test_reverse_stock_in_rejects_when_received_stock_was_already_used(self):
        movement = self.unsaved_movement(movement_type='IN', quantity=60)

        with self.assertRaisesMessage(
            ValidationError,
            'This movement cannot be changed because some of that stock was already used.',
        ):
            reverse_movement_from_batch(movement)

        self.batch.refresh_from_db()
        self.assertEqual(self.batch.quantity, 50)


class InventoryViewTests(InventoryFactoryMixin, TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='manager', password='safe-pass-123')
        self.client.force_login(self.user)
        self.supplier = self.make_supplier()
        self.medicine = self.make_medicine(supplier=self.supplier)
        self.batch = self.make_batch(medicine=self.medicine, quantity=50)

    def test_dashboard_requires_login(self):
        self.client.logout()

        response = self.client.get(reverse('dashboard'))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_medicine_search_filters_by_name_generic_name_or_category(self):
        other_medicine = self.make_medicine(name='Ibuprofen')
        other_medicine.generic_name = 'Ibuprofen'
        other_medicine.category = 'Pain relief'
        other_medicine.save()

        response = self.client.get(reverse('medicine_list'), {'q': 'antibiotic'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['medicines']), [self.medicine])

    def test_movement_create_decreases_batch_and_records_user(self):
        response = self.client.post(
            reverse('movement_create'),
            {
                'batch': self.batch.pk,
                'movement_type': 'OUT',
                'quantity': 7,
                'note': 'Dispensed to patient',
            },
        )

        self.assertRedirects(response, reverse('movement_list'))
        movement = StockMovement.objects.get()
        self.assertEqual(movement.created_by, self.user)
        self.assertEqual(movement.medicine, self.medicine)
        self.assertEqual(movement.batch, self.batch)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.quantity, 43)

    def test_movement_create_rejects_insufficient_stock_without_saving(self):
        response = self.client.post(
            reverse('movement_create'),
            {
                'batch': self.batch.pk,
                'movement_type': 'OUT',
                'quantity': 51,
                'note': 'Too much',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('Not enough stock in this batch.', response.context['form'].errors['quantity'])
        self.assertEqual(StockMovement.objects.count(), 0)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.quantity, 50)

    def test_movement_update_rolls_back_when_new_quantity_is_invalid(self):
        movement = self.make_movement(
            medicine=self.medicine,
            batch=self.batch,
            movement_type='OUT',
            quantity=20,
            created_by=self.user,
        )
        self.batch.quantity = 30
        self.batch.save()

        response = self.client.post(
            reverse('movement_update', args=[movement.pk]),
            {
                'batch': self.batch.pk,
                'movement_type': 'OUT',
                'quantity': 60,
                'note': 'Invalid correction',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('Not enough stock in this batch.', response.context['form'].errors['quantity'])
        movement.refresh_from_db()
        self.batch.refresh_from_db()
        self.assertEqual(movement.quantity, 20)
        self.assertEqual(self.batch.quantity, 30)

    def test_movement_delete_reverses_stock_out_and_removes_movement(self):
        movement = self.make_movement(
            medicine=self.medicine,
            batch=self.batch,
            movement_type='OUT',
            quantity=10,
            created_by=self.user,
        )
        self.batch.quantity = 40
        self.batch.save()

        response = self.client.post(reverse('movement_delete', args=[movement.pk]))

        self.assertRedirects(response, reverse('movement_list'))
        self.assertFalse(StockMovement.objects.filter(pk=movement.pk).exists())
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.quantity, 50)
