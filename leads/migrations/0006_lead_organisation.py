# Generated by Django 5.1.7 on 2025-03-12 12:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0005_alter_lead_agent'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='organisation',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, to='leads.userprofile'),
            preserve_default=False,
        ),
    ]
