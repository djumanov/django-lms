# Generated by Django 4.1.6 on 2023-02-01 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coursemanagement', '0002_coursesetting'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courseoffer',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='coursesetting',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]