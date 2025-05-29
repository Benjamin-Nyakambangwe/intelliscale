from django import forms
from .models import Scale, WeighingProcess, Product, DeliveryNote, CompanySettings
import serial.tools.list_ports

class ScaleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Dynamically populate COM port choices
        com_port_choices = [('', 'Auto-detect / Not set')]
        try:
            ports = serial.tools.list_ports.comports()
            detected_ports_choices = [(port.device, f"{port.device} ({port.description.split(' (COM')[0]})") for port in ports]
        except Exception as e:
            print(f"Error listing COM ports: {e}")
            detected_ports_choices = []

        current_com_port_value = None
        if self.instance and self.instance.pk and self.instance.com_port:
            current_com_port_value = self.instance.com_port
            # Add current value to choices if not in detected list
            if not any(current_com_port_value == p[0] for p in detected_ports_choices):
                # Check if it's not already the default empty choice
                if current_com_port_value != '':
                    com_port_choices.append((current_com_port_value, f"{current_com_port_value} (Currently saved, not detected)"))
        
        com_port_choices.extend(detected_ports_choices)
        
        # Preserve existing attrs (like class) and set choices
        com_port_attrs = self.fields['com_port'].widget.attrs
        self.fields['com_port'].widget = forms.Select(attrs=com_port_attrs, choices=com_port_choices)
        
        if current_com_port_value:
            self.initial['com_port'] = current_com_port_value
        elif not self.instance.pk: # For new forms, default to 'Auto-detect'
            self.initial['com_port'] = ''


    class Meta:
        model = Scale
        fields = [
            'name', 
            'com_port',
            'manufacturer',
            'model_number', 
            'max_capacity', 
            'is_active',
            'last_connection_status',
            'last_seen'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-zinc-800 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
            }),
            'com_port': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
            }),
            'model_number': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
            }),
            'max_capacity': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 border-zinc-300 rounded focus:ring-blue-500'
            }),
            'last_connection_status': forms.Select(attrs={
                'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
            }),
            'last_seen': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
            }),
        }
        
        
        
class WeighingProcessForm(forms.ModelForm):
    class Meta:
        model = WeighingProcess
        fields = [
            'name',
            'description',
            'custom_fields_schema',
            'erp_target_model',
            'max_weight',
            'min_weight',
            'weight_rounding',
            'allow_manual_entry',
            'is_active'
        ]
    
    widgets = {
        'name': forms.TextInput(attrs={
            'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
        }),
        'description': forms.Textarea(attrs={
            'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
        }),
        'custom_fields_schema': forms.Textarea(attrs={
            'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
        }),
        'erp_target_model': forms.TextInput(attrs={
            'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
        }),
        'is_active': forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 border-zinc-300 rounded focus:ring-blue-500'
        }),
        'max_weight': forms.NumberInput(attrs={
            'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
        }),
        'min_weight': forms.NumberInput(attrs={
            'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
        }),
        'weight_rounding': forms.NumberInput(attrs={
            'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
        }),
        'allow_manual_entry': forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 border-zinc-300 rounded focus:ring-blue-500'
        }),
    }
    
    def clean_is_active(self):
        is_active = self.cleaned_data.get('is_active')
        
        # If the process is being set to active, check for other active processes
        if is_active:
            # Get the current instance ID (if it exists)
            instance_id = self.instance.id if self.instance and self.instance.pk else None
            
            # Check if there are any other active processes
            other_active_processes = WeighingProcess.objects.filter(is_active=True)
            
            # Exclude the current instance if it exists
            if instance_id:
                other_active_processes = other_active_processes.exclude(id=instance_id)
            
            # If there are other active processes, raise a validation error
            if other_active_processes.exists():
                active_process = other_active_processes.first()
                raise forms.ValidationError(
                    f"Only one weighing process can be active at a time. "
                    f"Another process '{active_process.name}' is currently active. "
                    f"Please deactivate it first before activating this one."
                )
                
        return is_active


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name',
            'description',
            'erp_product_id',
            'is_active'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
            }),
            'description': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
            }),
            'erp_product_id': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 border-zinc-300 rounded focus:ring-blue-500'
            }),
        }
        
    def clean_is_active(self):
        is_active = self.cleaned_data.get('is_active')
        
        # If the product is being set to active, check for other active products
        if is_active:
            # Get the current instance ID (if it exists)
            instance_id = self.instance.id if self.instance and self.instance.pk else None
            
            # Check if there are any other active products
            other_active_products = Product.objects.filter(is_active=True)
            
            # Exclude the current instance if it exists
            if instance_id:
                other_active_products = other_active_products.exclude(id=instance_id)
            
            # If there are other active products, raise a validation error
            if other_active_products.exists():
                active_product = other_active_products.first()
                raise forms.ValidationError(
                    f"Only one product can be active at a time. "
                    f"Another product '{active_product.name}' is currently active. "
                    f"Please deactivate it first before activating this one."
                )
                
        return is_active


class DeliveryNoteForm(forms.ModelForm):
    class Meta:
        model = DeliveryNote
        fields = [
            'delivery_note_number',
            'created_by',
            'status',
            'is_synced',
            'last_sync_attempt',
            'sync_error_message',
            'notes'
        ]
    
    widgets = {
        'delivery_note_number': forms.TextInput(attrs={
            'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
        }),
        
        'status': forms.Select(attrs={
            'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
        }),
        
        'notes': forms.Textarea(attrs={
            'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 h-16'
        }),


    }
    
    
class CompanySettingsForm(forms.ModelForm):

    class Meta:
        model = CompanySettings
        fields = [
            'company_name',
            'erp_system',
            'api_key',
            'erp_username',
            'erp_password',
            'api_url',
            'is_active'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
            }),
            'erp_system': forms.Select(attrs={
                'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
            }),
            'api_key': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
            }),
            'erp_username': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
            }),
            'erp_password': forms.PasswordInput(attrs={
                'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
            }),
            'api_url': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-zinc-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 border-zinc-300 rounded focus:ring-blue-500'
            }),
        }
    
    
    
    
    