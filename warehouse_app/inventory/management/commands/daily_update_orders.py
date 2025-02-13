# inventory/management/commands/daily_update_orders.py
from django.core.management.base import BaseCommand
from warehouse_app.inventory.models import Order
class Command(BaseCommand):
    help = "Codzienna aktualizacja statusów zamówień (Order) oraz stanów produktów."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Rozpoczynam aktualizację zamówień..."))

        # Pobieramy wszystkie zamówienia, które nie są canceled ani completed
        orders = Order.objects.exclude(status__in=['canceled', 'completed'])
        count = 0

        for order in orders:
            old_status = order.status
            # Metoda update_status_if_needed() -> wywoła .save() i set_products_in_out()
            order.update_status_if_needed()

            # Sprawdzamy, czy status faktycznie się zmienił
            if order.status != old_status:
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Aktualizacja zakończona. Zmodyfikowano {count} zamówień."))
