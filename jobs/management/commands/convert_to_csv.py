from django.core.management.base import BaseCommand

import csv
import os

from jobs.models import Job
from jobs.configuration.config import App

class Command(BaseCommand):
    help = 'converts database to csv file'

    def handle(self, *args, **options):
        '''
        Converts database to csv file
        '''
        path = App.config()['APP']['CSV_DIRECTORY']
        if not os.path.exists(path):
            '''
            CSV storage folder doesn't exist, make it!
            '''
            os.mkdir(path)
        
        filename = "jobs.csv"
        filepath = os.path.join(path, filename)
        job_data = Job.objects.values().all().iterator()
        rows_done = 0
        fields = [f.name for f in Job._meta.get_fields()]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as my_file:
            writer = csv.DictWriter(my_file, fieldnames=fields)
            writer.writeheader()
            for data_item in job_data:
                row = {}
                for field in fields:
                    if str(field) == 'description':
                        row[str(field)] = str(data_item[field]).encode('unicode_escape')
                    else:
                        row[str(field)] = str(data_item[field])
                writer.writerow(row)
                rows_done += 1
        print("{} rows completed".format(rows_done))