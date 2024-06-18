# Generated by Django 4.2.10 on 2024-06-18 09:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geomanager', '0050_geomanagersettings_contact_us_page'),
    ]

    operations = [
        migrations.AddField(
            model_name='rasterstyle',
            name='rendering_engine',
            field=models.CharField(choices=[('large_image', 'Default'), ('magics', 'ECMWF Magics')], default='large_image', max_length=100, verbose_name='Rendering Engine'),
        ),
    ]