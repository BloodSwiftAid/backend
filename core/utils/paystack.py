import requests
from django.conf import settings
from decouple import config

class PaystackProvider:
    def __init__(self):
        self.secret_key = config('PAYSTACK_SECRET_KEY', default='sk_test_placeholder')
        self.base_url = "https://api.paystack.co"
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

    def initialize_transaction(self, email, amount, reference, callback_url=None):
        """
        Amount should be in Naira (converted to kobo for Paystack)
        """
        url = f"{self.base_url}/transaction/initialize"
        payload = {
            "email": email,
            "amount": int(float(amount) * 100),
            "reference": reference,
        }
        if callback_url:
            payload["callback_url"] = callback_url

        response = requests.post(url, json=payload, headers=self.headers)
        return response.json()

    def verify_transaction(self, reference):
        url = f"{self.base_url}/transaction/verify/{reference}"
        response = requests.get(url, headers=self.headers)
        return response.json()

    @staticmethod
    def calculate_fees(amount):
        """
        Calculates Paystack fees (1.5% + 100, capped at 2000)
        Calculates our service fee (e.g. 5% commission)
        """
        amount = float(amount)
        # Paystack Fee
        gateway_fee = (amount * 0.015)
        if amount >= 2500:
            gateway_fee += 100
        
        gateway_fee = min(gateway_fee, 2000)
        
        # Our Service Fee (Profit) - Let's assume 5% for now or from setting
        commission_pct = float(config('COMMISSION_PERCENTAGE', default=5.0))
        service_fee = amount * (commission_pct / 100)
        
        blood_bank_fee = amount - gateway_fee - service_fee
        
        return {
            "total_amount": amount,
            "gateway_fee": round(gateway_fee, 2),
            "service_fee": round(service_fee, 2),
            "blood_bank_fee": round(blood_bank_fee, 2),
            "commission_percentage": commission_pct
        }

    def create_transfer_recipient(self, name, account_number, bank_code):
        """
        Create a transfer recipient on Paystack
        """
        url = f"{self.base_url}/transferrecipient"
        payload = {
            "type": "nuban",
            "name": name,
            "account_number": account_number,
            "bank_code": bank_code,
            "currency": "NGN"
        }
        response = requests.post(url, json=payload, headers=self.headers)
        return response.json()

    def initiate_transfer(self, amount, recipient_code, reference, reason="SwiftAid Payout"):
        """
        Initiate a transfer from Paystack balance to a recipient
        """
        url = f"{self.base_url}/transfer"
        payload = {
            "source": "balance",
            "amount": int(float(amount) * 100),
            "recipient": recipient_code,
            "reference": reference,
            "reason": reason
        }
        response = requests.post(url, json=payload, headers=self.headers)
        return response.json()
