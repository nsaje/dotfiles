# Generated by Django 2.1.11 on 2020-03-18 14:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0456_auto_20200310_1818'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentadcandidate',
            name='state',
            field=models.IntegerField(choices=[(1, 'Enabled'), (2, 'Paused')], default=1, null=True),
        ),
    ]