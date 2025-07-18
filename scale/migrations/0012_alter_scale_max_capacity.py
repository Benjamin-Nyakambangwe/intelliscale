# Generated by Django 5.2.1 on 2025-07-15 08:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scale', '0011_alter_scale_com_port'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scale',
            name='max_capacity',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Maximum weight capacity in kg', max_digits=10, null=True),
        ),
    ]
