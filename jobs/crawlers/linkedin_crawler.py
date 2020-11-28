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
        self.__chrome_options.add_argument("--start-maximized")
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
        self.navigate_to_job_board()
        self.base_search()

        # Get all currently listed job urls
        job_posts = self.get_job_urls()

        # Navigate to each url and extract data
        print('There are ' + str(len(job_posts)) + ' jobs')
        job_index = 1
        for url in job_posts:
            # Navigate to the url
            url = 'https://www.linkedin.com/jobs/view/2291648589/?eBP=CwEAAAF2DRVmxjCJJXY4Xsgt6sqHX4ZsyvdBvvvZgvleCJ_ETb0qoTwsSvmyo0htP0yGo5y3tHtHqzaQG8LnT8ptBQdl9q42wqpwAY2C7qK4U8Xc9rhP0iA70a2fpGtD1o9OgvPCuE9hkEMnuz8QJWS0MzOpE394Bc839o_4rZHu43Tim6OFax3e7UWNdhKn03a1sThgJ1bH_O88qrW6QkQfPvQIuRVhbS5VdQhVa2JT-GLJm52JhrhmDX8tBsXcQTb0YmCqEeYBkph9B327MogumymwIDtTb06PONJv8A3mcbOIERfZnBD9ORKSkhrbDphLAVwFrvUmYAILodt19QNom94q9Jw2z8LmJH7iBjUL2lFjSShZMzxyI0prp7p3OGN53Rj6FQ&recommendedFlavor=ACTIVELY_HIRING_COMPANY&refId=gfZZMF3XmfCaTSQ9zdleOQ%3D%3D&trackingId=GZjecDxXN3KzHVN5y816KA%3D%3D&trk=flagship3_search_srp_jobs'
            self.__driver.execute_script("window.open('');")
            self.__driver.switch_to_window(self.__driver.window_handles[1])
            self.__driver.get(url)
            show_more_button = self.try_and_catch_find_webelements(
                lambda: WebDriverWait(self.__driver, self.__TIMEOUT_SECONDS) \
                    .until(EC.presence_of_element_located((By.XPATH , \
                    '//button[@aria-label="See more"]'))
                )
            )
            show_more_button.click()

            # Extract job post
            self.delay_by_2_to_3_seconds()
            entire_html: str = self.__driver.page_source.encode('unicode_escape')
            print(entire_html)
            break
            # title: str = self.try_and_catch_find_webelements(
            #     lambda: self.__driver.find_element_by_class_name('mt6 ml5 flex-grow-1')).find_element_by_tag_name('h1')
            # company_name: str = self.try_and_catch_find_webelements(
            #     lambda: self.__driver.find_element_by_class_name('jobs-top-card__company-url t-black ember-view')).text
            # description_list: WebElement = self.try_and_catch_find_webelements(
            #     lambda: self.__driver.find_element_by_class_name('jobs-box__html-content jobs-description-content__text t-14 t-normal'))
            # description_list.find_element_by_class_name('jobs-box__html-content jobs-description-content__text t-14 t-normal')
            # description_list = description_list.find_elements_by_tag_name('p')
            # description: str = ''
            # for description_tag in description_list:
            #     description + description_tag.text + '\n'

            # location: str = self.try_and_catch_find_webelements(
            #     lambda: self.__driver.find_element_by_class_name('jobs-top-card__bullet')).text
            # posted_date: str = self.try_and_catch_find_webelements(
            #     lambda: self.__driver.find_elements_by_class_name('topcard__flavor-row')) #job_header[1].text.split(' ago')[0]
            # posted_date.replace('Posted ', '')
            # posted_date.replace(' ago')
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
                # Jobs.objects.create(
                #     url=url,
                #     title=title,
                #     location=location,
                #     description=description,
                #     posted_date=posted_date,
                #     company_name=company_name,
                #     job_board_site=self.__JOB_BOARD_NAME
                # )
                print('job added')
            except Exception as e:
                print('Exception has occurred while trying to insert Job into the database: ', e)

            # switch back to original tab
            self.__driver.close()
            self.__driver.switch_to.window(self.__driver.window_handles[0])

            self.delay_by_2_to_3_seconds()
        self.__driver.close()
        print('Completed successfully')

    def navigate_to_job_board(self):
        '''
        Navigate to job board page. Go through any necessary steps (ex: login for authwall) to reach there
        '''
        self.__driver.get('https://www.linkedin.com/jobs/')
        self.delay_by_2_to_3_seconds()
        entire_html: str = self.__driver.page_source.encode('unicode_escape')
        print(entire_html)
        # Check for authwall. Signin if necessary
        username_xpath: str = ''
        password_xpath: str = ''
        login_submit_xpath: str = ''
        try:
            signin_link: WebElement = WebDriverWait(self.__driver, self.__TIMEOUT_SECONDS) \
                .until(EC.presence_of_element_located((By.XPATH , \
                '//a[@data-tracking-control-name="auth_wall_desktop_jserp-login-toggle"]'))
            )
            print('signing in with authwall')
            username_xpath = '//input[@class="login-email"]'
            password_xpath = '//input[@class="login-password"]'
            login_submit_xpath = '//input[@class="login submit-button"]'
            signin_link.click()
        except:
            print('signing in with other link')
            signin_link: WebElement = WebDriverWait(self.__driver, self.__TIMEOUT_SECONDS) \
                .until(EC.presence_of_element_located((By.XPATH , \
                '//a[@data-tracking-control-name="guest_homepage-jobseeker_nav-header-signin"]'))
            )
            username_xpath = '//input[@id="username"]'
            password_xpath = '//input[@id="password"]'
            login_submit_xpath = '//button[@aria-label="Sign in"]'
            signin_link.click()

        self.delay_by_2_to_3_seconds()
        self.login(username_xpath, password_xpath, login_submit_xpath)
        self.delay_by_2_to_3_seconds()
    
    def base_search(self):
        '''
        Search by job name and location only
        '''
        # Search jobs
        entire_html: str = self.__driver.page_source.encode('unicode_escape')
        print(entire_html)
        job_name_input: WebElement = self.try_and_catch_find_webelements(
            lambda: WebDriverWait(self.__driver, self.__TIMEOUT_SECONDS) \
                .until(EC.presence_of_element_located((By.XPATH , \
                '//div[@aria-label="Search by title, skill, or company"]/input'))
            )
        )
        job_name_input.clear()
        job_name_input.send_keys('Software Engineer')
        job_location_input: WebElement = self.try_and_catch_find_webelements(
            lambda: WebDriverWait(self.__driver, self.__TIMEOUT_SECONDS) \
                .until(EC.presence_of_element_located((By.XPATH , \
                '//div[@aria-label="City, state, or zip code"]/input'))
            )
        )
        job_location_input.clear()
        job_location_input.send_keys('United States')
        self.delay_by_2_to_3_seconds()
        job_location_input.send_keys(Keys.ENTER)
        self.delay_by_2_to_3_seconds()

    def login(self, username_xpath, password_xpath, login_submit_xpath):
        '''
        login to LinkedIn and go back to the job page
        '''
        username: WebElement = self.try_and_catch_find_webelements(
            lambda: WebDriverWait(self.__driver, self.__TIMEOUT_SECONDS) \
                .until(EC.presence_of_element_located((By.XPATH , \
                username_xpath))
            )
        )
        username.clear()
        username.send_keys(os.environ['FAKE_LINKEDIN_USERNAME'])
        password: WebElement = self.try_and_catch_find_webelements(
            lambda: WebDriverWait(self.__driver, self.__TIMEOUT_SECONDS) \
                .until(EC.presence_of_element_located((By.XPATH , \
                password_xpath))
            )
        )
        self.delay_by_2_to_3_seconds()
        password.clear()
        password.send_keys(os.environ['FAKE_LINKEDIN_PASSWORD'])
        signin_button: WebElement = self.try_and_catch_find_webelements(
            lambda: WebDriverWait(self.__driver, self.__TIMEOUT_SECONDS) \
                .until(EC.presence_of_element_located((By.XPATH , \
                login_submit_xpath))
            )
        )
        self.delay_by_2_to_3_seconds()
        signin_button.click()

        # Go back to the job search page
        time.sleep(5)
        self.__driver.get('https://www.linkedin.com/jobs/')
        self.delay_by_2_to_3_seconds()

    def get_job_urls(self):
        '''
        Get all job urls from the job board
        '''
        next_page:int = 2
        urls: list = []
        
        try:
            while(True):
                self.delay_by_2_to_3_seconds()
                print('Extracting page ' + str(next_page))
                self.delay_by_2_to_3_seconds()
                job_posts = self.try_and_catch_find_webelements(
                    lambda: self.__driver.find_elements_by_xpath('//ul[@class="jobs-search-results__list list-style-none"]/li')
                )

                # Traverse down "slowly" to properly retrieve job data
                for i in range(len(job_posts)):
                    id = job_posts[i].get_property('id')
                    job_post = self.try_and_catch_find_webelements(
                        lambda: self.__driver.find_element_by_xpath('//li[@id="' + id + '"]')
                    )
                    job_post.location_once_scrolled_into_view
                    self.delay_by_less_than_1_seconds()

                # Retrieve job urls
                job_posts = self.try_and_catch_find_webelements(
                    lambda: self.__driver.find_elements_by_xpath('//ul[@class="jobs-search-results__list list-style-none"]/li')
                )
                for job_post in job_posts:
                    a = job_post.find_element_by_tag_name('a')
                    url = a.get_attribute('href')
                    urls.append(url)
                print('Completed extracting page ' + str(next_page))

                # Move to next page
                next_page_button = self.__driver.find_element_by_xpath('//button[@aria-label="Page ' +  str(next_page) + '"]')
                next_page_button.click()
                next_page += 1
                break
        except NoSuchElementException:
            print('Job url extraction completed successfully')
        except Exception as e: 
            traceback.print_exc()
            print('Job url extraction failed')
        finally:
            return urls

    def delay_by_2_to_3_seconds(self):
        '''
        Sleep for a certain second in timeframe [2.0, 3.0] to avoid overloading requests
        '''
        time.sleep(random.randint(20, 30) / 10.0)

    def delay_by_less_than_1_seconds(self):
        '''
        Sleep for a certain second in timeframe [0.5, 0.99] to avoid overloading requests
        '''
        time.sleep(random.randint(50, 99) / 100.0)

    def try_and_catch_find_webelements(self, f):
        '''
        Calls the given WebElement(s) fetch function. Returns WebElement(s) if found. 
        If not, then it prints current html view and throws exception
        '''
        try:
            return f()
        except Exception as e: 
            print('Exception has occurred while trying to find the WebElement(s): ', e)
            traceback.print_exc()
            print('Print the current driver: ')
            print(self.__driver.page_source.encode('utf-8'))
            raise