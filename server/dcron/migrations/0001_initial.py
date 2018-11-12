# Generated by Django 2.1.2 on 2018-11-05 10:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DCronJob",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("command_name", models.CharField(max_length=150, unique=True)),
                ("executed_dt", models.DateTimeField(blank=True, null=True)),
                ("completed_dt", models.DateTimeField(blank=True, null=True)),
                ("host", models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={"verbose_name": "Distributed Cron Job", "verbose_name_plural": "Distributed Cron Jobs"},
        ),
        migrations.CreateModel(
            name="DCronJobSettings",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("schedule", models.CharField(max_length=250)),
                ("full_command", models.CharField(max_length=250)),
                ("enabled", models.BooleanField(default=True)),
                ("warning_wait", models.FloatField()),
                ("manual_warning_wait", models.BooleanField(default=False)),
                ("job", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to="dcron.DCronJob")),
            ],
            options={
                "verbose_name": "Distributed Cron Job Settings",
                "verbose_name_plural": "Distributed Cron Job Settings",
            },
        ),
    ]