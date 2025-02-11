import os
import uuid
from io import BytesIO
from django.conf import settings
from django.db import models
from django.core.files.base import ContentFile
from PIL import Image
from django.contrib.auth import get_user_model

User = get_user_model()

class Product(models.Model):
    """
    Model opisujący pojedynczy produkt w magazynie.
    """
    STATE_CHOICES = (
        ('magazyn', 'Magazyn'),
        ('wyjezd', 'Na wyjeździe'),
    )

    code = models.CharField(max_length=20, unique=True, blank=True)
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    custom_name = models.CharField(max_length=100, blank=True, null=True,
                                   help_text="Opcjonalna nazwa własna")
    serial_number = models.CharField(max_length=100, blank=True, null=True,
                                     help_text="Opcjonalny numer seryjny")
    description = models.TextField(blank=True, null=True)

    # Oryginalne zdjęcie
    photo_original = models.ImageField(
        upload_to='products/photos/original/',
        blank=True, null=True,
        help_text="Oryginalne zdjęcie produktu (opcjonalne)"
    )

    # Konwertowane do WebP (wewnętrznie, nie wyświetlamy w UI)
    photo_converted = models.ImageField(
        upload_to='products/images/',
        blank=True, null=True,
        help_text="Przekonwertowane zdjęcie (WebP)"
    )

    state = models.CharField(max_length=10, choices=STATE_CHOICES, default='magazyn')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Generowanie kodu, jeśli nie został podany
        if not self.code:
            prefix = (self.brand[:3] + self.model[:3]).upper()
            count = Product.objects.filter(code__startswith=prefix).count() + 1
            self.code = f"{prefix}{count:03d}"

        super().save(*args, **kwargs)

        # Konwersja obrazu do WebP, jeśli przesłano oryginalne zdjęcie
        if self.photo_original:
            self.convert_image()

    def convert_image(self):
        if not self.photo_original:
            return
        try:
            img = Image.open(self.photo_original)
        except Exception as e:
            print("Błąd przy otwieraniu obrazu:", e)
            return
        # Zmiana rozmiaru (np. 1080x1080) i konwersja na WebP
        max_size = (1080, 1080)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        img_io = BytesIO()
        img.save(img_io, format='WEBP', quality=80)
        img_content = ContentFile(img_io.getvalue())

        unique_filename = f"{uuid.uuid4().hex}.webp"
        converted_path = os.path.join("products", "images", unique_filename)

        self.photo_converted.save(converted_path, img_content, save=False)
        super().save(update_fields=['photo_converted'])

    def __str__(self):
        return f"{self.brand} {self.model} ({self.code})"


class Komplet(models.Model):
    """
    Model zestawu (kompletu). Każdy komplet może zawierać wiele produktów.
    """
    name = models.CharField(max_length=100)
    products = models.ManyToManyField(Product, related_name='komplety', blank=True)

    def __str__(self):
        return self.name


class BorrowingRecord(models.Model):
    """
    Historia wypożyczeń / wyjazdów. Rejestrujemy kto, kiedy i na jak długo wypożyczył dany produkt.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    borrow_start = models.DateField()
    borrow_end = models.DateField()
    borrow_date = models.DateTimeField(auto_now_add=True)
    return_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.product} wypożyczony przez {self.user} od {self.borrow_start} do {self.borrow_end}"
