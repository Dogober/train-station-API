# Generated by Django 5.1.6 on 2025-02-21 21:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('station', '0002_alter_route_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='crew',
            name='position',
            field=models.CharField(default='staff', max_length=255),
        ),
    ]
