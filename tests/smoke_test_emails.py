import os
import sys
import django

def run_smoke_test(email_address):
    print(f"Starting email smoke tests for: {email_address}\n")
    
    # 1. Verification Email
    print("1. Sending Verification Email...")
    try:
        from core.mail import send_verification_email
        send_verification_email(email_address, "842915")
        print("   ✅ Sent successfully.")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    print("\n2. Sending Onboarding Invitation...")
    try:
        from core.mail import send_onboarding_email
        send_onboarding_email(
            user_email=email_address,
            temporary_password="TempPassword123!",
            facility_name="Lagos University Teaching Hospital",
            facility_type="hospital",
            portal_url="https://app.swiftaid.co/login",
            inviter_name="SwiftAid Team",
            role="ADMIN",
        )
        print("   ✅ Sent successfully.")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # 3. Password Reset
    print("\n3. Sending Password Reset OTP...")
    try:
        from core.mail import send_password_reset_email
        send_password_reset_email(email_address, "XYZ-992")
        print("   ✅ Sent successfully.")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # 4. Password Changed
    print("\n4. Sending Password Changed Confirmation...")
    try:
        from core.mail import send_password_changed_email
        send_password_changed_email(email_address)
        print("   ✅ Sent successfully.")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        
    print("\nSmoke tests completed. Please check your inbox.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python smoke_test_emails.py <email_address>")
        sys.exit(1)

    # Setup Django environment
    # Ensure the script can find the 'core' app by adding the parent dir to sys.path
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, backend_dir)
    
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    django.setup()

    target_email = sys.argv[1]
    run_smoke_test(target_email)
