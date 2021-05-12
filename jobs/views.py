from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect

from .models import Job, CompanyBanList, JobPostBanList

import re

class HomePageView(TemplateView):
    template_name = 'index.html'

class SearchResultsView(ListView):
    model = Job
    template_name = 'search_results.html'
    
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        '''
        Runs raw query and returns result
        '''
        raw_query: str = self.request.GET.get('raw_query')
        return Job.objects.raw(raw_query)

    def post(self, request):
        '''
        Handles buttons in search result page
        '''
        if 'ban_company' in request.POST:
            banned_company_name = request.POST.get('company_name')
            CompanyBanList.objects.get_or_create(company_name=banned_company_name)
            Job.objects.filter(company_name=banned_company_name).delete()
            return redirect('/search/?raw_query=' + request.GET.get('raw_query'))
        elif 'delete_job_post' in request.POST:
            delete_url = request.POST.get('url')
            Job.objects.filter(url=delete_url).delete()
        elif 'ban_job_post' in request.POST:
            ban_url = request.POST.get('url')
            JobPostBanList.objects.get_or_create(url=ban_url)
            Job.objects.filter(url=ban_url).delete()
        else:
            return

        return redirect('/search/?raw_query=' + request.GET.get('raw_query'))
