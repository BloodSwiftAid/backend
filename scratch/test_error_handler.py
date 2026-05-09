import os
import sys
import django
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler

# Setup Django
sys.path.append('/Users/sunday/Documents/Project/swiftAid/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from core.utils.error_handler import custom_exception_handler

# Mock context
class MockContext:
    pass

# Test 1: Field-level validation error
exc1 = ValidationError({"new_password": ["This password is too common.", "This password is entirely numeric."]})
resp1 = custom_exception_handler(exc1, MockContext())
print(f"Test 1 Data: {resp1.data}")

# Test 2: Generic validation error
exc2 = ValidationError("Incorrect old password.")
resp2 = custom_exception_handler(exc2, MockContext())
print(f"Test 2 Data: {resp2.data}")

# Test 3: List error
exc3 = ValidationError(["Error one", "Error two"])
resp3 = custom_exception_handler(exc3, MockContext())
print(f"Test 3 Data: {resp3.data}")
