import sys
import os
import requests
import time
import csv
import json


from bs4 import BeautifulSoup
from selenium import webdriver

# from elementtree.ElementTree import Element


class ifitScraper(object):
    # based on https://towardsdatascience.com/scraping-data-behind-site-logins-with-python-ee0676f523ee
    def __init__(self, dl_dir, debug=False, debug_dir="ifit_captures"):
        self.debug = debug
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--incognito')
        options.add_argument('--headless')
        options.add_experimental_option("prefs", {
            "download.default_directory": dl_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing_for_trusted_sources_enabled": False,
            "safebrowsing.enabled": False
        })
        self.driver = webdriver.Chrome(
            executable_path="/Users/jacobkarcz/dev/selenium/chromium-browser/85.0.4183.87/chromedriver",
            chrome_options=options)
        self.driver.implicitly_wait(5)  # wait bc the table takes time to load
        self.base_url = "https://www.ifit.com"

        # # flexible driver sol'n (for the cloud)
        # # pip install webdriver-manager
        # from webdriver_manager.chrome import ChromeDriverManager
        # self.driver = webdriver.Chrome(ChromeDriverManager().install())

        cwd = os.getcwd()
        self.debug_dir = os.path.join(cwd, debug_dir)
        creds_fp = os.path.join(cwd, "credentials", "ifit.json")
        with open(creds_fp) as c:
            creds = json.load(c)

        self.session = requests.Session()
        payload = {"email": creds.get("username"),
                   "password": creds.get("password")
                   }
        lgs = self.session.post("https://www.ifit.com/web-api/login", data=payload)

        self.driver.get("https://www.ifit.com/login")

        # get cookies & transfer session
        cookies = self.session.cookies.items()
        for cookie in cookies:
            self.driver.add_cookie(cookie_dict={"name": cookie[0], "value": cookie[1], "path": "/"})

    def find_and_download_csv_files(self):

        # navigate page using selenium
        self.driver.get("https://www.ifit.com/me/workouts")
        if self.debug:
            title = self.driver.title
            url = self.driver.current_url
            f = open(self.debug_dir + "/ifit_workouts.png", "wb")
            f.write(self.driver.get_screenshot_as_png())
            with open(self.debug_dir + "/ifit_workouts.html", 'wb') as f:
                f.write(self.driver.page_source.encode('utf-8'))
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        workout_rows = soup.find_all(class_="two title workout-row")

        # traverse workout table and collect workout urls
        for tag in workout_rows:
            if tag.name == 'div':  # skip header element
                link = self.base_url + tag.next_element['href']
                self.driver.get(link)

                if self.debug:
                    title = self.driver.title
                    url = self.driver.current_url
                    f = open(self.debug_dir + "/workout_detail.png", "wb")
                    f.write(self.driver.get_screenshot_as_png())
                    with open(self.debug_dir + "./workout_detail.html", 'wb') as f:
                        f.write(self.driver.page_source.encode('utf-8'))

                # select csv from export dropdown menu
                self.driver.find_elements_by_class_name("export-btn")[0].click()
                self.driver.find_elements_by_class_name("js-export-csv")[0].click()

                # select export with incline from popup if cycling workout
                try:
                    c = self.driver.find_elements_by_class_name("js-modal-yes")[0].click()
                except Exception as e:
                    if self.debug:
                        f = open(self.debug_dir + "/download_error.png", "wb")
                        f.write(self.driver.get_screenshot_as_png())
                        with open(self.debug_dir + "/download_error.html", 'wb') as f:
                            f.write(self.driver.page_source.encode('utf-8'))

                # yield file downloads

    def find_and_download_tcx_files(self):

        # navigate page using selenium
        self.driver.get("https://www.ifit.com/me/workouts")
        if self.debug:
            title = self.driver.title
            url = self.driver.current_url
            f = open(self.debug_dir + "/ifit_workouts.png", "wb")
            f.write(self.driver.get_screenshot_as_png())
            with open(self.debug_dir + "/ifit_workouts.html", 'wb') as f:
                f.write(self.driver.page_source.encode('utf-8'))
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        workout_rows = soup.find_all(class_="two title workout-row")

        # traverse workout table and collect workout urls
        for tag in workout_rows:
            if tag.name == 'div':  # skip header element
                link = self.base_url + tag.next_element['href']
                self.driver.get(link)

                if self.debug:
                    title = self.driver.title
                    url = self.driver.current_url
                    f = open(self.debug_dir + "/workout_detail.png", "wb")
                    f.write(self.driver.get_screenshot_as_png())
                    with open(self.debug_dir + "./workout_detail.html", 'wb') as f:
                        f.write(self.driver.page_source.encode('utf-8'))

                # select csv from export dropdown menu
                self.driver.find_elements_by_class_name("export-btn")[0].click()
                # self.driver.find_elements_by_class_name("js-export-csv")[0].click()
                # use the link or use a click on the first li element
                # <a role="button" data-toggle="dropdown" href="#" class="btn export-btn"><span class="icon-download-new"></span><span> Export</span></a>
                #   <ul class="dropdown-menu">      <li><a href="/workout/export/tcx/5fa2ed71058a0200a9140c97" target="_exportPane">TCX</a></li><li><a href="#" class="js-export-csv">CSV</a></li></ul>
                #     <li>
                #       <a href="/workout/export/tcx/5fa2ed71058a0200a9140c97" target="_exportPane">TCX</a>
                #     </li>
                #     <li>
                #       <a href="#" class="js-export-csv">CSV</a>
                #     </li>
                #       <a href="#" class="js-export-csv">CSV</a>
                #     </li>
                # <ul class="dropdown-menu"><li><a href="/workout/export/tcx/5fa2ed71058a0200a9140c97" target="_exportPane">TCX</a></li><li><a href="#" class="js-export-csv">CSV</a></li></ul>
                # <div class="dropdown"><a role="button" data-toggle="dropdown" href="#" class="btn export-btn"><span class="icon-download-new"></span><span> Export</span></a><ul class="dropdown-menu"><li><a href="/workout/export/tcx/5fa2ed71058a0200a9140c97" target="_exportPane">TCX</a></li><li><a href="#" class="js-export-csv">CSV</a></li></ul></div>


    def fix_tcx(self, fp):
        # open file
        # with open(fp, "rw") as f:
        import xml.etree.ElementTree as ET
        tree = ET.parse(fp)
        root = tree.getroot()


        # iterate over trackpoints and calculate avg speed, watts, hr

        # find latest trackpoint distance and add to lap distance

        # fix activity lap

        # save file

        pass




    def finish(self):
        return self.driver.close()

