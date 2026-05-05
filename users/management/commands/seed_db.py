import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import Organization, UserProfile
from inventory.models import ProductCategory, Product, Inventory
from transaction.models import BloodRequest
from payment.models import Payment
from django.utils import timezone
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed the database with sample data for SwiftAid'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database...')

        # 1. Create Superuser (SwiftAid Admin)
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@swiftaid.com',
                password='password123',
                role='INTERNAL_ADMIN',
                is_verified=True
            )
            self.stdout.write(self.style.SUCCESS('Created SwiftAid Admin'))
        else:
            admin = User.objects.get(username='admin')

        # 2. Create Product Categories & Products
        categories = ['Whole Blood', 'Plasma', 'Platelets']
        blood_groups = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']
        
        for cat_name in categories:
            category, _ = ProductCategory.objects.get_or_create(name=cat_name)
            for bg in blood_groups:
                Product.objects.get_or_create(
                    category=category,
                    blood_group=bg,
                    volume_ml=Decimal('450.00'),
                    defaults={'price': Decimal('5000.00')}
                )
        self.stdout.write(self.style.SUCCESS('Seeded Categories & Products'))

        # 3. Create Organizations (Blood Banks & Hospitals)
        locations = [
            {'state': 'Lagos', 'lga': 'Ikeja', 'name': 'Lagos Central Blood Bank'},
            {'state': 'Lagos', 'lga': 'Lagos Island', 'name': 'Island Hope Hospital'},
            {'state': 'Abuja', 'lga': 'Garki', 'name': 'Abuja National Blood Center'},
            {'state': 'Abuja', 'lga': 'Wuse', 'name': 'Wuse District Hospital'},
        ]

        for loc in locations:
            org_type = 'BLOODBANK' if 'Blood' in loc['name'] else 'HOSPITAL'
            org, _ = Organization.objects.get_or_create(
                name=loc['name'],
                defaults={
                    'org_type': org_type,
                    'state': loc['state'],
                    'lga': loc['lga'],
                    'address': f"Sample address in {loc['lga']}",
                    'contact_email': f"contact@{loc['name'].lower().replace(' ', '')}.com",
                    'is_verified': True
                }
            )

            # Create Admin for each Org
            username = f"{loc['lga'].lower()}_admin"
            role = f"{org_type}_ADMIN"
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f"{username}@example.com",
                    password='password123',
                    role=role,
                    is_verified=True
                )
                UserProfile.objects.create(user=user, organization=org)
            
            # Re-fetch user if it already existed
            user = User.objects.get(username=username)
                
            # Add Staff for Blood Banks
            if org_type == 'BLOODBANK':
                for i in range(1, 3):
                    staff_username = f"{username}_staff_{i}"
                    if not User.objects.filter(username=staff_username).exists():
                        # Check current staff count for this org
                        staff_count = UserProfile.objects.filter(
                            organization=org, 
                            user__role__in=['BLOODBANK_STAFF', 'HOSPITAL_STAFF']
                        ).count()
                        
                        if staff_count < 2:
                            staff_user = User.objects.create_user(
                                username=staff_username,
                                email=f"{staff_username}@example.com",
                                password='password123',
                                role='BLOODBANK_STAFF'
                            )
                            UserProfile.objects.create(user=staff_user, organization=org)


        self.stdout.write(self.style.SUCCESS('Seeded Organizations, Admins, and Staff'))

        # 4. Seed Inventory for Blood Banks
        blood_banks = Organization.objects.filter(org_type='BLOODBANK')
        products = Product.objects.all()
        for bb in blood_banks:
            for product in random.sample(list(products), 5):
                Inventory.objects.get_or_create(
                    organization=bb,
                    product=product,
                    defaults={
                        'quantity': random.randint(10, 50),
                        'expiry_date': timezone.now().date() + timezone.timedelta(days=35)
                    }
                )
        self.stdout.write(self.style.SUCCESS('Seeded Inventory'))

        self.stdout.write(self.style.SUCCESS('Database seeding completed successfully!'))
