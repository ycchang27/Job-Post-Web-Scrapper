from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from django.db.models import Q

from .models import Job

class HomePageView(TemplateView):
    template_name = 'index.html'

class SearchResultsView(ListView):
    model = Job
    template_name = 'search_results.html'
    
    def get_queryset(self):
        '''
        Runs raw query and returns result
        '''
        raw_query = self.request.GET.get('raw_query')
        return Job.objects.raw(raw_query)
