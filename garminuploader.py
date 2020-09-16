import sys
import os
import requests
import csv
import time
import json

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumrequests import Chrome

JS_DROP_FILE = """
        var target = arguments[0],
            offsetX = arguments[1],
            offsetY = arguments[2],
            document = target.ownerDocument || document,
            window = document.defaultView || window;
    
        var input = document.createElement('INPUT');
        input.type = 'file';
        input.onchange = function () {
          var rect = target.getBoundingClientRect(),
              x = rect.left + (offsetX || (rect.width >> 1)),
              y = rect.top + (offsetY || (rect.height >> 1)),
              dataTransfer = { files: this.files };
    
          ['dragenter', 'dragover', 'drop'].forEach(function (name) {
            var evt = document.createEvent('MouseEvent');
            evt.initMouseEvent(name, !0, !0, window, 0, 0, 0, x, y, !1, !1, !1, !1, 0, null);
            evt.dataTransfer = dataTransfer;
            target.dispatchEvent(evt);
          });
    
          setTimeout(function () { document.body.removeChild(input); }, 25);
        };
        document.body.appendChild(input);
        return input;
    """  # solution found at https://stackoverflow.com/questions/43382447/python-with-selenium-drag-and-drop-from-file-system-to-webdriver

class garminUploader(object):
    def __init__(self, debug=False, debug_dir="garmin_captures"):
        self.debug = debug
        self.signin = "https://connect.garmin.com/signin/"
        self.home = "https://connect.garmin.com/modern/"
        self.import_url = "https://connect.garmin.com/modern/import-data"

        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--incognito')
        options.add_argument('--headless')
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--disable-notifications")
        self.driver = webdriver.Chrome(
            executable_path="/Users/jacobkarcz/dev/selenium/chromium-browser/85.0.4183.87/chromedriver",
            chrome_options=options)
        self.wait = WebDriverWait(self.driver, 13)

        cwd = os.getcwd()
        self.debug_dir = os.path.join(cwd, debug_dir)
        creds_fp = os.path.join(cwd, "credentials", "garmin.json")
        with open(creds_fp) as c:
            creds = json.load(c)

        try:
            self.driver.get(self.signin)
            time.sleep(5)
            # login is dynamic w js
            # switch to iframe once it's present:
            self.wait.until(EC.presence_of_element_located((By.ID, "gauth-widget-frame-gauth-widget")))
            self.driver.switch_to.frame("gauth-widget-frame-gauth-widget")

            # fill out the form
            email = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
            email.clear()
            time.sleep(1)
            u = creds.get("username")
            email.send_keys(str(u))
            pw = self.wait.until(EC.presence_of_element_located((By.ID, "password")))
            pw.clear()
            time.sleep(1)
            p = creds.get("password")
            pw.send_keys(str(p))
            time.sleep(1)
            # self.driver.find_element_by_id("login-btn-signin").click()
            form = self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="login-form"]')))
            # self.driver.find_element_by_xpath('//*[@id="login-form"]')
            form.submit()

            self.wait.until(lambda driver: self.driver.current_url != self.signin)

            if self.debug:
                title = self.driver.title
                url = self.driver.current_url
                windows = self.driver.window_handles
                f = open(self.debug_dir + "/garmin_init_debug.png", "wb")
                f.write(self.driver.get_screenshot_as_png())
                with open(self.debug_dir + "/garmin_init_debug.html", 'wb') as f:
                    f.write(self.driver.page_source.encode('utf-8'))

            if self.driver.current_url != self.home:
                raise Exception(f"wrong url, {self.driver.current_url}")

        except Exception as e:
            title = self.driver.title
            url = self.driver.current_url
            windows = self.driver.window_handles
            f = open(self.debug_dir + "/garmin_init_err.png", "wb")
            f.write(self.driver.get_screenshot_as_png())
            with open(self.debug_dir + "/garmin_init_err.html", 'wb') as f:
                f.write(self.driver.page_source.encode('utf-8'))
            raise e

    def drag_and_drop_file(self, path):
        try:
            # drag and drop files
            self.driver.get(self.import_url)
            drop_target = self.wait.until(EC.presence_of_element_located((By.ID, "import-data")))
            for f in os.listdir(path):
                fp = f"{path}/{f}"
                file_input = self.driver.execute_script(JS_DROP_FILE, drop_target, 0, 0)
                file_input.send_keys(fp)

            # import
            self.driver.find_element_by_id("import-data-start").click()
            if self.debug:
                title = self.driver.title
                url = self.driver.current_url
                f = open(self.debug_dir + "/garmin_import.png", "wb")
                f.write(self.driver.get_screenshot_as_png())
                with open(self.debug_dir + "/garmin_import.html", 'wb') as f:
                    f.write(self.driver.page_source.encode('utf-8'))
            # look for "An error occurred with your upload. Please try again." (<span class="dz-error-message">An error occurred with your upload. Please try again.</span>)

        except Exception as e:
            title = self.driver.title
            url = self.driver.current_url
            f = open(self.debug_dir + "/garmin_file_err.png", "wb")
            f.write(self.driver.get_screenshot_as_png())
            with open(self.debug_dir + "/garmin_file_err.html", 'wb') as f:
                f.write(self.driver.page_source.encode('utf-8'))
            raise e

    def finish(self):
        return self.driver.close()

    # def import_data(self):
    #     self.driver.find_element_by_id("import-data-start").click()
    #     if self.debug:
    #         title = self.driver.title
    #         url = self.driver.current_url
    #         f = open(self.debug_dir + "/garmin_import.png", "wb")
    #         f.write(self.driver.get_screenshot_as_png())
    #         with open(self.debug_dir + "/garmin_import.html", 'wb') as f:
    #             f.write(self.driver.page_source.encode('utf-8'))
