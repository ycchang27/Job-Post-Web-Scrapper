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


from jobs.models import Jobs

class MonsterCrawler:
    __TIMEOUT_SECONDS = 10
    __NO_RESPONSE_MAX = 3
    __JOB_BOARD_NAME = 'MONSTER'
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
        last_posted = 1
        search_url = self.create_search_url('Software Engineer', 'San Francisco, California', True, last_posted)
        print('Navigate to url: ' + search_url)
        self.__driver.get(search_url)
        
        # Extract all job post urls
        job_post_urls = self.extract_job_post_urls(search_url)
        
        # Add all jobs to db
        self.add_to_db(job_post_urls, last_posted)
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
            job_post = job_post.find_element_by_tag_name('a')
            job_urls.append(str(job_post.get_attribute('href')))
        print('Link extraction complete')
        return job_urls
    
    def add_to_db(self, job_post_urls: list, last_posted: int):
        '''
        Go to each link and store job data to database
        '''
        print('There are ' + str(len(job_post_urls)) + ' jobs')
        for url in job_post_urls:
            # Navigate to the url
            self.__driver.execute_script("window.open('');")
            self.__driver.switch_to_window(self.__driver.window_handles[1])
            self.__driver.get(url)
            self.sleep_between_three_to_five_seconds()

            # Extract job post
            title: str = self.__driver.find_element_by_xpath('//h1[@name="job_title"]').text
            company_name: str = self.__driver.find_element_by_xpath('//div[@name="job_company_name"]').text
            description: str = self.__driver.find_element_by_xpath('//div[@name="value_description"]/div').text
            location: str = self.__driver.find_element_by_xpath('//div[@name="job_company_location"]').text
            posted_date: str = ''
            
            try:
                posted_date = self.__driver.find_element_by_xpath('//div[@name="value_posted"]/div').text.replace(' ago', '')
            except:
                try:
                    posted_date = self.__driver.find_element_by_xpath('//div[@name="value_posted"]').text.replace(' ago', '')
                except:
                    print('Date not found')
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
            print('url='+url)
            print('title:'+title)
            print('location:'+location)
            print(('description:'+description).encode('unicode_escape'))
            print('posted_date:'+str(posted_date))
            print('company:'+company_name)
            print('job_board_site:'+self.__JOB_BOARD_NAME)
            print('-----------------------------------------------------')

            # Save to database
            try:
                Jobs.objects.create(
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

            # switch back to original tab
            self.__driver.close()
            self.__driver.switch_to.window(self.__driver.window_handles[0])
