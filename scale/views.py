from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from users.views import is_admin 
from .models import Scale, WeighingProcess, Product, DeliveryNote, WeighingRecord
from .forms import ScaleForm, WeighingProcessForm, ProductForm, DeliveryNoteForm
import serial
import serial.tools.list_ports
from django.utils import timezone
import json
from decimal import Decimal
from django.core.paginator import Paginator


# Scale Management Views
@login_required
@user_passes_test(is_admin)
def scale_list(request):
    scales = Scale.objects.all().order_by('name')
    return render(request, 'scale/scale_list.html', {'scales': scales})

@login_required
@user_passes_test(is_admin)
def scale_detail(request, pk):
    scale = get_object_or_404(Scale, pk=pk)
    return render(request, 'scale/scale_detail.html', {'scale': scale})

@login_required
@user_passes_test(is_admin)
def scale_create(request):
    if request.method == 'POST':
        form = ScaleForm(request.POST)
        if form.is_valid():
            scale = form.save()
            messages.success(request, f'Scale {scale.name} was created successfully.')
            return redirect('scale:scale_list')
    else:
        form = ScaleForm()
    
    return render(request, 'scale/scale_create.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def scale_edit(request, pk):
    scale = get_object_or_404(Scale, pk=pk)
    
    if request.method == 'POST':
        form = ScaleForm(request.POST, instance=scale)
        if form.is_valid():
            scale = form.save()
            messages.success(request, f'Scale {scale.name} was updated successfully.')
            return redirect('scale:scale_detail', pk=scale.pk)
    else:
        form = ScaleForm(instance=scale)
    
    return render(request, 'scale/scale_edit.html', {'form': form, 'scale': scale})

@login_required
@user_passes_test(is_admin)
def scale_delete(request, pk):
    scale = get_object_or_404(Scale, pk=pk)
    
    if request.method == 'POST':
        name = scale.name
        scale.delete()
        messages.success(request, f'Scale {name} was deleted successfully.')
        return redirect('scale:scale_list')
    
    # If not POST, redirect to detail page
    return redirect('scale:scale_detail', pk=pk)


@login_required
@user_passes_test(is_admin)
def connect_scale_view(request, scale_id):
    if request.method == 'POST':
        try:
            scale = get_object_or_404(Scale, pk=scale_id)
            success, message = connect_scale(scale)
            
            if success:
                # Update scale status
                scale.last_connection_status = "connected"
                scale.last_seen = timezone.now()
                scale.save()
                
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'status': scale.last_connection_status,
                    'last_seen': scale.last_seen.strftime('%Y-%m-%d %H:%M:%S')
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': message
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Only POST requests are allowed.'
    })


