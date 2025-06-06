# Generated by Django 5.2.1 on 2025-05-20 13:12

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scale', '0003_alter_product_erp_product_id'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DeliveryNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('delivery_note_number', models.CharField(blank=True, max_length=100)),
                ('status', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_synced', models.BooleanField(default=False)),
                ('last_sync_attempt', models.DateTimeField(blank=True, null=True)),
                ('sync_error_message', models.TextField(blank=True)),
                ('notes', models.TextField(blank=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='weighingrecord',
            name='delivery_note',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='scale.deliverynote'),
        ),
    ]
