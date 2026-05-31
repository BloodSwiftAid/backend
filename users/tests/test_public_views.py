from rest_framework.test import APITestCase
from rest_framework import status
from users.models import Hospital, BloodBank, User, PotentialDonor
from users.views.public_views import RegisterFacilityView, RegisterDonorView
from rest_framework.test import APIRequestFactory

class PublicViewsTest(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_register_hospital(self):
        request = self.factory.post('/register/facility/', {
            'facility_type': 'hospital',
            'facility_name': 'New Pub Hospital',
            'hospital_type': 'General',
            'has_emergency_unit': True,
            'admin_name': 'Pub Admin',
            'admin_email': 'pub@test.com',
            'admin_phone': '1234567890',
            'operational_address': '123 Main St',
            'country': 'Nigeria',
            'state': 'Lagos',
            'lga': 'Ikeja',
            'city': 'Lagos'
        }, format='json')
        view = RegisterFacilityView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='pub@test.com').exists())
        self.assertTrue(Hospital.objects.filter(name='New Pub Hospital').exists())

    def test_register_bloodbank(self):
        request = self.factory.post('/register/facility/', {
            'facility_type': 'bloodbank',
            'facility_name': 'New Pub Bloodbank',
            'license_number': 'LIC456',
            'admin_name': 'BB Admin',
            'admin_email': 'bbpub@test.com',
            'admin_phone': '0987654321',
            'operational_address': '456 Side St',
            'country': 'Nigeria',
            'state': 'Lagos',
            'lga': 'Surulere',
            'city': 'Lagos'
        }, format='json')
        view = RegisterFacilityView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='bbpub@test.com').exists())
        self.assertTrue(BloodBank.objects.filter(name='New Pub Bloodbank').exists())

    def test_register_donor(self):
        request = self.factory.post('/register/donor/', {
            'full_name': 'Good Donor',
            'email': 'donor@test.com',
            'phone': '1112223334',
            'blood_group': 'A+',
            'address': '789 Donor Ave',
            'country': 'Nigeria',
            'state': 'Lagos',
            'city': 'Lagos',
            'lga': 'Ikeja'
        }, format='json')
        view = RegisterDonorView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PotentialDonor.objects.filter(email='donor@test.com').exists())