def connect_scale(scale):
    ser = None
    baud_rate = 9600  # Standard baud rate
    timeout = 2       # Connection timeout in seconds
    
    ports_to_try = []
    if scale.com_port:
        ports_to_try.append(scale.com_port)

    # Attempt to connect to the specified port first
    for port in ports_to_try:
        print(f"Attempting to connect to specified port: {port} for scale {scale.name}")
        try:
            ser = serial.Serial(port, baud_rate, timeout=timeout)
            if ser.is_open:
                print(f"Successfully opened port {port}. Trying to read data...")
                # Try a simple read to confirm responsiveness. Some scales send data on connect or CR.
                ser.write(b"\r\n") # Send a CR/LF, might elicit a response
                line = ser.readline()
                print(f"Read from {port}: {line.decode(errors='ignore').strip()}")
                ser.close()
                # If we successfully opened, (optionally read), and closed, consider it a success.
                # The `connect_scale_view` will update status and last_seen.
                # If the port was specified and worked, no need to change scale.com_port.
                return True, f"Successfully connected to {scale.name} on {port}."
        except serial.SerialException as e:
            print(f"SerialException on port {port} for scale {scale.name}: {str(e)}")
            if ser and ser.is_open:
                ser.close()
        except Exception as e:
            print(f"General Exception on port {port} for scale {scale.name}: {str(e)}")
            if ser and ser.is_open:
                ser.close()

    # If specified port failed or was not provided, attempt auto-detection
    print(f"Specified port connection failed or port not set for {scale.name}. Attempting auto-detection.")
    available_comports = serial.tools.list_ports.comports()
    print(f"Available COM ports for auto-detection: {[p.device for p in available_comports]}")

    for comport_info in available_comports:
        port_device = comport_info.device
        # Skip if this is the same as a specified port that already failed
        if scale.com_port and port_device == scale.com_port:
            continue

        # Check for common port name patterns
        if 'TTYUSB' in port_device.upper() or 'COM' in port_device.upper() or 'SERIAL' in port_device.upper():
            print(f"Auto-detect: Trying port {port_device} for scale {scale.name}")
            try:
                ser = serial.Serial(port_device, baud_rate, timeout=timeout)
                if ser.is_open:
                    print(f"Successfully opened auto-detected port {port_device}. Trying to read...")
                    ser.write(b"\r\n")
                    line = ser.readline()
                    print(f"Read from auto-detected {port_device}: {line.decode(errors='ignore').strip()}")
                    ser.close()
                    # Update the scale's com_port with the auto-detected one
                    scale.com_port = port_device 
                    print(f"Auto-detected working port {port_device} for {scale.name}. Scale's com_port updated.")
                    return True, f"Successfully connected to {scale.name} on {port_device} (auto-detected)."
            except serial.SerialException as e:
                print(f"Auto-detect: SerialException on {port_device} for {scale.name}: {str(e)}")
                if ser and ser.is_open:
                    ser.close()
            except Exception as e:
                print(f"Auto-detect: General Exception on {port_device} for {scale.name}: {str(e)}")
                if ser and ser.is_open:
                    ser.close()
                    
    return False, f"Could not connect to scale {scale.name}. No suitable COM port found or scale not responsive."







#################################################################################################
# Weighing Process Management Views
@login_required
@user_passes_test(is_admin)
def weighing_process_list(request):
    weighing_processes = WeighingProcess.objects.all().order_by('name')
    return render(request, 'scale/weighing_process_list.html', {'weighing_processes': weighing_processes})

@login_required
@user_passes_test(is_admin)
def weighing_process_detail(request, pk):
    weighing_process = get_object_or_404(WeighingProcess, pk=pk)
    return render(request, 'scale/weighing_process_detail.html', {'weighing_process': weighing_process})

