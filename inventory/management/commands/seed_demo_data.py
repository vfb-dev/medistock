from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from inventory.models import Medicine, StockBatch, StockMovement, Supplier


DEMO_MOVEMENT_PREFIX = 'DEMO:'


SUPPLIERS = [
    {
        'name': 'HealthFirst Distributors',
        'phone': '+1 555-0101',
        'email': 'orders@healthfirst.example',
        'address': '1200 Careway Drive, Springfield',
    },
    {
        'name': 'NovaMed Supply Co.',
        'phone': '+1 555-0134',
        'email': 'sales@novamed.example',
        'address': '44 Harbor Street, Lakeside',
    },
    {
        'name': 'Apex Pharma Wholesale',
        'phone': '+1 555-0178',
        'email': 'support@apexpharma.example',
        'address': '89 Market Avenue, Brookfield',
    },
    {
        'name': 'CareBridge Logistics',
        'phone': '+1 555-0199',
        'email': 'dispatch@carebridge.example',
        'address': '7 North Depot Road, Riverton',
    },
]


MEDICINES = [
    {
        'name': 'Paracetamol 500mg Tablets',
        'generic_name': 'Acetaminophen',
        'category': 'Pain Relief',
        'unit_price': '4.50',
        'reorder_level': 40,
        'supplier': 'HealthFirst Distributors',
        'batches': [
            {'number': 'DEMO-PARA-A', 'quantity': 18, 'opening_quantity': 96, 'expiry_days': 18, 'received_days_ago': 72},
            {'number': 'DEMO-PARA-B', 'quantity': 240, 'opening_quantity': 240, 'expiry_days': 220, 'received_days_ago': 12},
        ],
    },
    {
        'name': 'Amoxicillin 500mg Capsules',
        'generic_name': 'Amoxicillin',
        'category': 'Antibiotics',
        'unit_price': '11.75',
        'reorder_level': 25,
        'supplier': 'NovaMed Supply Co.',
        'batches': [
            {'number': 'DEMO-AMOX-A', 'quantity': 11, 'opening_quantity': 64, 'expiry_days': 12, 'received_days_ago': 56},
            {'number': 'DEMO-AMOX-B', 'quantity': 140, 'opening_quantity': 140, 'expiry_days': 170, 'received_days_ago': 8},
        ],
    },
    {
        'name': 'Ibuprofen 200mg Tablets',
        'generic_name': 'Ibuprofen',
        'category': 'Pain Relief',
        'unit_price': '5.25',
        'reorder_level': 35,
        'supplier': 'HealthFirst Distributors',
        'batches': [
            {'number': 'DEMO-IBU-A', 'quantity': 30, 'opening_quantity': 110, 'expiry_days': 44, 'received_days_ago': 85},
            {'number': 'DEMO-IBU-B', 'quantity': 190, 'opening_quantity': 190, 'expiry_days': 260, 'received_days_ago': 17},
        ],
    },
    {
        'name': 'Metformin 500mg Tablets',
        'generic_name': 'Metformin Hydrochloride',
        'category': 'Diabetes',
        'unit_price': '8.90',
        'reorder_level': 50,
        'supplier': 'Apex Pharma Wholesale',
        'batches': [
            {'number': 'DEMO-METF-A', 'quantity': 42, 'opening_quantity': 150, 'expiry_days': 26, 'received_days_ago': 66},
            {'number': 'DEMO-METF-B', 'quantity': 310, 'opening_quantity': 310, 'expiry_days': 320, 'received_days_ago': 19},
        ],
    },
    {
        'name': 'Lisinopril 10mg Tablets',
        'generic_name': 'Lisinopril',
        'category': 'Cardiovascular',
        'unit_price': '7.40',
        'reorder_level': 30,
        'supplier': 'CareBridge Logistics',
        'batches': [
            {'number': 'DEMO-LISI-A', 'quantity': 14, 'opening_quantity': 90, 'expiry_days': 9, 'received_days_ago': 94},
            {'number': 'DEMO-LISI-B', 'quantity': 170, 'opening_quantity': 170, 'expiry_days': 280, 'received_days_ago': 21},
        ],
    },
    {
        'name': 'Atorvastatin 20mg Tablets',
        'generic_name': 'Atorvastatin Calcium',
        'category': 'Cardiovascular',
        'unit_price': '13.30',
        'reorder_level': 30,
        'supplier': 'CareBridge Logistics',
        'batches': [
            {'number': 'DEMO-ATOR-A', 'quantity': 28, 'opening_quantity': 100, 'expiry_days': 33, 'received_days_ago': 60},
            {'number': 'DEMO-ATOR-B', 'quantity': 210, 'opening_quantity': 210, 'expiry_days': 350, 'received_days_ago': 15},
        ],
    },
    {
        'name': 'Omeprazole 20mg Capsules',
        'generic_name': 'Omeprazole',
        'category': 'Gastrointestinal',
        'unit_price': '9.10',
        'reorder_level': 45,
        'supplier': 'NovaMed Supply Co.',
        'batches': [
            {'number': 'DEMO-OME-A', 'quantity': 21, 'opening_quantity': 115, 'expiry_days': 21, 'received_days_ago': 70},
            {'number': 'DEMO-OME-B', 'quantity': 260, 'opening_quantity': 260, 'expiry_days': 300, 'received_days_ago': 11},
        ],
    },
    {
        'name': 'Salbutamol 100mcg Inhaler',
        'generic_name': 'Albuterol',
        'category': 'Respiratory',
        'unit_price': '18.80',
        'reorder_level': 20,
        'supplier': 'Apex Pharma Wholesale',
        'batches': [
            {'number': 'DEMO-SALB-A', 'quantity': 7, 'opening_quantity': 48, 'expiry_days': 16, 'received_days_ago': 75},
            {'number': 'DEMO-SALB-B', 'quantity': 65, 'opening_quantity': 65, 'expiry_days': 210, 'received_days_ago': 9},
        ],
    },
    {
        'name': 'Cetirizine 10mg Tablets',
        'generic_name': 'Cetirizine Hydrochloride',
        'category': 'Allergy',
        'unit_price': '6.35',
        'reorder_level': 25,
        'supplier': 'HealthFirst Distributors',
        'batches': [
            {'number': 'DEMO-CET-A', 'quantity': 23, 'opening_quantity': 85, 'expiry_days': 58, 'received_days_ago': 49},
            {'number': 'DEMO-CET-B', 'quantity': 150, 'opening_quantity': 150, 'expiry_days': 250, 'received_days_ago': 13},
        ],
    },
    {
        'name': 'Insulin Glargine Pen',
        'generic_name': 'Insulin Glargine',
        'category': 'Diabetes',
        'unit_price': '29.50',
        'reorder_level': 12,
        'supplier': 'Apex Pharma Wholesale',
        'batches': [
            {'number': 'DEMO-INSU-A', 'quantity': 5, 'opening_quantity': 36, 'expiry_days': 24, 'received_days_ago': 35},
            {'number': 'DEMO-INSU-B', 'quantity': 42, 'opening_quantity': 42, 'expiry_days': 130, 'received_days_ago': 6},
        ],
    },
    {
        'name': 'Oral Rehydration Salts Sachets',
        'generic_name': 'Oral Rehydration Salts',
        'category': 'Rehydration',
        'unit_price': '2.20',
        'reorder_level': 60,
        'supplier': 'CareBridge Logistics',
        'batches': [
            {'number': 'DEMO-ORS-A', 'quantity': 38, 'opening_quantity': 160, 'expiry_days': 27, 'received_days_ago': 80},
            {'number': 'DEMO-ORS-B', 'quantity': 360, 'opening_quantity': 360, 'expiry_days': 420, 'received_days_ago': 18},
        ],
    },
    {
        'name': 'Chlorhexidine 0.2% Mouthwash',
        'generic_name': 'Chlorhexidine Gluconate',
        'category': 'Antiseptic',
        'unit_price': '10.60',
        'reorder_level': 18,
        'supplier': 'NovaMed Supply Co.',
        'batches': [
            {'number': 'DEMO-CHX-A', 'quantity': 16, 'opening_quantity': 54, 'expiry_days': 63, 'received_days_ago': 45},
            {'number': 'DEMO-CHX-B', 'quantity': 80, 'opening_quantity': 80, 'expiry_days': 280, 'received_days_ago': 14},
        ],
    },
]


