from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from datetime import datetime, timedelta
import os
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
        self.__chrome_options.add_argument("--disable-dev-shm-usage")
        self.__driver = webdriver.Chrome(executable_path=os.environ['CHROMEDRIVER_PATH'], chrome_options=self.__chrome_options)
        self.__action = ActionChains(self.__driver)

    def scrape(self):
        '''
        Collects job posts from LinkedIn Jobs with preset configurations
        '''
        # Navigate to the job listings
        self.__driver.get('https://www.linkedin.com/jobs/search?keywords=Software%2BEngineer&location=California%2C%2BUnited%2BStates&trk=public_jobs_jobs-search-bar_search-submit&f_TP=1%2C2&f_SB2=3&f_JT=F&f_E=2%2C3&f_PP=106471299&redirect=false&position=1&pageNum=0')
        
        # Scroll down until you have "all results" (Show more jobs tend to "break" after around 900-1000 jobs)
        # last_height = self.__driver.execute_script('return document.body.scrollHeight')
        has_retried: bool = False
        no_response_count: int = 0
        while no_response_count <= self.__NO_RESPONSE_MAX:
            self.__driver.execute_script('window.scrollTo(0, 1000)')
            # new_height = self.__driver.execute_script('return document.body.scrollHeight')
            # last_height = new_height
            time.sleep(0.25)
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
        job_posts = self.__driver.find_elements_by_xpath('//ul[@class="jobs-search__results-list"]/li/a')

        # Navigate to each url and extract data
        for job_post in job_posts:
            # Navigate to the url
            url: str = job_post.get_attribute('href')
            self.__driver.execute_script("window.open('');")
            self.__driver.switch_to_window(self.__driver.window_handles[1])
            self.__driver.get(url)
            show_more_button = WebDriverWait(self.__driver, self.__TIMEOUT_SECONDS) \
                .until(EC.presence_of_element_located((By.XPATH , \
                '//button[@class="show-more-less-html__button show-more-less-html__button--more"]'))
            )
            show_more_button.click()

            # Extract job post
            title: str = self.__driver.find_element_by_class_name('topcard__title').text
            company_name: str = self.__driver.find_element_by_class_name('topcard__flavor').text
            description: str = self.__driver.find_element_by_class_name('show-more-less-html__markup').text

            job_header = self.__driver.find_elements_by_class_name('topcard__flavor-row')
            location: str = job_header[0].text.replace(company_name, '')
            posted_date: str = job_header[1].text.split(' ago')[0]
            if 'HOURS' in posted_date.upper():
                posted_date = datetime.now() - timedelta(hours=int(posted_date.split(' ')[0]))
            elif 'DAYS' in posted_date.upper():
                posted_date = datetime.now() - timedelta(days=int(posted_date.split(' ')[0]))
            
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
            pass

            # switch back to original tab
            self.__driver.close()
            self.__driver.switch_to.window(self.__driver.window_handles[0])