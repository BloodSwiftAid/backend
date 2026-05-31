from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from users.models import User, Hospital, BloodBank, UserProfile, GlobalConfig, VerificationLog, PotentialDonor, UserOTP

class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='password123',
            role='HOSPITAL_ADMIN'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.role, 'HOSPITAL_ADMIN')
        self.assertFalse(user.is_verified)
        self.assertFalse(user.must_change_password)
        self.assertEqual(str(user), 'testuser')

class UserOTPModelTest(TestCase):
    def test_create_user_otp(self):
        user = User.objects.create_user(username='testotp', email='otp@example.com', password='password123')
        otp = UserOTP.objects.create(
            user=user,
            otp='123456',
            purpose='VERIFICATION',
            expiry=timezone.now() + timedelta(minutes=10)
        )
        self.assertEqual(otp.otp, '123456')
        self.assertEqual(str(otp), f"testotp - 123456 (VERIFICATION)")

class OrganizationModelTest(TestCase):
    def test_create_hospital(self):
        hospital = Hospital.objects.create(
            name='Test Hospital',
            contact_email='hospital@example.com',
            state='Lagos',
            city='Ikeja'
        )
        self.assertEqual(hospital.name, 'Test Hospital')
        self.assertEqual(str(hospital), 'Test Hospital')
        self.assertTrue(hospital.has_emergency_unit)

    def test_create_blood_bank(self):
        blood_bank = BloodBank.objects.create(
            name='Test Blood Bank',
            license_number='LIC123',
            storage_capacity_liters=50.0
        )
        self.assertEqual(blood_bank.name, 'Test Blood Bank')
        self.assertEqual(blood_bank.commission_percentage, 10.0)

class UserProfileModelTest(TestCase):
    def setUp(self):
        self.hospital = Hospital.objects.create(name='Max Staff Hospital', state='Lagos')
        self.blood_bank = BloodBank.objects.create(name='Max Staff Blood Bank', state='Lagos')

    def test_hospital_staff_limit(self):
        # Create 10 staff members
        for i in range(10):
            user = User.objects.create_user(username=f'staff{i}', email=f'staff{i}@example.com', password='pw', role='HOSPITAL_STAFF')
            profile = UserProfile.objects.create(user=user, hospital=self.hospital)
        
        # 11th should fail validation
        user11 = User.objects.create_user(username='staff11', email='staff11@example.com', password='pw', role='HOSPITAL_STAFF')
        profile11 = UserProfile(user=user11, hospital=self.hospital)
        with self.assertRaises(ValidationError):
            profile11.clean()

    def test_blood_bank_staff_limit(self):
        # Create 5 staff members
        for i in range(5):
            user = User.objects.create_user(username=f'bb_staff{i}', email=f'bb_staff{i}@example.com', password='pw', role='BLOODBANK_STAFF')
            profile = UserProfile.objects.create(user=user, blood_bank=self.blood_bank)
        
        # 6th should fail validation
        user6 = User.objects.create_user(username='bb_staff6', email='bb_staff6@example.com', password='pw', role='BLOODBANK_STAFF')
        profile6 = UserProfile(user=user6, blood_bank=self.blood_bank)
        with self.assertRaises(ValidationError):
            profile6.clean()

class GlobalConfigModelTest(TestCase):
    def test_global_config_creation(self):
        config = GlobalConfig.objects.create(commission_percentage=15.0)
        self.assertEqual(config.commission_percentage, 15.0)
        self.assertEqual(str(config), "Global Config (Commission: 15.0%)")

class VerificationLogModelTest(TestCase):
    def test_verification_log_creation(self):
        admin = User.objects.create_user(username='admin', email='admin@example.com', password='pw', role='INTERNAL_ADMIN')
        hospital = Hospital.objects.create(name='Log Hospital', state='Lagos')
        
        log = VerificationLog.objects.create(
            admin=admin,
            hospital=hospital,
            action='VERIFIED',
            notes='Looks good'
        )
        self.assertEqual(log.action, 'VERIFIED')
        self.assertEqual(str(log), "admin VERIFIED Log Hospital")

class PotentialDonorModelTest(TestCase):
    def test_potential_donor_creation(self):
        donor = PotentialDonor.objects.create(
            full_name='John Doe',
            phone='1234567890',
            blood_group='O+'
        )
        self.assertEqual(donor.full_name, 'John Doe')
        self.assertEqual(str(donor), 'John Doe')
