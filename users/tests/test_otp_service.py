from django.test import TestCase
from users.models import User, UserOTP
from users.services.otp_service import generate_otp, create_user_otp, verify_otp

class OTPServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='otptest', email='otp@test.com', password='pw')

    def test_generate_otp(self):
        otp = generate_otp(length=8)
        self.assertEqual(len(otp), 8)
        self.assertTrue(otp.isdigit())

    def test_create_user_otp(self):
        otp_obj = create_user_otp(self.user, purpose='VERIFICATION')
        self.assertEqual(len(otp_obj.otp), 6)
        self.assertEqual(otp_obj.purpose, 'VERIFICATION')
        self.assertFalse(otp_obj.is_used)

        # Create another one, the first should be deactivated
        otp_obj2 = create_user_otp(self.user, purpose='VERIFICATION')
        
        otp_obj.refresh_from_db()
        self.assertTrue(otp_obj.is_used)
        self.assertFalse(otp_obj2.is_used)

    def test_verify_otp(self):
        otp_obj = create_user_otp(self.user, purpose='PASSWORD_RESET')
        
        # Verify with wrong purpose
        self.assertFalse(verify_otp(self.user, otp_obj.otp, purpose='VERIFICATION'))
        
        # Verify with wrong OTP
        self.assertFalse(verify_otp(self.user, '000000', purpose='PASSWORD_RESET'))
        
        # Verify successful
        self.assertTrue(verify_otp(self.user, otp_obj.otp, purpose='PASSWORD_RESET'))
        
        # Verify again should fail (used)
        self.assertFalse(verify_otp(self.user, otp_obj.otp, purpose='PASSWORD_RESET'))
