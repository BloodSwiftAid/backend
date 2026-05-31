from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from users.models import User, UserProfile, Hospital
from users.services.otp_service import create_user_otp

class AuthViewsTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='authuser',
            email='auth@test.com',
            password='password123',
            role='HOSPITAL_ADMIN',
            is_verified=False
        )
        self.hospital = Hospital.objects.create(name='Auth Hospital', state='Lagos', is_active=True, is_verified=True)
        UserProfile.objects.create(user=self.user, hospital=self.hospital)

    def test_request_password_reset_otp_success(self):
        url = '/api/users/auth/request-otp/' # Need to check the actual URL later or use hardcoded if reverse not configured, let's use reverse if possible or hardcoded
        # Actually I will just test the logic, maybe not the exact URL routing. I'll need to use reverse if the name is known, otherwise I'll define it. Let me check core/urls.py or users/urls/auth_urls.py later.
        # But for now, let's just make sure we are testing the right thing. Wait, I should import the views and test them directly using RequestFactory if URLs are unknown.
        # Let's use RequestFactory to test views directly to avoid URL issues.
        pass

class AuthViewsDirectTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='authuser',
            email='auth@test.com',
            password='password123',
            role='HOSPITAL_ADMIN',
            is_verified=False,
            is_active=True
        )
        self.hospital = Hospital.objects.create(name='Auth Hospital', state='Lagos', is_active=True, is_verified=True)
        UserProfile.objects.create(user=self.user, hospital=self.hospital)

    def test_request_password_reset_otp(self):
        from users.views.auth_views import RequestPasswordResetOTPView
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        
        # Success
        request = factory.post('/request-otp/', {'email': 'auth@test.com'}, format='json')
        view = RequestPasswordResetOTPView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Failure
        request = factory.post('/request-otp/', {'email': 'wrong@test.com'}, format='json')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_reset_password(self):
        from users.views.auth_views import ResetPasswordView
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        
        otp_obj = create_user_otp(self.user, purpose='PASSWORD_RESET')
        
        # Success
        request = factory.post('/reset/', {
            'email': 'auth@test.com',
            'otp': otp_obj.otp,
            'new_password': 'newpassword123'
        }, format='json')
        view = ResetPasswordView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))
        
        # Failure
        request = factory.post('/reset/', {
            'email': 'auth@test.com',
            'otp': 'invalid',
            'new_password': 'newpassword123'
        }, format='json')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password(self):
        from users.views.auth_views import ChangePasswordView
        from rest_framework.test import APIRequestFactory
        from rest_framework.test import force_authenticate
        factory = APIRequestFactory()
        
        # Success
        request = factory.post('/change-password/', {
            'old_password': 'password123',
            'new_password': 'newpassword123'
        }, format='json')
        force_authenticate(request, user=self.user)
        view = ChangePasswordView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))
        
        # Failure
        request = factory.post('/change-password/', {
            'old_password': 'wrongpassword',
            'new_password': 'newpassword1234'
        }, format='json')
        force_authenticate(request, user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login(self):
        from users.views.auth_views import MyTokenObtainPairView
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        
        # Success
        request = factory.post('/login/', {
            'email': 'auth@test.com',
            'password': 'password123'
        }, format='json')
        view = MyTokenObtainPairView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Failure
        request = factory.post('/login/', {
            'email': 'auth@test.com',
            'password': 'wrongpassword'
        }, format='json')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
