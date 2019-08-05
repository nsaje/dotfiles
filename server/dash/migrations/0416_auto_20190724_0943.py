# Generated by Django 2.1.8 on 2019-07-24 09:43

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("dash", "0415_auto_20190719_0755")]

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
                    ("ILS", "Israeli New Shekel"),
                    ("INR", "Indian Rupee"),
                    ("JPY", "Japanese Yen"),
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
                    ("ILS", "Israeli New Shekel"),
                    ("INR", "Indian Rupee"),
                    ("JPY", "Japanese Yen"),
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
                    ("ILS", "Israeli New Shekel"),
                    ("INR", "Indian Rupee"),
                    ("JPY", "Japanese Yen"),
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
                    ("ILS", "Israeli New Shekel"),
                    ("INR", "Indian Rupee"),
                    ("JPY", "Japanese Yen"),
                ],
                default="USD",
                max_length=3,
            ),
        ),
    ]