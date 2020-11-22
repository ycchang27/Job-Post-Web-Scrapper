from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains 
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


from datetime import datetime, timedelta
import os
import random
import re
import sys
import time

from jobs.models import Jobs

class LinkedInCrawler:
    __TIMEOUT_SECONDS = 10
    __NO_RESPONSE_MAX = 50
    __JOB_BOARD_NAME = 'LINKEDIN'
    def __init__(self):
        self.__chrome_options = webdriver.ChromeOptions()
        self.__chrome_options.binary_location = os.environ['GOOGLE_CHROME_BIN']
        self.__chrome_options.add_argument('--disable-gpu')
        self.__chrome_options.add_argument('--no-sandbox')
        self.__chrome_options.add_argument('--headless')
        self.__chrome_options.add_argument('--disable-dev-shm-usage')
        self.__chrome_options.add_argument('--incognito')
        self.__chrome_options.add_argument('--disable-extensions')
        self.__chrome_options.add_argument('--version')
        self.__driver = webdriver.Chrome(executable_path=os.environ['CHROMEDRIVER_PATH'], chrome_options=self.__chrome_options)
        self.__action = ActionChains(self.__driver)
        print('Using driver: ' + self.__driver.execute_script("return navigator.userAgent"))


    def scrape(self):
        '''
        Collects job posts from LinkedIn Jobs with preset configurations
        '''
        # Navigate to the job listings
        self.__driver.get('https://www.linkedin.com/jobs/')
        self.delay_by_random_seconds()
        job_name_input: WebElement = self.try_and_catch_find_webelements(
            lambda: WebDriverWait(self.__driver, self.__TIMEOUT_SECONDS) \
                .until(EC.presence_of_element_located((By.XPATH , \
                '//input[@aria-label="Search job titles or companies"]'))
            )
        )
        job_name_input.clear()
        job_name_input.send_keys('Software Engineer')
        job_location_input: WebElement = self.try_and_catch_find_webelements(
            lambda: WebDriverWait(self.__driver, self.__TIMEOUT_SECONDS) \
                .until(EC.presence_of_element_located((By.XPATH , \
                '//input[@aria-label="Location"]'))
            )
        )
        job_location_input.clear()
        job_location_input.send_keys('Portland, Oregon, United States')
        job_location_input.send_keys(Keys.ENTER)

        # Scroll down until you have "all results" (Show more jobs tend to "break" after around 900-1000 jobs)
        last_height = self.__driver.execute_script('return document.body.scrollHeight')
        has_retried: bool = False
        no_response_count: int = 0
        while no_response_count <= self.__NO_RESPONSE_MAX:
            self.__driver.execute_script('window.scrollTo(0, ' + str(last_height) + ')')
            new_height = self.__driver.execute_script('return document.body.scrollHeight')
            last_height = new_height
            self.delay_by_random_seconds()
            try:
                see_more_jobs = WebDriverWait(self.__driver, self.__TIMEOUT_SECONDS) \
                    .until(EC.presence_of_element_located((By.CSS_SELECTOR , \
                    '.infinite-scroller__show-more-button.infinite-scroller__show-more-button'))
                )
                if see_more_jobs.is_displayed() and see_more_jobs.is_enabled():
                    if has_retried:
                        no_response_count = 0
                        has_retried = False
                    else:
                        no_response_count += 1
                    retry_count = 0
                    see_more_jobs.click()
                else:
                    has_retried = True
                    no_response_count += 1
            except NoSuchElementException:
                print('no such element found - please fix the css')
                no_response_count += 1
            except TimeoutException:
                print('timed out - please look into this')
                no_response_count += 1

        # Get all currently listed job urls
        job_posts = self.try_and_catch_find_webelements(
            lambda: self.__driver.find_elements_by_xpath('//ul[@class="jobs-search__results-list"]/li/a')
        )

        # Navigate to each url and extract data
        print('There are ' + str(len(job_posts)) + ' jobs')
        job_index = 1
        for job_post in job_posts:
            # Navigate to the url
            url: str = job_post.get_attribute('href')
            self.__driver.execute_script("window.open('');")
            self.__driver.switch_to_window(self.__driver.window_handles[1])
            self.__driver.get(url)
            show_more_button = self.try_and_catch_find_webelements(
                lambda: WebDriverWait(self.__driver, self.__TIMEOUT_SECONDS) \
                    .until(EC.presence_of_element_located((By.XPATH , \
                    '//button[@class="show-more-less-html__button show-more-less-html__button--more"]'))
                )
            )
            show_more_button.click()

            # Extract job post
            title: str = self.try_and_catch_find_webelements(lambda: self.__driver.find_element_by_class_name('topcard__title')).text
            company_name: str = self.try_and_catch_find_webelements(lambda: self.__driver.find_element_by_class_name('topcard__flavor')).text
            description: str = self.try_and_catch_find_webelements(lambda: self.__driver.find_element_by_class_name('show-more-less-html__markup')).text

            job_header = self.try_and_catch_find_webelements(lambda: self.__driver.find_elements_by_class_name('topcard__flavor-row'))
            location: str = job_header[0].text.replace(company_name, '')
            posted_date: str = job_header[1].text.split(' ago')[0]
            if 'HOURS' in posted_date.upper() or 'HOUR' in posted_date.upper():
                posted_date = datetime.now() - timedelta(hours=int(posted_date.split(' ')[0]))
            elif 'DAYS' in posted_date.upper() or 'DAY' in posted_date.upper():
                posted_date = datetime.now() - timedelta(days=int(posted_date.split(' ')[0]))
            elif 'WEEKS' in posted_date.upper() or 'WEEK' in posted_date.upper():
                posted_date = datetime.now() - timedelta(days=7 * int(posted_date.split(' ')[0]))
            elif 'MONTHS' in posted_date.upper() or 'MONTH' in posted_date.upper():
                posted_date = datetime.now() - timedelta(days=30 * int(posted_date.split(' ')[0]))
            elif 'YEAR' in posted_date.upper() or 'YEARS' in posted_date.upper():
                continue # too old
            else:
                posted_date = datetime.now() # too small to subtract

            # Display data
            print('-----------------------------------------------------')
            print('job # ' + str(job_index))
            print('url='+url)
            print('title:'+title)
            print('location:'+location)
            print(('description:'+description).encode('unicode_escape'))
            print('posted_date:'+str(posted_date))
            print('company:'+company_name)
            print('job_board_site:'+self.__JOB_BOARD_NAME)
            print('-----------------------------------------------------')
            job_index += 1

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
                print('Exception has occurred while trying to insert Job into the database: ', e)

            # switch back to original tab
            self.__driver.close()
            self.__driver.switch_to.window(self.__driver.window_handles[0])

            self.delay_by_random_seconds()
        self.__driver.close()

    def delay_by_random_seconds(self):
        '''
        Sleep for a certain second in timeframe [0.5, 1] to avoid overloading requests
        '''
        time.sleep(random.randint(5, 10) / 10.0)

    def try_and_catch_find_webelements(self, f):
        '''
        Calls the given WebElement(s) fetch function. Returns WebElement(s) if found. 
        If not, then it prints current html view and throws exception
        '''
        try:
            return f()
        except Exception as e: 
            print('Exception has occurred while trying to find the WebElement(s): ', e)
            print('Print the current driver: ')
            print(self.__driver.page_source.encode('utf-8'))
            raise