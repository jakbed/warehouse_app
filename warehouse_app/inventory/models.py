import os
import uuid
from datetime import date
from io import BytesIO
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
    description = models.TextField(blank=True, null=True, help_text="Opis - jeśli posiada inne komponenty, lokalizacja")
    weight = models.CharField(max_length=4, blank=True, null=True, help_text="Waga w kilogramach")
    ean = models.CharField(max_length=13, blank=True, null=True, help_text="Kod EAN")

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



class BorrowHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    borrow_date = models.DateTimeField(auto_now_add=True)
    return_date = models.DateTimeField(null=True, blank=True)

    def is_returned(self):
        return self.return_date is not None

    def __str__(self):
        return f"{self.user.username} - {self.product} ({self.borrow_date} - {self.return_date or 'Nie zwrócono'})"


from .models import Product  # zakładamy, że Product już istnieje

User = get_user_model()


class Order(models.Model):
    STATUS_CHOICES = (
        ('reserved', 'Zarezerwowane'),  # Domyślnie
        ('in_progress', 'W toku'),
        ('completed', 'Zakończone'),
        ('canceled', 'Anulowane'),
    )

    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='reserved')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    # daty
    reservation_date = models.DateField(help_text="Data rezerwacji (złożenia zamówienia)")
    pickup_date = models.DateField(help_text="Data odbioru")
    return_date = models.DateField(help_text="Data zwrotu")
    # lista produktów
    products = models.ManyToManyField('inventory.Product', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} - {self.name}"

    def update_status_if_needed(self):
        """
        Metoda, która na podstawie bieżącej daty ustawia
        odpowiedni status: in_progress (jeśli dzisiaj w zakresie),
        completed (dzień po return_date),
        w innym wypadku status pozostaje reserved/canceled itp.
        """
        today = date.today()

        # Jeśli zamówienie nie jest canceled ani completed, sprawdzamy logikę
        if self.status not in ['canceled', 'completed']:
            if self.pickup_date <= today <= self.return_date:
                self.status = 'in_progress'
            elif today > self.return_date:
                self.status = 'completed'
            else:
                # wciąż 'reserved' lub inne
                pass

            self.save()

    def set_products_in_out(self):
        """
        Ustawia status produktów w zależności od statusu zamówienia:
          - in_progress => produkty "wyjezd"
          - completed / canceled => produkty wracają do "magazyn"
        """
        if self.status == 'in_progress':
            for p in self.products.all():
                if p.state == 'magazyn':
                    p.state = 'wyjezd'
                    p.save(update_fields=['state'])
        elif self.status in ['completed', 'canceled']:
            for p in self.products.all():
                if p.state == 'wyjezd':
                    p.state = 'magazyn'
                    p.save(update_fields=['state'])

    def save(self, *args, **kwargs):
        # Najpierw normalny zapis
        super().save(*args, **kwargs)
        # Następnie aktualizacja stanu (bo np. w pickup_date w przyszłości)
        self.update_status_if_needed()
        # Ustaw produkty
        self.set_products_in_out()
