# Generated by Django 3.1.2 on 2020-11-15 23:37

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Jobs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.CharField(max_length=250, unique=True)),
                ('title', models.CharField(max_length=250)),
                ('location', models.CharField(max_length=250)),
                ('description', models.TextField()),
                ('posted_date', models.DateField()),
                ('company_name', models.CharField(max_length=250)),
                ('job_board_site', models.CharField(max_length=250)),
            ],
        ),
    ]
