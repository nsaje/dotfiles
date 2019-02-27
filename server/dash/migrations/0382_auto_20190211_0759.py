# Generated by Django 2.1.2 on 2019-02-11 07:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("dash", "0381_adgroupsettings_language_targeting_enabled")]

    operations = [
        migrations.AlterField(
            model_name="account",
            name="currency",
            field=models.CharField(
                choices=[
                    ("USD", "US Dollar"),
                    ("EUR", "Euro"),
                    ("GBP", "British Pound"),
                    ("AUD", "Australian Dollar"),
                    ("SGD", "Singapore Dollar"),
                    ("BRL", "Brazilian Real"),
                    ("MYR", "Malaysian Ringgit"),
                    ("CHF", "Swiss Franc"),
                    ("ZAR", "South African Rand"),
                ],
                default="USD",
                max_length=3,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="creditlineitem",
            name="currency",
            field=models.CharField(
                choices=[
                    ("USD", "US Dollar"),
                    ("EUR", "Euro"),
                    ("GBP", "British Pound"),
                    ("AUD", "Australian Dollar"),
                    ("SGD", "Singapore Dollar"),
                    ("BRL", "Brazilian Real"),
                    ("MYR", "Malaysian Ringgit"),
                    ("CHF", "Swiss Franc"),
                    ("ZAR", "South African Rand"),
                ],
                default="USD",
                max_length=3,
            ),
        ),
        migrations.AlterField(
            model_name="currencyexchangerate",
            name="currency",
            field=models.CharField(
                choices=[
                    ("USD", "US Dollar"),
                    ("EUR", "Euro"),
                    ("GBP", "British Pound"),
                    ("AUD", "Australian Dollar"),
                    ("SGD", "Singapore Dollar"),
                    ("BRL", "Brazilian Real"),
                    ("MYR", "Malaysian Ringgit"),
                    ("CHF", "Swiss Franc"),
                    ("ZAR", "South African Rand"),
                ],
                max_length=3,
            ),
        ),
        migrations.AlterField(
            model_name="yahooaccount",
            name="currency",
            field=models.CharField(
                choices=[
                    ("USD", "US Dollar"),
                    ("EUR", "Euro"),
                    ("GBP", "British Pound"),
                    ("AUD", "Australian Dollar"),
                    ("SGD", "Singapore Dollar"),
                    ("BRL", "Brazilian Real"),
                    ("MYR", "Malaysian Ringgit"),
                    ("CHF", "Swiss Franc"),
                    ("ZAR", "South African Rand"),
                ],
                default="USD",
                max_length=3,
            ),
        ),
    ]