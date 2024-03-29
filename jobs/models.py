from django.db import models

class Job(models.Model):
    url = models.CharField(max_length=250, unique=True)
    title = models.CharField(max_length=250)
    location = models.CharField(max_length=250)
    description = models.TextField()
    posted_date = models.DateField()
    company_name = models.CharField(max_length=250)
    job_board_site = models.CharField(max_length=250)

    class Meta:
        # table name
        db_table = 'job'

class JobPostBanList(models.Model):
    url = models.CharField(max_length=250, unique=True)

class CompanyBanList(models.Model):
    company_name = models.CharField(max_length=250, unique=True)

