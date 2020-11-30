from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from django.db.models import Q

from .models import Jobs

class HomePageView(TemplateView):
    template_name = 'index.html'

class SearchResultsView(ListView):
    model = Jobs
    template_name = 'search_results.html'
    
    def get_queryset(self):
        # Get the queries
        title_include_query = self.request.GET.get('title_include_query')
        title_exclude_query = self.request.GET.get('title_exclude_query')

        location_include_query = self.request.GET.get('location_include_query')
        location_exclude_query = self.request.GET.get('location_exclude_query')

        description_include_query = self.request.GET.get('description_include_query')
        description_exclude_query = self.request.GET.get('description_exclude_query')

        company_name_include_query = self.request.GET.get('company_name_include_query')
        company_name_exclude_query = self.request.GET.get('company_name_exclude_query')

        # Filter accordingly
        job_list = Jobs.objects.filter(
            Q(title__icontains=title_include_query) 
            & Q(location__icontains=location_include_query)
            & Q(description__icontains=description_include_query)
            & Q(company_name__icontains=company_name_include_query)
        )
        if title_exclude_query != '':
            job_list = job_list.exclude(Q(title__icontains=title_exclude_query))
        if location_exclude_query != '':
            job_list = job_list.exclude(Q(location__icontains=location_exclude_query))
        if description_exclude_query != '':
            job_list = job_list.exclude(Q(description__icontains=description_exclude_query))
        if company_name_exclude_query != '':
            job_list = job_list.exclude(Q(company_name__icontains=company_name_exclude_query))
        return job_list