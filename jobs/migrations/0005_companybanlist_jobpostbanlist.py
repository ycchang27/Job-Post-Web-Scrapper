# Generated by Django 3.1.2 on 2021-05-07 04:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0004_auto_20210430_2018'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyBanList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(max_length=250, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='JobPostBanList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.CharField(max_length=250, unique=True)),
            ],
        ),
    ]
