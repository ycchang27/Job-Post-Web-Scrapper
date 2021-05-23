from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains 
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from django.db.models import Q

from datetime import datetime, timedelta
import random
import time

from jobs.models import Job, CompanyBanList, JobPostBanList
from jobs.configuration.config import App

class LinkedInCrawler:
    __TIMEOUT_SECONDS = 10
    __NO_RESPONSE_MAX = 20
    __JOB_BOARD_NAME = 'LINKEDIN'
    def __init__(self):
        chrome_bin_path: str = App.config()['APP']['GOOGLE_CHROME_BIN']
        chrome_driver_path: str = App.config()['APP']['CHROMEDRIVER_PATH']
        self.__chrome_options = webdriver.ChromeOptions()
        self.__chrome_options.binary_location = chrome_bin_path
        self.__chrome_options.add_argument('--disable-gpu')
        self.__chrome_options.add_argument('--no-sandbox')
        self.__chrome_options.add_argument('--headless')
        self.__chrome_options.add_argument("--start-maximized")
        self.__chrome_options.add_argument('--disable-dev-shm-usage')
        self.__chrome_options.add_argument('--incognito')
        self.__chrome_options.add_argument('--disable-extensions')
        self.__chrome_options.add_argument('--version')
        self.__driver = webdriver.Chrome(executable_path=chrome_driver_path, chrome_options=self.__chrome_options, service_log_path='NUL')
        self.__action = ActionChains(self.__driver)
        print('Using driver: ' + self.__driver.execute_script("return navigator.userAgent"))


    def sleep_between_half_to_one_second(self):
        '''
        Sleeps between 0.5 to 1 seconds
        '''
        time.sleep(random.randint(5, 10) / 10.0)


    def sleep_between_three_to_four_seconds(self):
        '''
        Sleeps between 3 to 4 seconds
        '''
        time.sleep(random.randint(30, 40) / 10.0)


    def get_job_urls(self, job_name: str, location: str):
        '''
        Navigate to the job listings and fetch job urls
        '''
        # Navigate to the job listings
        print('Navigate to job listings for ' + job_name + ' in ' + location)
        self.sleep_between_three_to_four_seconds()
        self.__driver.get('https://www.linkedin.com/jobs/')
        job_name_input: WebElement = WebDriverWait(self.__driver, self.__TIMEOUT_SECONDS) \
            .until(EC.presence_of_element_located((By.XPATH , \
            '//input[@aria-label="Search job titles or companies"]'))
        )
        job_name_input.clear()
        job_name_input.send_keys(job_name)
        job_location_input: WebElement = WebDriverWait(self.__driver, self.__TIMEOUT_SECONDS) \
            .until(EC.presence_of_element_located((By.XPATH , \
            '//input[@aria-label="Location"]'))
        )
        job_location_input.clear()
        job_location_input.send_keys(location)
        job_location_input.send_keys(Keys.ENTER)
        self.sleep_between_three_to_four_seconds()
        print('Finished navigating to job listings for ' + job_name + ' in ' + location)

        # Select last 7 days option
        try:
            print('Select last 7 days option')
            time_options_button = WebDriverWait(self.__driver, self.__TIMEOUT_SECONDS) \
                .until(EC.presence_of_element_located((By.XPATH , \
                '//button[@aria-controls="TIME_POSTED_RANGE-dropdown"]'))
            )
            time_options_button.click()
            self.sleep_between_half_to_one_second()
            last_30days_label = WebDriverWait(self.__driver, self.__TIMEOUT_SECONDS) \
                .until(EC.presence_of_element_located((By.XPATH , \
                '//label[@for="TIME_POSTED_RANGE-1"]'))
            )
            last_30days_label.click()
            self.sleep_between_half_to_one_second()
            save_settings_button = WebDriverWait(self.__driver, self.__TIMEOUT_SECONDS) \
                .until(EC.presence_of_element_located((By.XPATH , \
                '//button[@data-tracking-control-name="f_TPR-done-btn"]'))
            )
            save_settings_button.click()
            print('Finished selecting last 7 days option')
            self.sleep_between_three_to_four_seconds()
        except Exception as e:
            print('Failed selecting last 7 days option')
            print(e)
        
        # Scroll down until you have "all results" (Show more jobs tend to "break" after around 900-1000 jobs)
        print('Get all job post urls')
        last_height = self.__driver.execute_script('return document.body.scrollHeight')
        has_retried: bool = False
        no_response_count: int = 0
        while no_response_count <= self.__NO_RESPONSE_MAX:
            self.__driver.execute_script('window.scrollTo(0, ' + str(last_height) + ')')
            new_height = self.__driver.execute_script('return document.body.scrollHeight')
            last_height = new_height
            self.sleep_between_half_to_one_second()
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
            finally:
                self.sleep_between_half_to_one_second()
        job_posts = self.__driver.find_elements_by_xpath('//ul[@class="jobs-search__results-list"]/li/a')
        print('Finished getting all job post urls')

        # Get all currently listed job urls
        urls = []
        for job_post in job_posts:
            urls.append(job_post.get_attribute('href')) 
        self.__driver.execute_script("window.open('');")
        self.__driver.switch_to_window(self.__driver.window_handles[1])
        print('There are ' + str(len(job_posts)) + ' jobs for ' + job_name + ' in ' + location)
        self.sleep_between_three_to_four_seconds()
        return urls


    def remove_duplicates(self, urls):
        '''
        Removes already existing url(s) in the list
        '''
        print('Filter duplicates')
        urls = set(urls)
        new_unique_urls = []
        for url in urls:
            if not(Job.objects.filter(Q(url=url)).exists() or JobPostBanList.objects.filter(Q(url=url)).exists()):
                new_unique_urls.append(url)
        print('After filtering duplicates, there are total ' + str(len(urls)) + ' jobs')
        return urls

    def remove_old_records(self):
        '''
        Removes old records (older than last 7 days)
        '''
        print('Remove records older than 7 days')
        try:
            Job.objects.filter(posted_date__lt=datetime.now() - timedelta(days=7)).delete()
        except Exception as e:
            print('Removing old records failed. Skipping this flow')
            print(e)
        print('Finished removing records older than 7 days')


    def scrape(self):
        '''
        Collects job posts from LinkedIn Jobs with preset configurations
        '''
        # Get the urls for specified criteria
        self.remove_old_records()
        urls = []
        delimiter: str = App.config()['LINKEDIN']['DELIMITER']
        job_names: str = App.config()['LINKEDIN']['JOB_NAMES']
        locations: str = App.config()['LINKEDIN']['LOCATIONS']

        job_names = job_names.split(delimiter)
        locations = locations.split(delimiter)

        for job_name in job_names:
            for location in locations:
                try:
                    urls.extend(self.get_job_urls(job_name, location))
                except Exception as e:
                    print('Exception has occurred. Skipping search for ' + job_name + ' in ' + location)
                    print(e)

        # exit early if there are no jobs found
        if(len(urls) == 0):
            print('There are no jobs found. Exiting the flow')
            return

        # Remove duplicate urls
        urls = self.remove_duplicates(urls)

        # Navigate to each url and extract data
        print('Extract all job posts')
        failed_urls = []
        job_index: int = 1
        for url in urls:
            # Navigate to the url
            print('Extract job post for url = ' + url)
            self.__driver.get(url)
            try:
                show_more_button = WebDriverWait(self.__driver, self.__TIMEOUT_SECONDS) \
                    .until(EC.presence_of_element_located((By.XPATH , \
                    '//button[@class="show-more-less-html__button show-more-less-html__button--more"]'))
                )
                show_more_button.click()
            except Exception as e:
                print('This url is invalid. Refreshing one more time just case: ' + url)
                self.__driver.refresh()
                try:
                    show_more_button = WebDriverWait(self.__driver, self.__TIMEOUT_SECONDS) \
                        .until(EC.presence_of_element_located((By.XPATH , \
                        '//button[@class="show-more-less-html__button show-more-less-html__button--more"]'))
                    )
                    show_more_button.click()
                except Exception as e:
                    print('This url has failed. Putting this in failed url list')
                    failed_urls.append(url)
                    continue

            # Extract job post
            title: str = self.__driver.find_element_by_class_name('topcard__title').text
            company_name: str = self.__driver.find_element_by_class_name('topcard__flavor').text
            description: str = self.__driver.find_element_by_class_name('show-more-less-html__markup').text

            job_header = self.__driver.find_elements_by_class_name('topcard__flavor-row')
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

            # Skip record if this is part of any ban lists
            if CompanyBanList.objects.filter(Q(company_name=company_name)).exists():
                print('This company is banned: ' + company_name + '. Continue with next job post')
                continue
            # Display data
            # print('-----------------------------------------------------')
            # print('url='+url)
            # print('title:'+title)
            # print('location:'+location)
            # print(('description:'+description).encode('unicode_escape'))
            # print('posted_date:'+str(posted_date))
            # print('company:'+company_name)
            # print('job_board_site:'+self.__JOB_BOARD_NAME)
            # print('-----------------------------------------------------')

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
                print('Job(#' + str(job_index) + '/' + str(len(urls)) + ') successfully inserted for ' + title + ' in ' + location)
            except Exception as e: 
                print('Faced an issue while inserting this job to database')
                print(e)
            finally:
                print('Finished extracting job post for url = ' + url)
                job_index += 1
                self.sleep_between_three_to_four_seconds()

        # close
        print('Finished extracting job posts')
        print('Failed urls count: ' + str(len(failed_urls)) + '/' + str(len(urls)))
        self.__driver.close()
        self.__driver.switch_to.window(self.__driver.window_handles[0])
        self.__driver.close()
