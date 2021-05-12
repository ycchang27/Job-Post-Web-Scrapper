from django.contrib import admin

from jobs.models import Job, CompanyBanList, JobPostBanList

admin.site.register(Job)
admin.site.register(CompanyBanList)
admin.site.register(JobPostBanList)