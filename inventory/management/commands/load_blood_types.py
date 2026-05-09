from django.core.management.base import BaseCommand
from inventory.models import BloodType

class Command(BaseCommand):
    help = 'Load default blood types into the system'

    def handle(self, *args, **options):
        blood_groups = [
            ('A+', 5000.00),
            ('A-', 6000.00),
            ('B+', 5000.00),
            ('B-', 6000.00),
            ('AB+', 7000.00),
            ('AB-', 8500.00),
            ('O+', 5500.00),
            ('O-', 7500.00),
        ]

        for group, price in blood_groups:
            bt, created = BloodType.objects.get_or_create(
                group=group,
                defaults={'base_price': price, 'is_active': True}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created blood type {group}'))
            else:
                bt.base_price = price
                bt.save()
                self.stdout.write(f'Updated base price for blood type {group}')