@login_required
@user_passes_test(is_admin)
def weighing_process_create(request):
    if request.method == 'POST':
        form = WeighingProcessForm(request.POST)
        if form.is_valid():
            weighing_process = form.save()
            messages.success(request, f'Weighing process {weighing_process.name} was created successfully.')
            return redirect('scale:weighing_process_list')
    else:
        form = WeighingProcessForm()
    
    return render(request, 'scale/weighing_process_create.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def weighing_process_edit(request, pk):
    weighing_process = get_object_or_404(WeighingProcess, pk=pk)
    
    if request.method == 'POST':
        form = WeighingProcessForm(request.POST, instance=weighing_process)
        if form.is_valid():
            weighing_process = form.save()
            messages.success(request, f'Weighing process {weighing_process.name} was updated successfully.')
            return redirect('scale:weighing_process_detail', pk=weighing_process.pk)
    else:
        form = WeighingProcessForm(instance=weighing_process)
    
    return render(request, 'scale/weighing_process_edit.html', {'form': form, 'weighing_process': weighing_process})

@login_required
@user_passes_test(is_admin)
def weighing_process_delete(request, pk):
    weighing_process = get_object_or_404(WeighingProcess, pk=pk)
    
    if request.method == 'POST':
        name = weighing_process.name
        weighing_process.delete()
        messages.success(request, f'Weighing process {name} was deleted successfully.')
        return redirect('scale:weighing_process_list')
    
    # If not POST, redirect to detail page
    return redirect('scale:weighing_process_detail', pk=pk)


# Weighing Station Views
@login_required
@user_passes_test(is_admin)
def weighing_station(request):
    scales = Scale.objects.filter(is_active=True).order_by('name')
    products = Product.objects.filter(is_active=True).order_by('name')
    processes = WeighingProcess.objects.filter(is_active=True).order_by('name')
    delivery_notes = DeliveryNote.objects.all().order_by('-created_at')[:20]  # Get the 20 most recent delivery notes
    
    # Get custom fields data for all processes
    process_custom_fields = {}
    for process in processes:
        process_custom_fields[process.id] = process.custom_fields_schema
    
    if request.method == 'POST':
        try:
            # Extract form data
            scale_id = request.POST.get('scale_id')
            product_id = request.POST.get('product_id')
            process_id = request.POST.get('process_id')
            gross_weight = request.POST.get('gross_weight', '0')
            tare_weight = request.POST.get('tare_weight', '0')
            net_weight = request.POST.get('net_weight', '0')
            unit_of_measure = request.POST.get('unit_of_measure', 'kg')
            notes = request.POST.get('notes', '')
            barcode = request.POST.get('barcode', '')
            
            # Convert weights to Decimal, handling empty strings
            gross_weight = Decimal(gross_weight) if gross_weight and gross_weight.strip() else Decimal('0')
            tare_weight = Decimal(tare_weight) if tare_weight and tare_weight.strip() else Decimal('0')
            net_weight = Decimal(net_weight) if net_weight and net_weight.strip() else Decimal('0')
            
            # Extract custom fields
            custom_data = {}
            for key, value in request.POST.items():
                if key.startswith('custom_field_'):
                    field_name = key.replace('custom_field_', '')
                    custom_data[field_name] = value
            
            # Handle delivery note association
            add_to_delivery_note = request.POST.get('add_to_delivery_note') == 'on'
            delivery_note = None
            
            if add_to_delivery_note:
                note_option = request.POST.get('note_option')
                if note_option == 'existing':
                    delivery_note_id = request.POST.get('delivery_note_id')
                    if delivery_note_id:
                        delivery_note = get_object_or_404(DeliveryNote, pk=delivery_note_id)
                elif note_option == 'new':
                    delivery_note_number = request.POST.get('new_note_number')
                    note_status = request.POST.get('new_note_status', 'draft')
                    if delivery_note_number:
                        delivery_note = DeliveryNote.objects.create(
                            delivery_note_number=delivery_note_number,
                            created_by=request.user,
                            status=note_status
                        )
            
            # Create the weighing record
            weighing_record = WeighingRecord.objects.create(
                scale_id=scale_id,
                product_id=product_id,
                process_id=process_id,
                user=request.user,
                gross_weight=gross_weight,
                tare_weight=tare_weight,
                net_weight=net_weight,
                unit_of_measure=unit_of_measure,
                notes=notes,
                custom_data=custom_data,
                delivery_note=delivery_note,
                barcode=barcode
            )
            
            print_after_save = request.POST.get('print_after_save') == 'true'
            
            if print_after_save:
                # Update print count
                weighing_record.print_count += 1
                weighing_record.last_printed_at = timezone.now()
                weighing_record.save()
                
                # Add a message indicating that printing was triggered
                messages.success(request, 'Weighing record created and sent to printer.')
                
                # TODO: Implement actual printing functionality
                # This would typically involve generating a PDF and sending it to a printer
                # For now, just redirect to a print view or mock this functionality
            else:
                messages.success(request, 'Weighing record created successfully.')
                
            return redirect('scale:weighing_station')
            
        except Exception as e:
            messages.error(request, f'Error creating weighing record: {str(e)}')
    
    context = {
        'scales': scales,
        'products': products,
        'processes': processes,
        'delivery_notes': delivery_notes,
        'process_custom_fields': json.dumps(process_custom_fields)
    }
    
    return render(request, 'scale/weighing_station.html', context)


#################################################################################################
# Product Management Views
@login_required
@user_passes_test(is_admin)
def product_list(request):
    products = Product.objects.all().order_by('name')
    return render(request, 'scale/product_list.html', {'products': products})

@login_required
@user_passes_test(is_admin)
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'scale/product_detail.html', {'product': product})

@login_required
@user_passes_test(is_admin)
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product {product.name} was created successfully.')
            return redirect('scale:product_list')
    else:
        form = ProductForm()
    
    return render(request, 'scale/product_create.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product {product.name} was updated successfully.')
            return redirect('scale:product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'scale/product_edit.html', {'form': form, 'product': product})

@login_required
@user_passes_test(is_admin)
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'Product {name} was deleted successfully.')
        return redirect('scale:product_list')
    
    # If not POST, redirect to detail page
    return redirect('scale:product_detail', pk=pk)



