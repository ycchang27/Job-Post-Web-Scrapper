# Job Post Web Scrapper

<h2>Introduction</h2>

This is designed to reduce time to reduce time browsing through job board sites like LinkedIn.

Combined with Selenium (webscraping) and Heroku Scheduler (batch operation), this will receive data daily from job board sites and display it on web UI, which contains multiple filter options:
* Job title
* Job location
* Job description
* Company name

![demo](readme_files/demo_ui.gif)
Thanks to the personalized query, there are noticibly reduced number of jobs to look.

<h2>Disclaimer</h2>

This project is not intended to replace existing job boards by any means. This is only intended to streamline job search time for personal purposes by adding additional filters. 

To respect the job board sites, webscraping process has purposeful delays between requests, and this project will be used only for personal uses.

<h2>Setup</h2>

To execute this project, you must do the following:
1. git clone to your installation directory.
2. pip install necessary imports in [requirements.txt](requirements.txt)
3. Install [Google Chrome](https://www.google.com/chrome/) and [ChromeDriver](https://chromedriver.chromium.org/downloads)
4. Create .ini file at the project root and add the following in the file: 
```
[APP]
SECRET_KEY = <any text>
DEBUG = <True or False>
GOOGLE_CHROME_BIN = <path of Google Chrome directory>\\chrome.exe
CHROMEDRIVER_PATH = <path of Chrome Driver directory>\\chromedriver.exe
CSV_DIRECTORY = <path to write csv file>

[DATABASE]
ENGINE =
NAME =
HOST =
USER =
PASSWORD =
PORT =

[LINKEDIN]
DELIMITER = ~
JOB_NAMES = Software Engineer~Junior Software Engineer~Entry Level Software Engineer
LOCATIONS = San Francisco, California~Bellevue, Washington~San Diego, California
```

5. Migrate schema in local. If you followed the config given above, then it will create a sqlite database in your root directory. 
```
python manage.py makemigrations
python manage.py migrate
```
6. Try running webscraping. Warning: This process will take an hour or more.
```
python manage.py job_scrape
```
7. Try running the server to view the UI.
```
python manage.py runserver
```
8. Optional: Create admin to access your django admin db page. [Link to the django admin tutorial.](https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/Admin_site)
```
python manage.py createsuperuser
```