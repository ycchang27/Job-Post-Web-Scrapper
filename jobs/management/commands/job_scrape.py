from django.core.management.base import BaseCommand

from jobs.crawlers.linkedin_crawler import LinkedInCrawler

class Command(BaseCommand):
    help = 'collect job posts from job boards posted within 7 days with preset criteria'

    def handle(self, *args, **options):
        '''
        Collects job posts from job boards posted within 7 days with preset criteria
        '''
        linkedin_crawler = LinkedInCrawler()
        linkedin_crawler.scrape()
