from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains 
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup

from datetime import datetime, timedelta
import os
import random
import re
import sys
import time
import traceback


from jobs.models import Job

class MonsterCrawler:
    __TIMEOUT_SECONDS = 10
    __NO_RESPONSE_MAX = 3
    __JOB_BOARD_NAME = 'MONSTER'
    __JOB_NOT_FOUND_MESSAGE = 'Sorry, we didn\'t find any jobs matching your criteria'
    def __init__(self):
        self.__chrome_options = webdriver.ChromeOptions()
        self.__chrome_options.binary_location = os.environ['GOOGLE_CHROME_BIN']
        self.__chrome_options.add_argument('--disable-gpu')
        self.__chrome_options.add_argument('--no-sandbox')
        self.__chrome_options.add_argument('--headless')
        self.__chrome_options.add_argument("--start-maximized")
        self.__chrome_options.add_argument('--disable-dev-shm-usage')
        self.__chrome_options.add_argument('--incognito')
        self.__chrome_options.add_argument('--disable-extensions')
        self.__chrome_options.add_argument('--version')
        self.__chrome_options.add_argument('--disable-web-security')
        self.__chrome_options.add_experimental_option('useAutomationExtension', False)
        self.__driver = webdriver.Chrome(executable_path=os.environ['CHROMEDRIVER_PATH'], chrome_options=self.__chrome_options)
        self.__action = ActionChains(self.__driver)
        self.__wait = WebDriverWait(self.__driver, self.__TIMEOUT_SECONDS)
        print('Using driver: ' + self.__driver.execute_script("return navigator.userAgent"))

    def scrape(self):
        '''
        Collects job posts from Monster Jobs with preset configurations
        '''
        # Navigate to the job listings
        last_posted_days = int(os.environ['MONSTER_LAST_DAYS_POSTED'])
        job_names = os.environ['MONSTER_JOBS'].split(os.environ['MONSTER_DELIMITER'])
        job_locations = os.environ['MONSTER_LOCATION'].split(os.environ['MONSTER_DELIMITER'])
        print('Search based on the following:')
        print('\tJob names: ' + str(job_names))
        print('\tJob locations: ' + str(job_locations))
        print('\tJob posted ' + str(last_posted_days) + ' days ago')
        job_post_urls: list = []
        for job_location in job_locations:
            for job_name in job_names:
                search_url = self.create_search_url(job_name, job_location, True, last_posted_days)
                print('Navigate to this search url: ' + search_url)
                self.__driver.get(search_url)
                job_post_urls.extend(self.extract_job_post_urls(search_url))
        
        # Extract all job post urls
        job_post_urls = self.remove_duplicate_urls(job_post_urls)
        
        # Add all jobs to db
        self.add_to_db(job_post_urls, last_posted_days)
        self.__driver.close()
        print('Scraping for Monster is complete')

    def sleep_less_than_one_second(self):
        '''
        Sleeps between 0.5 to 0.99 seconds
        '''
        time.sleep(random.randint(50, 99) / 100.0)

    def sleep_between_two_to_three_seconds(self):
        '''
        Sleeps between 2 to 3 seconds
        '''
        time.sleep(random.randint(20, 30) / 10.0)

    def sleep_between_three_to_five_seconds(self):
        '''
        Sleeps between 3 to 5 seconds
        '''
        time.sleep(random.randint(30, 50) / 10.0)

    def create_search_url(self, job_name: str, location: str, is_fulltime: bool, last_posted: int):
        '''
        Returns Monster job search url with given job name, location, full-time/part-time, last posted (in days)
        '''
        job_name = job_name.replace(' ', '-')
        location = location.replace(' ', '-')
        job_type = ''
        if is_fulltime:
            job_type = 'Full-Time_8'
        else:
            job_type = 'Part-Time_8'
        return 'https://www.monster.com/jobs/search/' + job_type + '?q=' + job_name \
            + '&where=' + location +'&tm=' + str(last_posted)

    def go_to_next_page(self, url: str, next_page: int):
        '''
        Manually go to 2nd page url of job board since "Load more jobs" button is not found
        '''
        next_page_url = url + '&stpage=1&page=' + str(next_page)
        print('Navigate to url: ' + next_page_url)
        self.__driver.get(next_page_url)
    
    def extract_job_post_urls(self, url):
        '''
        Extract job post urls in the job board
        '''
        # Scroll down until all jobs are found
        try:
            job_not_found = self.__driver.find_element_by_xpath('//header[@class="title"]/h1')
            if job_not_found.text == self.__JOB_NOT_FOUND_MESSAGE:
                print('Jobs not found. Don\'t extract urls for this search category.')
                return []
            print('Jobs found. Continue extracting urls.')
        except Exception as e:
            print('e')
        current_page: int = 1
        while True:
            print('Currently in page: ' + str(current_page))
            last_job_post = self.__driver.find_elements_by_xpath('//section/div[@class="flex-row"]')
            last_job_post[len(last_job_post) - 1].location_once_scrolled_into_view
            self.sleep_less_than_one_second()
            try:
                load_more_jobs = WebDriverWait(self.__driver, self.__TIMEOUT_SECONDS) \
                    .until(EC.presence_of_element_located((By.XPATH , \
                    '//a[@id="loadMoreJobs"]'))
                )
                current_page += 1
                self.go_to_next_page(url, current_page)
            except TimeoutException:
                print('timed out - loadMoreJobs')
                break
            finally:
                self.sleep_between_three_to_five_seconds()

        # Extract urls
        job_urls = []
        job_posts = self.__driver.find_elements_by_xpath('//section/div[@class="flex-row"]')
        for job_post in job_posts:
            try:
                job_post = job_post.find_element_by_tag_name('a')
                job_urls.append(str(job_post.get_attribute('href')))
            except:
                print('Url doesn\'t exist for this div: ' + str(job_post.get_attribute('innerHTML')))
        print('Link extraction complete. Extracted ' + str(len(job_urls)) + ' urls')
        self.sleep_between_three_to_five_seconds()
        return job_urls
    
    def add_to_db(self, job_post_urls: list, last_posted: int):
        '''
        Go to each link and store job data to database
        '''
        for url in job_post_urls:
            # Navigate to the url
            self.__driver.get(url)
            self.sleep_between_three_to_five_seconds()

            # Extract job post
            try:
                title: str = self.__driver.find_element_by_xpath('//h1[@name="job_title"]').text
                company_name: str = self.__driver.find_element_by_xpath('//div[@name="job_company_name"]').text
                description: str = self.__driver.find_element_by_xpath('//div[@name="value_description"]/div').text
                location: str = self.__driver.find_element_by_xpath('//div[@name="job_company_location"]').text
            except:
                print('Job info extraction failed (probably job not found): ' + url)
                continue
            posted_date: str = ''    
            try:
                posted_date = self.__driver.find_element_by_xpath('//div[@name="value_posted"]/div').text.replace(' ago', '')
            except:
                try:
                    posted_date = self.__driver.find_element_by_xpath('//div[@name="value_posted"]').text.replace(' ago', '')
                except:
                    print('Date not found for url: ' + url)
                    raise

            # format date
            if 'TODAY' in posted_date.upper() or 'TODAY' in posted_date.upper():
                posted_date = datetime.now()
            elif 'HOURS' in posted_date.upper() or 'HOUR' in posted_date.upper():
                posted_date = datetime.now() - timedelta(hours=int(posted_date.split(' ')[0]))
            elif 'DAYS' in posted_date.upper() or 'DAY' in posted_date.upper():
                posted_date = posted_date.replace('+', '')
                posted_date = datetime.now() - timedelta(days=int(posted_date.split(' ')[0]))
            elif 'WEEKS' in posted_date.upper() or 'WEEK' in posted_date.upper():
                posted_date = datetime.now() - timedelta(days=7 * int(posted_date.split(' ')[0]))
            elif 'MONTHS' in posted_date.upper() or 'MONTH' in posted_date.upper():
                posted_date = datetime.now() - timedelta(days=30 * int(posted_date.split(' ')[0]))
            elif 'YEAR' in posted_date.upper() or 'YEARS' in posted_date.upper():
                continue # too old
            else:
                posted_date = datetime.now() # too small to subtract
            if last_posted == 0:
                last_posted = 1
            posted_date = posted_date.date()
            if posted_date < datetime.now().date() - timedelta(days=last_posted):
                print('date too older than ' + str(last_posted) + ' day(s): ' + str(posted_date))
                continue

            # Display data
            print('-----------------------------------------------------')
            print('url:'+url)
            print(('title:'+title).encode('unicode_escape'))
            print(('location:'+location).encode('unicode_escape'))
            print(('description:'+description).encode('unicode_escape'))
            print('posted_date:'+str(posted_date))
            print(('company:'+company_name).encode('unicode_escape'))
            print('job_board_site:'+self.__JOB_BOARD_NAME)
            print('-----------------------------------------------------')

            # Save to database
            try:
                Job.objects.get_or_create(
                    url=url,
                    title=title,
                    location=location,
                    description=description,
                    posted_date=posted_date,
                    company_name=company_name,
                    job_board_site=self.__JOB_BOARD_NAME
                )
                print('job added')
            except Exception as e: 
                print(e)

    def remove_duplicate_urls(self, urls: list):
        '''
        Remove urls that already exist in the database
        '''
        existing_urls = list(Job.objects.values_list('url', flat=True))
        urls_to_insert_to_db = list(set(urls) - set(existing_urls))
        print('Removed duplicates. There are ' + str(len(urls_to_insert_to_db)) + ' urls to be added to database')
        return urls_to_insert_to_db
