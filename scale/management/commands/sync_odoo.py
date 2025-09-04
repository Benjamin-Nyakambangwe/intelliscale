from django.core.management.base import BaseCommand
from scale.tasks import sync_odoo_delivery_notes

class Command(BaseCommand):
    help = 'Manually sync Odoo delivery notes'

    def handle(self, *args, **options):
        self.stdout.write('Starting Odoo sync...')
        result = sync_odoo_delivery_notes()
        self.stdout.write(self.style.SUCCESS(f'Sync completed: {result}'))