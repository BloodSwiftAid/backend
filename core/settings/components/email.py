from decouple import config

EMAIL_USE_TLS = True
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# Using Resend's SMTP relay
EMAIL_HOST = "smtp.resend.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = "resend"
EMAIL_HOST_PASSWORD = config("RESEND_API_KEY")

EMAIL_FROM = config("DEFAULT_FROM_EMAIL", "NeoEvent <no-reply@swiftaid.co>")