class Command(BaseCommand):
    help = 'Create realistic demo suppliers, medicines, batches, movements, and a demo user.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            default='demo',
            help='Username for the demo login. Defaults to "demo".',
        )
        parser.add_argument(
            '--password',
            default='demo12345',
            help='Password for the demo login. Defaults to "demo12345".',
        )
        parser.add_argument(
            '--skip-user',
            action='store_true',
            help='Only create inventory data, not a login user.',
        )
        parser.add_argument(
            '--reset-demo',
            action='store_true',
            help='Delete the existing demo inventory dataset before seeding it again.',
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            if options['reset_demo']:
                self._delete_demo_inventory()

            user = None
            if not options['skip_user']:
                user = self._upsert_demo_user(options['username'], options['password'])

            supplier_lookup = self._upsert_suppliers()
            medicine_lookup = self._upsert_medicines(supplier_lookup)
            batch_lookup = self._upsert_batches(medicine_lookup)
            movement_count = self._replace_demo_movements(batch_lookup, user)

        self.stdout.write(self.style.SUCCESS('Demo data is ready.'))
        self.stdout.write(
            f'Created/updated {len(supplier_lookup)} suppliers, '
            f'{len(medicine_lookup)} medicines, {len(batch_lookup)} batches, '
            f'and {movement_count} stock movements.'
        )

        if not options['skip_user']:
            self.stdout.write(
                f'Demo login: {options["username"]} / {options["password"]}'
            )

    def _upsert_demo_user(self, username, password):
        User = get_user_model()
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                'email': 'demo@medistock.example',
                'first_name': 'Demo',
                'last_name': 'User',
            },
        )

        user.email = user.email or 'demo@medistock.example'
        user.first_name = user.first_name or 'Demo'
        user.last_name = user.last_name or 'User'
        user.is_active = True
        user.set_password(password)
        user.save()
        return user

    def _delete_demo_inventory(self):
        medicine_names = [medicine['name'] for medicine in MEDICINES]
        supplier_names = [supplier['name'] for supplier in SUPPLIERS]

        StockMovement.objects.filter(note__startswith=DEMO_MOVEMENT_PREFIX).delete()
        StockBatch.objects.filter(batch_number__startswith='DEMO-').delete()
        Medicine.objects.filter(name__in=medicine_names).delete()
        Supplier.objects.filter(name__in=supplier_names).delete()

    def _upsert_suppliers(self):
        suppliers = {}

        for supplier_data in SUPPLIERS:
            supplier, _ = Supplier.objects.update_or_create(
                name=supplier_data['name'],
                defaults={
                    'phone': supplier_data['phone'],
                    'email': supplier_data['email'],
                    'address': supplier_data['address'],
                },
            )
            suppliers[supplier.name] = supplier

        return suppliers

    def _upsert_medicines(self, supplier_lookup):
        medicines = {}

        for medicine_data in MEDICINES:
            medicine, _ = Medicine.objects.update_or_create(
                name=medicine_data['name'],
                defaults={
                    'generic_name': medicine_data['generic_name'],
                    'category': medicine_data['category'],
                    'unit_price': Decimal(medicine_data['unit_price']),
                    'reorder_level': medicine_data['reorder_level'],
                    'supplier': supplier_lookup[medicine_data['supplier']],
                },
            )
            medicines[medicine.name] = medicine

        return medicines

    def _upsert_batches(self, medicine_lookup):
        today = timezone.localdate()
        batches = {}

        for medicine_data in MEDICINES:
            medicine = medicine_lookup[medicine_data['name']]

            for batch_data in medicine_data['batches']:
                received_date = today - timedelta(days=batch_data['received_days_ago'])
                batch, _ = StockBatch.objects.update_or_create(
                    medicine=medicine,
                    batch_number=batch_data['number'],
                    defaults={
                        'quantity': batch_data['quantity'],
                        'expiry_date': today + timedelta(days=batch_data['expiry_days']),
                    },
                )
                StockBatch.objects.filter(pk=batch.pk).update(received_date=received_date)
                batch.received_date = received_date
                batches[batch.batch_number] = batch

        return batches

    def _replace_demo_movements(self, batch_lookup, user):
        StockMovement.objects.filter(note__startswith=DEMO_MOVEMENT_PREFIX).delete()

        now = timezone.now()
        movement_count = 0

        for medicine_data in MEDICINES:
            for batch_data in medicine_data['batches']:
                batch = batch_lookup[batch_data['number']]
                movement_count += self._create_movement(
                    batch=batch,
                    movement_type='IN',
                    quantity=batch_data['opening_quantity'],
                    note=f'{DEMO_MOVEMENT_PREFIX} Opening stock for {batch.batch_number}.',
                    created_by=user,
                    created_at=now - timedelta(days=batch_data['received_days_ago']),
                )

                dispensed_quantity = batch_data['opening_quantity'] - batch_data['quantity']
                if dispensed_quantity > 0:
                    movement_count += self._create_movement(
                        batch=batch,
                        movement_type='OUT',
                        quantity=dispensed_quantity,
                        note=f'{DEMO_MOVEMENT_PREFIX} Dispensed stock from {batch.batch_number}.',
                        created_by=user,
                        created_at=now - timedelta(days=max(batch_data['received_days_ago'] // 4, 1)),
                    )

        return movement_count

    def _create_movement(self, batch, movement_type, quantity, note, created_by, created_at):
        movement = StockMovement.objects.create(
            medicine=batch.medicine,
            batch=batch,
            movement_type=movement_type,
            quantity=quantity,
            note=note,
            created_by=created_by,
        )
        StockMovement.objects.filter(pk=movement.pk).update(created_at=created_at)
        return 1
