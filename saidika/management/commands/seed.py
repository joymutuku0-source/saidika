"""python manage.py seed  - loads the demo catalogue and one capsule per body type.
Safe to run many times (it updates instead of duplicating)."""
from django.core.management.base import BaseCommand

from saidika.models import Outfit, Product

IMG = {
    "tops": "saidika/images/tops.jpg",
    "bottoms": "saidika/images/jeans.jpg",
    "outerwear": "saidika/images/coats.jpg",
    "footwear": "saidika/images/shoes.jpg",
}

PRODUCTS = [
    # name, category, price, colour, description
    ("Ivory Wrap Blouse", "tops", 1800, "Ivory", "Soft crepe wrap blouse that follows the waist."),
    ("Blush Ribbed Henley", "tops", 1500, "Blush", "Stretch ribbed knit with a button placket."),
    ("Structured White Shirt", "tops", 2200, "White", "Crisp cotton shirt, the capsule workhorse."),
    ("Soft Grey Layer Tee", "tops", 1300, "Grey", "Longline tee made for layering."),
    ("Square-Neck Bodysuit", "tops", 1700, "Black", "Smooth jersey bodysuit with a square neckline."),
    ("High-Waist Straight Jeans", "bottoms", 3200, "Light denim", "Rigid denim, straight leg, sits at the natural waist."),
    ("Wide-Leg Sky Denim", "bottoms", 3500, "Sky blue", "Fluid wide leg that balances the shoulders."),
    ("Tailored Black Trousers", "bottoms", 3800, "Black", "Pleat-front trousers with a clean drape."),
    ("Relaxed Cream Chinos", "bottoms", 3000, "Cream", "Easy chinos in a mid-weight twill."),
    ("Camel Corduroy Jacket", "outerwear", 5200, "Camel", "Boxy corduroy overshirt jacket."),
    ("Charcoal Utility Jacket", "outerwear", 5600, "Charcoal", "Structured jacket with chest pockets."),
    ("Espresso Knit Blazer", "outerwear", 6200, "Espresso", "Textured blazer that dresses any outfit up."),
    ("Grey Zip Hoodie", "outerwear", 3400, "Heather grey", "Weekend layer in brushed cotton."),
    ("Court Sneakers", "footwear", 4500, "White & tan", "Everyday leather-look sneakers."),
    ("Clean White Trainers", "footwear", 4200, "White", "Minimal trainers that go with everything."),
    ("Mid-Top Street Sneakers", "footwear", 5200, "Blue & white", "Statement mid-tops for relaxed looks."),
    ("Leather Ankle Boots", "footwear", 6800, "Black", "Polished boots for work or evenings."),
]

OUTFITS = [
    {
        "name": "The Waist Definer", "body_type": "hourglass",
        "tagline": "Follow your natural line.",
        "tips": "Choose wrap and fitted tops, tuck in, and wear high-waisted bottoms so your waist stays the focal point.",
        "items": ["Ivory Wrap Blouse", "High-Waist Straight Jeans", "Camel Corduroy Jacket", "Clean White Trainers"],
    },
    {
        "name": "The Balance Capsule", "body_type": "pear",
        "tagline": "Draw the eye upward.",
        "tips": "Structured shoulders and lighter colours on top, darker bottoms below. Add a blazer for shape.",
        "items": ["Structured White Shirt", "Tailored Black Trousers", "Espresso Knit Blazer", "Leather Ankle Boots"],
    },
    {
        "name": "The Shape Maker", "body_type": "rectangle",
        "tagline": "Create curves with layers.",
        "tips": "Layer textures, add a belt, and try cropped or cinched tops to define the waist.",
        "items": ["Square-Neck Bodysuit", "Wide-Leg Sky Denim", "Charcoal Utility Jacket", "Court Sneakers"],
    },
    {
        "name": "The Easy Lengthener", "body_type": "apple",
        "tagline": "Long lines, open layers.",
        "tips": "V-necks and open layers elongate. Choose fabrics with drape and keep the bottom half clean and simple.",
        "items": ["Soft Grey Layer Tee", "Relaxed Cream Chinos", "Grey Zip Hoodie", "Clean White Trainers"],
    },
    {
        "name": "The Grounded Look", "body_type": "inverted",
        "tagline": "Add volume below.",
        "tips": "Keep tops simple, then wear wide-leg and A-line bottoms to balance broader shoulders.",
        "items": ["Blush Ribbed Henley", "Wide-Leg Sky Denim", "Camel Corduroy Jacket", "Mid-Top Street Sneakers"],
    },
]


class Command(BaseCommand):
    help = "Load demo products and outfits"

    def handle(self, *args, **opts):
        for name, cat, price, colour, desc in PRODUCTS:
            Product.objects.update_or_create(
                name=name,
                defaults=dict(category=cat, price=price, color=colour, description=desc, image=IMG[cat], in_stock=True),
            )
        for data in OUTFITS:
            outfit, _ = Outfit.objects.update_or_create(
                name=data["name"],
                defaults=dict(body_type=data["body_type"], tagline=data["tagline"], tips=data["tips"]),
            )
            outfit.products.set(Product.objects.filter(name__in=data["items"]))
        self.stdout.write(self.style.SUCCESS(
            f"Seeded {Product.objects.count()} products and {Outfit.objects.count()} outfits."
        ))
