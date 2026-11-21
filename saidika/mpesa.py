"""
Daraja (Safaricom M-Pesa) helper: STK Push + callback handling.

If MPESA_KEY is not configured the app runs in SIMULATION mode, so the whole
flow (register -> pay -> shop -> checkout) still works for demos.
"""
import base64
import re
from datetime import datetime

import requests
from django.conf import settings
from django.urls import reverse

from .models import Payment

BASE_URLS = {
    "sandbox": "https://sandbox.safaricom.co.ke",
    "production": "https://api.safaricom.co.ke",
}


def simulation_mode():
    return not (settings.MPESA_KEY and settings.MPESA_SECRET and settings.MPESA_PASSKEY)


def normalize_phone(raw):
    """Accepts 07.. and the newer 01.. Safaricom numbers, with or without +254.
    0712345678 / 0112345678 / +254112345678  ->  254712345678 / 254112345678"""
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("2540") and len(digits) == 13:   # 2540712345678 -> 254712345678
        digits = "254" + digits[4:]
    if digits.startswith("0") and len(digits) == 10:
        digits = "254" + digits[1:]
    elif digits.startswith("7") or digits.startswith("1"):
        if len(digits) == 9:
            digits = "254" + digits
    if re.fullmatch(r"254[17]\d{8}", digits):
        return digits
    return None


def _base():
    return BASE_URLS.get(settings.MPESA_ENV, BASE_URLS["sandbox"])


def get_token():
    r = requests.get(
        f"{_base()}/oauth/v1/generate?grant_type=client_credentials",
        auth=(settings.MPESA_KEY, settings.MPESA_SECRET),
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def callback_url(request):
    if settings.MPESA_CALLBACK_URL:
        return settings.MPESA_CALLBACK_URL
    return request.build_absolute_uri(reverse("mpesa_callback"))


def mark_success(payment, receipt="SIMULATED"):
    """Apply the effects of a successful payment."""
    payment.status = "SUCCESS"
    payment.receipt = receipt
    payment.save()
    if payment.purpose == "REGISTRATION":
        profile = payment.user.profile
        profile.registration_paid = True
        profile.save()
    elif payment.purpose == "ORDER" and payment.order:
        payment.order.status = "PAID"
        payment.order.save()


def mark_failed(payment, reason=""):
    payment.status = "FAILED"
    payment.note = reason[:200]
    payment.save()
    if payment.purpose == "ORDER" and payment.order:
        payment.order.status = "FAILED"
        payment.order.save()


def start_payment(request, user, phone, amount, purpose, order=None):
    """Create a Payment and send the STK Push prompt. Returns the Payment."""
    payment = Payment.objects.create(
        user=user, purpose=purpose, order=order, phone=phone, amount=amount
    )

    if simulation_mode():
        mark_success(payment, receipt="SIM" + str(payment.pk).zfill(6))
        payment.note = "Simulation mode (no Daraja keys set)"
        payment.save()
        return payment

    try:
        token = get_token()
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(
            f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{ts}".encode()
        ).decode()
        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": ts,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone,
            "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": phone,
            "CallBackURL": callback_url(request),
            "AccountReference": "WardrobeCapsule",
            "TransactionDesc": "Wardrobe Capsule payment",
        }
        r = requests.post(
            f"{_base()}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=20,
        )
        data = r.json()
        if data.get("ResponseCode") == "0":
            payment.checkout_request_id = data.get("CheckoutRequestID", "")
            payment.save()
        else:
            mark_failed(payment, data.get("errorMessage") or data.get("ResponseDescription", "STK push rejected"))
    except Exception as exc:  # network error, bad keys, etc.
        mark_failed(payment, f"Daraja error: {exc}")
    return payment


def handle_callback(body):
    """Process the JSON Safaricom posts to our callback URL."""
    cb = body["Body"]["stkCallback"]
    payment = Payment.objects.filter(checkout_request_id=cb.get("CheckoutRequestID")).first()
    if not payment or payment.status != "PENDING":
        return
    if cb.get("ResultCode") == 0:
        receipt = ""
        for item in cb.get("CallbackMetadata", {}).get("Item", []):
            if item.get("Name") == "MpesaReceiptNumber":
                receipt = str(item.get("Value", ""))
        mark_success(payment, receipt=receipt)
    else:
        mark_failed(payment, cb.get("ResultDesc", "Payment failed or cancelled"))
