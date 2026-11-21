from decimal import Decimal
from functools import wraps
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import mpesa
from .forms import PayForm, QuizForm, SignUpForm
from .models import (BODY_TYPES, CATEGORIES, Order, OrderItem, Outfit, Payment,
                     Product, Profile)

BODY_TYPE_INFO = {
    "hourglass": "Balanced bust and hips with a defined waist. Fitted and wrap shapes follow your natural line.",
    "pear": "Hips wider than shoulders. Structured tops and light layers balance the silhouette.",
    "rectangle": "Straight, even proportions. Belts, layers and texture create shape.",
    "apple": "Weight carried around the midsection. Open layers, V-necks and long lines elongate.",
    "inverted": "Broader shoulders than hips. Wide-leg and A-line bottoms add balance below.",
}


def classify_body_type(bust, waist, hips):
    """Simple measurement-based heuristic. A starting point, not a rule."""
    big = max(bust, hips)
    if waist >= bust * 0.95 and waist >= hips * 0.95:
        return "apple"
    if abs(bust - hips) / big <= 0.05:
        return "hourglass" if waist / big <= 0.75 else "rectangle"
    if hips > bust * 1.05:
        return "pear"
    if bust > hips * 1.05:
        return "inverted"
    return "rectangle"


def lookbook_images():
    """Existing photos are always kept. Any image you drop into
    saidika/static/saidika/images/lookbook/ is added to the gallery automatically."""
    base = [
        "saidika/images/hero.jpg", "saidika/images/tops.jpg", "saidika/images/jeans.jpg",
        "saidika/images/coats.jpg", "saidika/images/shoes.jpg",
    ]
    folder = Path(settings.BASE_DIR) / "saidika" / "static" / "saidika" / "images" / "lookbook"
    extra = []
    if folder.exists():
        extra = [
            f"saidika/images/lookbook/{f.name}" for f in sorted(folder.iterdir())
            if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        ]
    return extra + base


def paid_required(view):
    """Account must exist AND the registration fee must be paid."""
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        if not profile.registration_paid:
            messages.info(request, "Complete your registration payment to unlock your capsule.")
            return redirect("activate")
        return view(request, *args, **kwargs)
    return wrapper


# ------------------------------------------------------------------ public pages
def home(request):
    outfits = Outfit.objects.prefetch_related("products")[:3]
    return render(request, "saidika/home.html", {
        "fee": settings.REGISTRATION_FEE,
        "body_types": [(k, v, BODY_TYPE_INFO[k]) for k, v in BODY_TYPES],
        "outfits": outfits,
        "featured": Product.objects.filter(in_stock=True)[:4],
        "lookbook": lookbook_images(),
    })


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        Profile.objects.create(user=user, phone=form.cleaned_data["phone"])
        login(request, user)
        return redirect("activate")
    return render(request, "saidika/signup.html", {"form": form, "fee": settings.REGISTRATION_FEE})


