from rest_framework.test import APITestCase
from rest_framework import status
from users.models import User, Hospital, BloodBank, UserProfile
from inventory.models import Inventory, BloodType, Product, ProductCategory
from transaction.models import BloodRequest

class TransactionViewsTest(APITestCase):
    def setUp(self):
        # Create users
        self.internal_admin = User.objects.create_user(
            username='admin', email='admin@test.com', password='pw', role='INTERNAL_ADMIN'
        )
        self.hospital_admin = User.objects.create_user(
            username='hadmin', email='hadmin@test.com', password='pw', role='HOSPITAL_ADMIN'
        )
        self.bb_admin = User.objects.create_user(
            username='bbadmin', email='bbadmin@test.com', password='pw', role='BLOODBANK_ADMIN'
        )
        
        # Create facilities
        self.hospital = Hospital.objects.create(name='Test Hosp', state='Lagos')
        self.bb = BloodBank.objects.create(name='Test BB', state='Lagos')
        
        # Create profiles
        UserProfile.objects.create(user=self.hospital_admin, hospital=self.hospital)
        UserProfile.objects.create(user=self.bb_admin, blood_bank=self.bb)
        
        # Create inventory
        from inventory.models import ProductCategory
        self.blood_type = BloodType.objects.create(group='O+')
        self.category = ProductCategory.objects.create(name='Blood Components')
        self.product = Product.objects.create(category=self.category, blood_group='O+', volume_ml=500.0)
        self.inventory = Inventory.objects.create(blood_bank=self.bb, product=self.product, blood_type=self.blood_type, quantity=50, price=100)

    def test_blood_request_create(self):
        self.client.force_authenticate(user=self.hospital_admin)
        data = {
            'product': self.product.id,
            'quantity': 5,
            'total_amount': 500,
            'patient_name': 'John Doe',
            'urgency': 'NORMAL'
        }
        response = self.client.post('/transactions/requests/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BloodRequest.objects.count(), 1)
        req = BloodRequest.objects.first()
        self.assertEqual(req.requester_hospital, self.hospital)

    def test_blood_request_update_inventory(self):
        # Create a pending request
        req = BloodRequest.objects.create(
            requester_user=self.hospital_admin,
            requester_hospital=self.hospital,
            product=self.product,
            quantity=5,
            total_amount=500,
            status='PENDING'
        )
        
        self.client.force_authenticate(user=self.bb_admin)
        data = {
            'blood_bank': self.bb.id,
            'status': 'APPROVED'
        }
        # Assuming updating the blood bank and status triggers inventory deduction
        response = self.client.patch(f'/transactions/requests/{req.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 45)  # 50 - 5 = 45

    def test_blood_request_approve_action(self):
        req = BloodRequest.objects.create(
            requester_user=self.hospital_admin,
            requester_hospital=self.hospital,
            blood_bank=self.bb,
            product=self.product,
            quantity=10,
            total_amount=1000,
            status='PENDING'
        )
        
        self.client.force_authenticate(user=self.bb_admin)
        response = self.client.post(f'/transactions/requests/{req.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 40)
        req.refresh_from_db()
        self.assertEqual(req.status, 'APPROVED')

    def test_blood_request_reject_action(self):
        req = BloodRequest.objects.create(
            requester_user=self.hospital_admin,
            requester_hospital=self.hospital,
            blood_bank=self.bb,
            product=self.product,
            quantity=10,
            total_amount=1000,
            status='PENDING'
        )
        
        self.client.force_authenticate(user=self.bb_admin)
        response = self.client.post(f'/transactions/requests/{req.id}/reject/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        req.refresh_from_db()
        self.assertEqual(req.status, 'REJECTED')

    def test_bulk_create_marketplace(self):
        self.client.force_authenticate(user=self.hospital_admin)
        data = {
            'items': [
                {
                    'product': self.product.id,
                    'quantity': 2,
                    'total_amount': 200,
                    'patient_name': 'Patient 1',
                    'urgency': 'URGENT'
                },
                {
                    'product': self.product.id,
                    'quantity': 3,
                    'total_amount': 300,
                    'patient_name': 'Patient 2',
                    'urgency': 'NORMAL'
                }
            ]
        }
        response = self.client.post('/transactions/requests/bulk-create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BloodRequest.objects.count(), 2)

    def test_bulk_pos_sale(self):
        self.client.force_authenticate(user=self.bb_admin)
        data = {
            'payment_method': 'POS',
            'items': [
                {
                    'product': self.product.id,
                    'quantity': 5,
                    'total_amount': 500,
                    'patient_name': 'Walk-in Patient 1',
                    'urgency': 'NORMAL'
                }
            ]
        }
        response = self.client.post('/transactions/requests/bulk-pos-sale/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BloodRequest.objects.count(), 1)
        
        req = BloodRequest.objects.first()
        self.assertEqual(req.status, 'DELIVERED')
        self.assertEqual(req.source, 'POS')
        self.assertEqual(req.blood_bank, self.bb)
        
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 45)

    def test_revenue_stats_view(self):
        # Create some delivered requests
        BloodRequest.objects.create(
            blood_bank=self.bb,
            product=self.product,
            quantity=1,
            total_amount=100,
            commission_amount=10,
            status='DELIVERED',
            source='POS'
        )
        
        self.client.force_authenticate(user=self.bb_admin)
        response = self.client.get('/transactions/revenue/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_revenue'], 100)
        self.assertEqual(response.data['total_profit'], 10)

    def test_live_activity_view(self):
        BloodRequest.objects.create(
            blood_bank=self.bb,
            product=self.product,
            quantity=1,
            total_amount=100,
            status='DELIVERED',
            source='POS'
        )
        
        self.client.force_authenticate(user=self.internal_admin)
        response = self.client.get('/transactions/live-activity/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
