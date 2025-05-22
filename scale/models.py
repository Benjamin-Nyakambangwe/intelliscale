from django.db import models
from users.models import CustomUser

class Scale(models.Model):
    name = models.CharField(max_length=100)
    com_port = models.CharField(max_length=50)
    manufacturer = models.CharField(max_length=50)
    model_number = models.CharField(max_length=50)
    max_capacity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Maximum weight capacity in kg")
    is_active = models.BooleanField(default=True)
    last_connection_status = models.CharField(max_length=50, default='disconnected')
    last_seen = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.model_number})"
    
    
class WeighingProcess(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    custom_fields_schema = models.JSONField(default=list, blank=True)
    erp_target_model = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    

class Product(models.Model):
    erp_product_id = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    

class WeighingRecord(models.Model):
    scale = models.ForeignKey(Scale, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    process = models.ForeignKey(WeighingProcess, on_delete=models.CASCADE)
    barcode = models.CharField(max_length=100, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    gross_weight = models.DecimalField(max_digits=10, decimal_places=2)
    tare_weight = models.DecimalField(max_digits=10, decimal_places=2)
    net_weight = models.DecimalField(max_digits=10, decimal_places=2)
    unit_of_measure = models.CharField(max_length=50)
    custom_data = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    is_synced = models.BooleanField(default=False)
    erp_record_id = models.CharField(max_length=100, blank=True)
    erp_model_name = models.CharField(max_length=100, blank=True)
    last_sync_attempt = models.DateTimeField(null=True, blank=True)
    sync_error_message = models.TextField(blank=True)
    print_count = models.IntegerField(default=0)
    last_printed_at = models.DateTimeField(null=True, blank=True)
    delivery_note = models.ForeignKey('DeliveryNote', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.scale.name} - {self.product.name} - {self.timestamp}"
    

class DeliveryNote(models.Model):
    delivery_note_number = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    status = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_synced = models.BooleanField(default=False)
    last_sync_attempt = models.DateTimeField(null=True, blank=True)
    sync_error_message = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.delivery_note_number}"
    
    