# ------------------------------------------------------------ registration payment
@login_required
def activate(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if profile.registration_paid:
        return redirect("dashboard")
    form = PayForm(request.POST or None, initial={"phone": profile.phone})
    if request.method == "POST" and form.is_valid():
        payment = mpesa.start_payment(
            request, request.user, form.cleaned_data["phone"],
            settings.REGISTRATION_FEE, "REGISTRATION",
        )
        return redirect("payment_status", pk=payment.pk)
    return render(request, "saidika/activate.html", {
        "form": form, "fee": settings.REGISTRATION_FEE, "simulated": mpesa.simulation_mode(),
    })


@login_required
def payment_status(request, pk):
    payment = get_object_or_404(Payment, pk=pk, user=request.user)
    return render(request, "saidika/payment_status.html", {
        "payment": payment, "simulated": mpesa.simulation_mode(),
    })


@login_required
def payment_status_json(request, pk):
    payment = get_object_or_404(Payment, pk=pk, user=request.user)
    return JsonResponse({"status": payment.status, "receipt": payment.receipt, "note": payment.note})


# ------------------------------------------------------------------- member area
@paid_required
def dashboard(request):
    profile = request.user.profile
    outfit = Outfit.objects.filter(body_type=profile.body_type).first() if profile.body_type else None
    return render(request, "saidika/dashboard.html", {
        "profile": profile,
        "outfit": outfit,
        "orders": request.user.orders.filter(status="PAID")[:5],
        "info": BODY_TYPE_INFO.get(profile.body_type, ""),
    })


@paid_required
def curate(request):
    profile = request.user.profile
    form = QuizForm(request.POST or None, initial={"size": profile.size or "M", "style": profile.style or "minimal"})
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        if d.get("bust") and d.get("waist") and d.get("hips"):
            body_type = classify_body_type(d["bust"], d["waist"], d["hips"])
        else:
            body_type = d["body_type"]
        profile.body_type = body_type
        profile.size = d["size"]
        profile.style = d["style"]
        profile.save()
        return redirect("capsule")
    return render(request, "saidika/curate.html", {"form": form})


@paid_required
def capsule(request):
    profile = request.user.profile
    if not profile.body_type:
        return redirect("curate")
    outfits = Outfit.objects.filter(body_type=profile.body_type).prefetch_related("products")
    return render(request, "saidika/capsule.html", {
        "profile": profile,
        "info": BODY_TYPE_INFO.get(profile.body_type, ""),
        "outfits": outfits,
    })


@paid_required
def closet(request):
    category = request.GET.get("category", "")
    products = Product.objects.filter(in_stock=True)
    if category in dict(CATEGORIES):
        products = products.filter(category=category)
    return render(request, "saidika/closet.html", {
        "products": products, "categories": CATEGORIES, "active": category,
    })


# -------------------------------------------------------------------------- cart
def _cart(request):
    return request.session.setdefault("cart", {})


@paid_required
@require_POST
def cart_add(request, pk):
    product = get_object_or_404(Product, pk=pk, in_stock=True)
    cart = _cart(request)
    cart[str(product.pk)] = cart.get(str(product.pk), 0) + 1
    request.session.modified = True
    messages.success(request, f"{product.name} added to your bag.")
    return redirect(request.POST.get("next") or "closet")


@paid_required
@require_POST
def cart_add_outfit(request, pk):
    outfit = get_object_or_404(Outfit, pk=pk)
    cart = _cart(request)
    for product in outfit.products.filter(in_stock=True):
        cart[str(product.pk)] = cart.get(str(product.pk), 0) + 1
    request.session.modified = True
    messages.success(request, f"The “{outfit.name}” capsule is in your bag.")
    return redirect("cart")


@paid_required
@require_POST
def cart_remove(request, pk):
    cart = _cart(request)
    cart.pop(str(pk), None)
    request.session.modified = True
    return redirect("cart")


def _cart_lines(request):
    cart = request.session.get("cart", {})
    products = Product.objects.in_bulk([int(k) for k in cart])
    lines, total = [], Decimal("0")
    for key, qty in cart.items():
        product = products.get(int(key))
        if product:
            subtotal = product.price * qty
            total += subtotal
            lines.append({"product": product, "qty": qty, "subtotal": subtotal})
    return lines, total


@paid_required
def cart(request):
    lines, total = _cart_lines(request)
    return render(request, "saidika/cart.html", {"lines": lines, "total": total})


@paid_required
def checkout(request):
    lines, total = _cart_lines(request)
    if not lines:
        messages.info(request, "Your bag is empty.")
        return redirect("closet")
    form = PayForm(request.POST or None, initial={"phone": request.user.profile.phone})
    if request.method == "POST" and form.is_valid():
        order = Order.objects.create(user=request.user, total=total)
        for line in lines:
            OrderItem.objects.create(
                order=order, product=line["product"], quantity=line["qty"], price=line["product"].price
            )
        payment = mpesa.start_payment(
            request, request.user, form.cleaned_data["phone"], total, "ORDER", order=order
        )
        request.session["cart"] = {}
        return redirect("payment_status", pk=payment.pk)
    return render(request, "saidika/checkout.html", {
        "form": form, "lines": lines, "total": total, "simulated": mpesa.simulation_mode(),
    })


@paid_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, "saidika/order_detail.html", {"order": order})
