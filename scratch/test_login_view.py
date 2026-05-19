import os
import sys
import django

# Setup Django
sys.path.append('/Users/sunday/Documents/Project/swiftAid/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import User
from rest_framework.test import APIClient

# Ensure temporary user exists
email = 'testuser@swiftaid.com'
username = 'testuser'
password = 'password123'

User.objects.filter(email=email).delete()
User.objects.filter(username=username).delete()

u = User.objects.create_user(username=username, email=email, password=password)
print(f"Created temporary user: {u}")

client = APIClient()

# Attempt to log in with correct credentials
print("Sending login request with correct credentials...")
response = client.post(
    '/api/v1/auth/login/',
    {'username': email, 'password': password},
    format='json'
)

print(f"Status Code: {response.status_code}")
print(f"Response Body: {response.content}")

# Clean up
u.delete()
print("Cleaned up temporary user.")
