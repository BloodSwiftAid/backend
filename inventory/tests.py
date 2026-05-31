from rest_framework.test import APITestCase
from rest_framework import status
from users.models import User, BloodBank, UserProfile, GlobalConfig
from inventory.models import BloodType, ProductCategory, Product, Inventory, Donation

class InventoryViewsTest(APITestCase):
    def setUp(self):
        self.internal_admin = User.objects.create_user(
            username='admin', email='admin@test.com', password='pw', role='INTERNAL_ADMIN'
        )
        self.bb_admin = User.objects.create_user(
            username='bbadmin', email='bbadmin@test.com', password='pw', role='BLOODBANK_ADMIN'
        )
        self.bb = BloodBank.objects.create(name='Test BB', state='Lagos', city='Ikeja', is_active=True)
        UserProfile.objects.create(user=self.bb_admin, blood_bank=self.bb)
        
        self.blood_type = BloodType.objects.create(group='A+', base_price=100.0, is_active=True)
        self.category = ProductCategory.objects.create(name='Whole Blood')
        self.product = Product.objects.create(category=self.category, blood_group='A+', volume_ml=500.0)

    def test_blood_type_viewset(self):
        self.client.force_authenticate(user=self.internal_admin)
        response = self.client.get('/api/v1/inventory/blood-types/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

    def test_product_category_viewset(self):
        self.client.force_authenticate(user=self.internal_admin)
        response = self.client.get('/api/v1/inventory/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_product_viewset(self):
        self.client.force_authenticate(user=self.internal_admin)
        response = self.client.get('/api/v1/inventory/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_inventory_viewset(self):
        Inventory.objects.create(blood_bank=self.bb, blood_type=self.blood_type, quantity=10, price=100.0)
        
        self.client.force_authenticate(user=self.bb_admin)
        response = self.client.get('/api/v1/inventory/inventory/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

        # Test internal admin views all
        self.client.force_authenticate(user=self.internal_admin)
        response = self.client.get('/api/v1/inventory/inventory/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

        # Create
        self.client.force_authenticate(user=self.bb_admin)
        data = {
            'blood_type': self.blood_type.id,
            'quantity': 5,
            'price': 100.0
        }
        response = self.client.post('/api/v1/inventory/inventory/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_inventory_bulk_create(self):
        self.client.force_authenticate(user=self.bb_admin)
        data = {
            'items': [
                {'blood_group': 'A+', 'quantity': 10}
            ]
        }
        response = self.client.post('/api/v1/inventory/inventory/bulk-create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Inventory.objects.count(), 1)
        self.assertEqual(Inventory.objects.first().quantity, 10)
        
        # Test add to existing
        response = self.client.post('/api/v1/inventory/inventory/bulk-create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Inventory.objects.first().quantity, 20)

    def test_donation_viewset(self):
        self.client.force_authenticate(user=self.bb_admin)
        data = {
            'donor_name': 'Donor 1',
            'blood_group': 'A+',
            'volume_ml': 500.0
        }
        response = self.client.post('/api/v1/inventory/donations/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check if inventory was auto updated
        self.assertEqual(Inventory.objects.count(), 1)
        self.assertEqual(Inventory.objects.first().quantity, 1)

        response = self.client.get('/api/v1/inventory/donations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

    def test_inventory_stats(self):
        Inventory.objects.create(blood_bank=self.bb, blood_type=self.blood_type, quantity=10, price=100.0)
        self.client.force_authenticate(user=self.bb_admin)
        response = self.client.get('/api/v1/inventory/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['A+'], 10)

    def test_marketplace(self):
        GlobalConfig.objects.create(commission_percentage=10.0)
        Inventory.objects.create(blood_bank=self.bb, blood_type=self.blood_type, quantity=10, price=100.0)
        
        self.client.force_authenticate(user=self.internal_admin)
        response = self.client.get('/api/v1/inventory/marketplace/?city=Ikeja')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['available_units'], 10)
        self.assertEqual(response.data[0]['total_price'], 110.0)

    def test_marketplace_locations(self):
        self.client.force_authenticate(user=self.internal_admin)
        response = self.client.get('/api/v1/inventory/marketplace/locations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('cities', response.data)
        self.assertIn('Ikeja', response.data['cities'])

    def test_blood_type_breakdown(self):
        Inventory.objects.create(blood_bank=self.bb, blood_type=self.blood_type, quantity=10, price=100.0)
        self.client.force_authenticate(user=self.internal_admin)
        response = self.client.get('/api/v1/inventory/blood-type-breakdown/?blood_group=A%2B')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)
        self.assertEqual(response.data[0]['quantity'], 10)
