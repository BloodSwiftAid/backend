from django.core import mail
from django.test import TestCase

from core.mail import (
    _send_email,
    send_verification_email,
    send_onboarding_email,
    send_password_reset_email,
    send_password_changed_email,
)


class MailTestCase(TestCase):
    def test_send_email_success(self):
        """Test the underlying _send_email function via Django's outbox."""
        with self.settings(EMAIL_FROM="test@swiftaid.com"):
            attachments = [
                ("test.txt", b"hello world", "text/plain"),
            ]
            response = _send_email(
                recipient="user@example.com",
                subject="Test Subject",
                body_text="Test text",
                body_html="<p>Test HTML</p>",
                attachments=attachments,
                quiet=False,
            )

            self.assertTrue(response)
            
            self.assertEqual(len(mail.outbox), 1)
            email = mail.outbox[0]
            
            self.assertEqual(email.from_email, "test@swiftaid.com")
            self.assertEqual(email.to, ["user@example.com"])
            self.assertEqual(email.subject, "Test Subject")
            self.assertEqual(email.body, "Test text\n")
            
            self.assertEqual(len(email.alternatives), 1)
            self.assertEqual(email.alternatives[0], ("<p>Test HTML</p>", "text/html"))
            
            self.assertEqual(len(email.attachments), 1)
            self.assertEqual(email.attachments[0][0], "test.txt")
            self.assertEqual(email.attachments[0][1], "hello world")
            self.assertEqual(email.attachments[0][2], "text/plain")

    def test_send_verification_email(self):
        """Test sending a verification email triggers _send_email with correct templates."""
        send_verification_email("user@example.com", "123456")
        
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        
        self.assertEqual(email.to, ["user@example.com"])
        self.assertEqual(email.subject, "Verify Your SwiftAid Account")
        
        html_body = email.alternatives[0][0]
        self.assertIn("123456", html_body)

    def test_send_onboarding_email(self):
        """Test sending an onboarding email."""
        send_onboarding_email(
            user_email="staff@hospital.com",
            temporary_password="temp_password",
            facility_name="General Hospital",
            facility_type="hospital",
            portal_url="http://localhost:3000/login",
            inviter_name="Dr. Smith"
        )
        
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        
        self.assertEqual(email.to, ["staff@hospital.com"])
        self.assertEqual(email.subject, "You've Been Invited to SwiftAid — General Hospital")
        
        html_body = email.alternatives[0][0]
        self.assertIn("temp_password", html_body)
        self.assertIn("General Hospital", html_body)
        self.assertIn("Dr. Smith", html_body)

    def test_send_password_reset_email(self):
        """Test sending a password reset email."""
        send_password_reset_email("user@example.com", "RESET123")
        
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        
        self.assertEqual(email.to, ["user@example.com"])
        self.assertEqual(email.subject, "Password Reset Request — SwiftAid")
        
        html_body = email.alternatives[0][0]
        self.assertIn("RESET123", html_body)

    def test_send_password_changed_email(self):
        """Test sending a password changed confirmation email."""
        send_password_changed_email("user@example.com")
        
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        
        self.assertEqual(email.to, ["user@example.com"])
        self.assertEqual(email.subject, "Your Password Has Been Changed — SwiftAid")
        
        html_body = email.alternatives[0][0]
        self.assertIn("user@example.com", html_body)
