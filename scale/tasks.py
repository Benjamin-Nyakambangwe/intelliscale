# your_app/tasks.py
from celery import shared_task
import requests
import logging
from django.utils import timezone
from .models import DeliveryNote

logger = logging.getLogger(__name__)

@shared_task
def sync_odoo_delivery_notes():
    """Fetch all delivery notes from Odoo and sync with Django"""
    try:
        # Fetch from Odoo API
        response = requests.get(
            'http://localhost:8069/api/grower-delivery-notes',
            params={'include_bales': 'true'},
            headers={
                'User-Agent': 'insomnia/11.5.0',
                # Add cookie authentication if needed
                # 'Cookie': 'your-session-cookie-here'
            },
            timeout=30
        )
        
        if response.status_code != 200:
            error_message = (
                f"Odoo API error: Status {response.status_code} for URL {response.url}. "
                f"Response: {response.text}"
            )
            logger.error(error_message)
            return f"API Error: {response.status_code}"
        
        odoo_data = response.json()
        
        if not odoo_data.get('success'):
            logger.error("Odoo API returned success=false")
            return "API returned error"
        
        synced_count = 0
        error_count = 0
        
        # Process each delivery note
        for item in odoo_data['data']:
            try:
                sync_single_delivery_note(item)
                synced_count += 1
            except Exception as e:
                logger.error(f"Error syncing record {item.get('id')}: {str(e)}")
                error_count += 1
        
        result = f"Synced: {synced_count}, Errors: {error_count}"
        logger.info(result)
        return result
        
    except Exception as e:
        logger.error(f"Sync task failed: {str(e)}")
        return f"Task failed: {str(e)}"

def sync_single_delivery_note(odoo_record):
    """Sync a single delivery note record"""
    try:
        odoo_id = odoo_record['id']
        document_number = odoo_record['document_number']
        
        # Get or create delivery note
        delivery_note, created = DeliveryNote.objects.get_or_create(
            odoo_id=odoo_id,
            defaults={
                'delivery_note_number': document_number,
                'created_by_id': 1,  # Set a default user or handle this properly
            }
        )
        
        # Update with Odoo data
        delivery_note.odoo_data = odoo_record
        delivery_note.delivery_note_number = document_number
        # Note: partner_id is IntegerField, but grower_number is string like "V342819"
        # Store grower_number in odoo_data, extract numeric part if needed
        grower_number = odoo_record.get('grower_number', '')
        if grower_number.startswith('V') and grower_number[1:].isdigit():
            delivery_note.partner_id = int(grower_number[1:])  # Extract numeric part
        delivery_note.is_synced = True
        delivery_note.last_sync_attempt = timezone.now()
        delivery_note.sync_error_message = ''
        
        # Map Odoo state to your status
        if odoo_record['state'] in ['open', 'printing']:
            delivery_note.status = 'Open'
        else:  # 'closed'
            delivery_note.status = 'Closed'
        
        delivery_note.save()
        
        action = "Created" if created else "Updated"
        logger.info(f"{action} delivery note: {document_number}")
        
    except Exception as e:
        # Log error but don't crash the whole sync
        logger.error(f"Failed to sync record {odoo_record.get('id')}: {str(e)}")
        
        # Try to update error message if record exists
        try:
            if 'odoo_id' in locals():
                DeliveryNote.objects.filter(odoo_id=odoo_id).update(
                    sync_error_message=str(e),
                    last_sync_attempt=timezone.now(),
                    is_synced=False
                )
        except:
            pass
        
        raise  # Re-raise to be caught by parent function