from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .mpesa import normalize_phone
from .models import BODY_TYPES, SIZES

STYLES = [
    ("minimal", "Minimal & clean"),
    ("classic", "Classic & polished"),
    ("street", "Street & relaxed"),
    ("soft", "Soft & feminine"),
]


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(
        label="M-Pesa phone number",
        help_text="Works with 07XX and the newer 01XX numbers, e.g. 0712 345 678 or 0112 345 678.",
        widget=forms.TextInput(attrs={"placeholder": "07XX XXX XXX or 01XX XXX XXX", "inputmode": "tel"}),
    )

    class Meta:
        model = User
        fields = ("username", "email", "phone", "password1", "password2")

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data["phone"])
        if not phone:
            raise forms.ValidationError("Enter a valid Safaricom number, e.g. 0712345678 or 0112345678.")
        return phone

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class PayForm(forms.Form):
    phone = forms.CharField(
        label="M-Pesa phone number",
        widget=forms.TextInput(attrs={"placeholder": "07XX XXX XXX or 01XX XXX XXX", "inputmode": "tel"}),
    )

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data["phone"])
        if not phone:
            raise forms.ValidationError("Enter a valid Safaricom number, e.g. 0712345678 or 0112345678.")
        return phone


class QuizForm(forms.Form):
    size = forms.ChoiceField(choices=SIZES, initial="M")
    style = forms.ChoiceField(choices=STYLES, label="Your style")
    bust = forms.FloatField(required=False, min_value=50, max_value=200, label="Bust (cm)")
    waist = forms.FloatField(required=False, min_value=40, max_value=200, label="Waist (cm)")
    hips = forms.FloatField(required=False, min_value=50, max_value=220, label="Hips (cm)")
    body_type = forms.ChoiceField(
        choices=[("", "I'm not sure, use my measurements")] + BODY_TYPES,
        required=False,
        label="Selected silhouette",
    )

    def clean(self):
        data = super().clean()
        has_measure = all(data.get(k) for k in ("bust", "waist", "hips"))
        if not has_measure and not data.get("body_type"):
            raise forms.ValidationError(
                "Add all three measurements, or pick a silhouette from the list."
            )
        return data
