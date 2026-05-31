from rest_framework.test import APITestCase
from rest_framework import status
from users.models import User, Hospital, BloodBank, UserProfile
from users.views.user_views import UserViewSet, StaffManagementViewSet, HospitalViewSet, BloodBankViewSet
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate

class UserViewsTest(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.internal_admin = User.objects.create_user(
            username='internal', email='internal@test.com', password='pw', role='INTERNAL_ADMIN'
        )
        self.hospital_admin = User.objects.create_user(
            username='hadmin', email='hadmin@test.com', password='pw', role='HOSPITAL_ADMIN'
        )
        self.hospital = Hospital.objects.create(name='View Hospital', state='Lagos')
        UserProfile.objects.create(user=self.hospital_admin, hospital=self.hospital)

    def test_user_viewset_create_facility_admin(self):
        request = self.factory.post('/users/', {
            'username': 'newhadmin',
            'email': 'newhadmin@test.com',
            'password': 'pw',
            'role': 'HOSPITAL_ADMIN',
            'first_name': 'New',
            'last_name': 'Admin'
        }, format='json')
        force_authenticate(request, user=self.internal_admin)
        view = UserViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'newhadmin@test.com')

    def test_staff_management_viewset_create_staff(self):
        request = self.factory.post('/staff/', {
            'username': 'newstaff',
            'email': 'newstaff@test.com',
            'password': 'pw',
            'first_name': 'New',
            'last_name': 'Staff'
        }, format='json')
        force_authenticate(request, user=self.hospital_admin)
        view = StaffManagementViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify staff was created and linked to hospital
        new_staff = User.objects.get(email='newstaff@test.com')
        self.assertEqual(new_staff.role, 'HOSPITAL_STAFF')
        self.assertEqual(new_staff.profile.hospital, self.hospital)

    def test_toggle_active_user(self):
        target_user = User.objects.create_user(username='target', email='target@test.com', password='pw', is_active=True)
        request = self.factory.post(f'/users/{target_user.id}/toggle-active/')
        force_authenticate(request, user=self.internal_admin)
        view = UserViewSet.as_view({'post': 'toggle_active'})
        response = view(request, pk=target_user.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        target_user.refresh_from_db()
        self.assertFalse(target_user.is_active)

    def test_toggle_verified_hospital(self):
        target_hospital = Hospital.objects.create(name='Target Hospital', state='Lagos', is_verified=False)
        request = self.factory.post(f'/hospitals/{target_hospital.id}/toggle-verified/')
        force_authenticate(request, user=self.internal_admin)
        view = HospitalViewSet.as_view({'post': 'toggle_verified'})
        response = view(request, pk=target_hospital.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        target_hospital.refresh_from_db()
        self.assertTrue(target_hospital.is_verified)

    def test_toggle_active_bloodbank(self):
        target_bb = BloodBank.objects.create(name='Target BB', state='Lagos', is_active=True)
        request = self.factory.post(f'/bloodbanks/{target_bb.id}/toggle-active/')
        force_authenticate(request, user=self.internal_admin)
        view = BloodBankViewSet.as_view({'post': 'toggle_active'})
        response = view(request, pk=target_bb.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        target_bb.refresh_from_db()
        self.assertFalse(target_bb.is_active)

    def test_me_view(self):
        from users.views.user_views import MeView
        request = self.factory.get('/me/')
        force_authenticate(request, user=self.internal_admin)
        view = MeView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        request = self.factory.patch('/me/', {'first_name': 'Updated'}, format='json')
        force_authenticate(request, user=self.internal_admin)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_global_config_view(self):
        from users.views.user_views import GlobalConfigView
        request = self.factory.get('/config/')
        force_authenticate(request, user=self.internal_admin)
        view = GlobalConfigView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        request = self.factory.post('/config/', {'commission_percentage': 15.0}, format='json')
        force_authenticate(request, user=self.internal_admin)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_staff_management_extras(self):
        bb_admin = User.objects.create_user(username='bbadmin', email='bba@test.com', password='pw', role='BLOODBANK_ADMIN')
        bb = BloodBank.objects.create(name='My BB', state='Lagos')
        UserProfile.objects.create(user=bb_admin, blood_bank=bb)
        
        # Test create staff for blood bank
        request = self.factory.post('/staff/', {
            'username': 'bbstaff',
            'email': 'bbstaff@test.com',
            'password': 'pw'
        }, format='json')
        force_authenticate(request, user=bb_admin)
        view = StaffManagementViewSet.as_view({'post': 'create', 'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test get queryset
        request = self.factory.get('/staff/')
        force_authenticate(request, user=bb_admin)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        staff_user = User.objects.get(email='bbstaff@test.com')
        # Test reset password
        request = self.factory.post(f'/staff/{staff_user.id}/reset-password/', {'password': 'newpw'}, format='json')
        force_authenticate(request, user=bb_admin)
        reset_view = StaffManagementViewSet.as_view({'post': 'reset_password'})
        response = reset_view(request, pk=staff_user.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_system_stats_view(self):
        from users.views.stats_views import SystemStatsView
        request = self.factory.get('/stats/')
        force_authenticate(request, user=self.internal_admin)
        view = SystemStatsView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_users', response.data)
        self.assertIn('blood_banks', response.data)