#################################################################################################
# Delivery Note Management Views
@login_required
@user_passes_test(is_admin)
def delivery_note_list(request):
    delivery_notes = DeliveryNote.objects.all().order_by('delivery_note_number')
    return render(request, 'scale/delivery_note_list.html', {'delivery_notes': delivery_notes})

@login_required
@user_passes_test(is_admin)
def delivery_note_detail(request, pk):
    delivery_note = get_object_or_404(DeliveryNote, pk=pk)
    weighing_records = WeighingRecord.objects.filter(delivery_note=delivery_note).order_by('-timestamp')
    return render(request, 'scale/delivery_note_detail.html', {
        'delivery_note': delivery_note,
        'weighing_records': weighing_records
    })

@login_required
@user_passes_test(is_admin)
def delivery_note_create(request):
    if request.method == 'POST':
        form = DeliveryNoteForm(request.POST)
        if form.is_valid():
            delivery_note = form.save()
            messages.success(request, f'Delivery Note {delivery_note.delivery_note_number} was created successfully.')
            return redirect('scale:delivery_note_list')
    else:
        form = DeliveryNoteForm()
    
    return render(request, 'scale/delivery_note_create.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def delivery_note_edit(request, pk):
    delivery_note = get_object_or_404(DeliveryNote, pk=pk)
    
    if request.method == 'POST':
        form = DeliveryNoteForm(request.POST, instance=delivery_note)
        if form.is_valid():
            delivery_note = form.save()
            messages.success(request, f'Delivery Note {delivery_note.delivery_note_number} was updated successfully.')
            return redirect('scale:delivery_note_detail', pk=delivery_note.pk)
    else:
        form = DeliveryNoteForm(instance=delivery_note)
    
    return render(request, 'scale/delivery_note_edit.html', {'form': form, 'delivery_note': delivery_note})

@login_required
@user_passes_test(is_admin)
def delivery_note_delete(request, pk):
    delivery_note = get_object_or_404(DeliveryNote, pk=pk)
    
    if request.method == 'POST':
        name = delivery_note.delivery_note_number
        delivery_note.delete()
        messages.success(request, f'Delivery Note {name} was deleted successfully.')
        return redirect('scale:delivery_note_list')
    
    # If not POST, redirect to detail page
    return redirect('scale:delivery_note_detail', pk=pk)



#################################################################################################
# Weighing Record Management Views
@login_required
@user_passes_test(is_admin)
def weighing_record_list(request):
    # Get filter parameters from request
    scale_id = request.GET.get('scale')
    product_id = request.GET.get('product')
    process_id = request.GET.get('process')
    barcode = request.GET.get('barcode')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    sort_param = request.GET.get('sort', '-timestamp')  # Default sort by timestamp desc
    
    # Start with all records
    records = WeighingRecord.objects.all()
    
    # Apply filters if provided
    if scale_id:
        records = records.filter(scale_id=scale_id)
    
    if product_id:
        records = records.filter(product_id=product_id)
    
    if process_id:
        records = records.filter(process_id=process_id)
    
    if barcode:
        records = records.filter(barcode__icontains=barcode)
    
    # Date range filtering
    from django.utils.dateparse import parse_date
    from datetime import datetime, timedelta, time
    
    if date_from:
        date_from_obj = parse_date(date_from)
        if date_from_obj:
            date_from_datetime = datetime.combine(date_from_obj, time.min)
            records = records.filter(timestamp__gte=date_from_datetime)
    
    if date_to:
        date_to_obj = parse_date(date_to)
        if date_to_obj:
            date_to_datetime = datetime.combine(date_to_obj, time.max)
            records = records.filter(timestamp__lte=date_to_datetime)
    
    # Apply sorting
    if sort_param:
        records = records.order_by(sort_param)
    
    # Pagination
    paginator = Paginator(records, 10)  # Show 10 records per page
    page_number = request.GET.get('page', 1)
    records_page = paginator.get_page(page_number)
    
    # Get lists for filter dropdowns
    scales = Scale.objects.all().order_by('name')
    products = Product.objects.all().order_by('name')
    processes = WeighingProcess.objects.all().order_by('name')
    
    context = {
        'records': records_page,
        'scales': scales,
        'products': products,
        'processes': processes,
    }
    
    return render(request, 'scale/weighing_record_list.html', context)

@login_required
@user_passes_test(is_admin)
def weighing_record_detail(request, pk):
    record = get_object_or_404(WeighingRecord, pk=pk)
    return render(request, 'scale/weighing_record_detail.html', {'record': record})

@login_required
@user_passes_test(is_admin)
def print_weighing_record(request, pk):
    record = get_object_or_404(WeighingRecord, pk=pk)
    
    # Update print count
    record.print_count += 1
    record.last_printed_at = timezone.now()
    record.save()
    
    # For now, just redirect back to the detail page with a success message
    messages.success(request, f'Weighing record {pk} sent to printer.')
    return redirect('scale:weighing_record_detail', pk=record.pk)

@login_required
@user_passes_test(is_admin)
def weighing_record_edit(request, pk):
    record = get_object_or_404(WeighingRecord, pk=pk)
    
    if request.method == 'POST':
        # For now, handle basic fields manually since we don't have a form
        try:
            record.gross_weight = Decimal(request.POST.get('gross_weight', record.gross_weight))
            record.tare_weight = Decimal(request.POST.get('tare_weight', record.tare_weight))
            record.net_weight = Decimal(request.POST.get('net_weight', record.net_weight))
            record.unit_of_measure = request.POST.get('unit_of_measure', record.unit_of_measure)
            record.notes = request.POST.get('notes', record.notes)
            record.barcode = request.POST.get('barcode', record.barcode)
            
            # Handle delivery note association
            delivery_note_id = request.POST.get('delivery_note_id')
            if delivery_note_id:
                record.delivery_note = get_object_or_404(DeliveryNote, pk=delivery_note_id)
            elif 'remove_delivery_note' in request.POST:
                record.delivery_note = None
            
            record.save()
            messages.success(request, 'Weighing record updated successfully.')
            return redirect('scale:weighing_record_detail', pk=record.pk)
        except Exception as e:
            messages.error(request, f'Error updating record: {str(e)}')
    
    # For edit, we should create a form, but for now, just render a template with the record
    context = {
        'record': record,
        'delivery_notes': DeliveryNote.objects.all().order_by('-created_at'),
        'scales': Scale.objects.filter(is_active=True),
        'products': Product.objects.filter(is_active=True),
        'processes': WeighingProcess.objects.filter(is_active=True),
    }
    
    return render(request, 'scale/weighing_record_edit.html', context)

@login_required
@user_passes_test(is_admin)
def weighing_record_delete(request, pk):
    record = get_object_or_404(WeighingRecord, pk=pk)
    
    if request.method == 'POST':
        record_id = record.id
        record.delete()
        messages.success(request, f'Weighing record #{record_id} deleted successfully.')
        return redirect('scale:weighing_record_list')
    
    # If not POST, redirect to detail page
    return redirect('scale:weighing_record_detail', pk=pk)

@login_required
@user_passes_test(is_admin)
def export_weighing_records(request):
    # Get filter parameters from request (same as in weighing_record_list)
    scale_id = request.GET.get('scale')
    product_id = request.GET.get('product')
    process_id = request.GET.get('process')
    barcode = request.GET.get('barcode')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    sort_param = request.GET.get('sort', '-timestamp')
    export_format = request.GET.get('format', 'csv')
    
    # Start with all records
    records = WeighingRecord.objects.all()
    
    # Apply filters if provided
    if scale_id:
        records = records.filter(scale_id=scale_id)
    
    if product_id:
        records = records.filter(product_id=product_id)
    
    if process_id:
        records = records.filter(process_id=process_id)
    
    if barcode:
        records = records.filter(barcode__icontains=barcode)
    
    # Date range filtering
    from django.utils.dateparse import parse_date
    from datetime import datetime, timedelta, time
    
    if date_from:
        date_from_obj = parse_date(date_from)
        if date_from_obj:
            date_from_datetime = datetime.combine(date_from_obj, time.min)
            records = records.filter(timestamp__gte=date_from_datetime)
    
    if date_to:
        date_to_obj = parse_date(date_to)
        if date_to_obj:
            date_to_datetime = datetime.combine(date_to_obj, time.max)
            records = records.filter(timestamp__lte=date_to_datetime)
    
    # Apply sorting
    if sort_param:
        records = records.order_by(sort_param)
    
    # Process export based on format
    if export_format == 'csv':
        return export_records_to_csv(records)
    elif export_format == 'excel':
        return export_records_to_excel(records)
    elif export_format == 'pdf':
        return export_records_to_pdf(records)
    else:
        messages.error(request, f"Unsupported export format: {export_format}")
        return redirect('scale:weighing_record_list')

def export_records_to_csv(records):
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="weighing_records.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Timestamp', 'Barcode', 'Scale', 'Product', 'Process', 'Gross Weight', 
                    'Tare Weight', 'Net Weight', 'Unit', 'Recorded By', 'Notes', 'Delivery Note'])
    
    for record in records:
        writer.writerow([
            record.id,
            record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            record.barcode,
            record.scale.name,
            record.product.name,
            record.process.name,
            record.gross_weight,
            record.tare_weight,
            record.net_weight,
            record.unit_of_measure,
            f"{record.user.first_name} {record.user.last_name}",
            record.notes,
            record.delivery_note.delivery_note_number if record.delivery_note else ''
        ])
    
    return response

def export_records_to_excel(records):
    import xlwt
    from django.http import HttpResponse
    from datetime import datetime
    
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="weighing_records.xls"'
    
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Weighing Records')
    
    # Sheet header, first row
    row_num = 0
    
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    
    columns = ['ID', 'Timestamp', 'Barcode', 'Scale', 'Product', 'Process', 'Gross Weight', 
              'Tare Weight', 'Net Weight', 'Unit', 'Recorded By', 'Notes', 'Delivery Note']
    
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    
    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()
    
    for record in records:
        row_num += 1
        ws.write(row_num, 0, record.id, font_style)
        ws.write(row_num, 1, record.timestamp.strftime('%Y-%m-%d %H:%M:%S'), font_style)
        ws.write(row_num, 2, record.barcode, font_style)
        ws.write(row_num, 3, record.scale.name, font_style)
        ws.write(row_num, 4, record.product.name, font_style)
        ws.write(row_num, 5, record.process.name, font_style)
        ws.write(row_num, 6, float(record.gross_weight), font_style)
        ws.write(row_num, 7, float(record.tare_weight), font_style)
        ws.write(row_num, 8, float(record.net_weight), font_style)
        ws.write(row_num, 9, record.unit_of_measure, font_style)
        ws.write(row_num, 10, f"{record.user.first_name} {record.user.last_name}", font_style)
        ws.write(row_num, 11, record.notes, font_style)
        ws.write(row_num, 12, record.delivery_note.delivery_note_number if record.delivery_note else '', font_style)
    
    wb.save(response)
    return response

def export_records_to_pdf(records):
    from django.http import HttpResponse
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    from io import BytesIO
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []
    
    # Add title
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Weighing Records", styles['Title']))
    elements.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    
    # Table data
    data = [['ID', 'Timestamp', 'Barcode', 'Scale', 'Product', 'Process', 'Gross', 
            'Tare', 'Net', 'Unit', 'Recorded By', 'Delivery Note']]
    
    for record in records:
        data.append([
            str(record.id),
            record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            record.barcode,
            record.scale.name,
            record.product.name,
            record.process.name,
            str(record.gross_weight),
            str(record.tare_weight),
            str(record.net_weight),
            record.unit_of_measure,
            f"{record.user.first_name} {record.user.last_name}",
            record.delivery_note.delivery_note_number if record.delivery_note else ''
        ])
    
    # Create the table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    # Add the table to elements
    elements.append(table)
    
    # Build the PDF
    doc.build(elements)
    
    # Get the value of the buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create the HTTP response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="weighing_records.pdf"'
    response.write(pdf)
    
    return response