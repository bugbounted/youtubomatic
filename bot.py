import time
from instagrapi import Client
import requests
from moviepy.editor import VideoFileClip
from playwright.sync_api import sync_playwright
import re
import pymongo
import cv2
import datetime
import urllib3
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException, \
    UnexpectedAlertPresentException, ElementNotInteractableException, ElementClickInterceptedException, \
    NoSuchWindowException, WebDriverException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import logging
import os
from threading import Event
from datetime import datetime, timedelta
import secrets
from bs4 import BeautifulSoup
from random import shuffle

# Logging Initializer
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Initializing EVENT to enable EVENT.wait() which is more effective than time.sleep()
EVENT = Event()

# Making Program to start with other locators instead of javascript locator
YT_JAVASCRIPT = False

# Locations For YouTube button elements
ytbutton_elements_location_dict = {
    "yt_id_like_button": "like-button",
    "yt_id_sub_button_type1": "subscribe-button",
    "yt_css_like_button_active": "#top-level-buttons-computed > "
                                 "ytd-toggle-button-renderer.style-scope.ytd-menu-renderer.force-icon-button.style"
                                 "-default-active",
    "yt_css_sub_button": "#subscribe-button > ytd-subscribe-button-renderer > tp-yt-paper-button",
    "yt_js_like_button": "document.querySelector('#top-level-buttons-computed >"
                         " ytd-toggle-button-renderer:nth-child(1)').click()",
    "yt_js_sub_button": 'document.querySelector("#subscribe-button >'
                        ' ytd-subscribe-button-renderer > tp-yt-paper-button").click()',

}


def get_clear_browsing_button(driver: webdriver) -> webdriver:
    """Find the "CLEAR BROWSING BUTTON" on the Chrome settings page.
    Args:
    - driver (webdriver): webdriver parameter.
    Return
    - WebElement: returns "* /deep/ #clearBrowsingDataConfirm" WebElement.
    """
    return driver.find_element(By.CSS_SELECTOR, '* /deep/ #clearBrowsingDataConfirm')


def clear_cache(driver: webdriver, timeout: int = 60) -> None:
    """Clear the cookies and cache for the ChromeDriver instance.
    Args:
    - driver (webdriver): webdriver parameter.
    - timeout (int): Parameter to stop program after reaches timeout.
    Returns:
    - None(NoneType)
    """
    driver.get('chrome://settings/clearBrowserData')
    wait = WebDriverWait(driver, timeout)
    wait.until(get_clear_browsing_button)
    get_clear_browsing_button(driver).click()
    wait.until_not(get_clear_browsing_button)


def set_driver_opt(req_dict: dict,
                   headless: bool = True,
                   website: str = "") -> webdriver:
    """Set driver options for chrome or firefox
    Args:
    - req_dict(dict): dictionary object of required parameters
    - is_headless(bool): bool parameter to check for chrome headless or not
    - website (string): string parameter to enable extensions corresponding to the Website.
    Returns:
    - webdriver: returns driver with options already added to it.
    """
    # Chrome
    chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        prefs = {"profile.managed_default_content_settings.images": 2,
                 "disk-cache-size": 4096,
                 "profile.password_manager_enabled": False,
                 "credentials_enable_service": False}
        chrome_options.add_experimental_option('prefs', prefs)
        chrome_options.add_experimental_option("excludeSwitches", ["ignore-certificate-errors"])
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--proxy-server='direct://'")
        chrome_options.add_argument("--proxy-bypass-list=*")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--mute-audio")
        chrome_options.add_argument("--window-size=1920,1080")

    # Set github token environment for webdriver manager
    os.environ['GH_TOKEN'] = req_dict['github_token']
    # Save binary webdrivers to project location
    os.environ['WDM_LOCAL'] = '1'
    # Enable or Disable SSL verification when downloading webdrivers
    os.environ['WDM_SSL_VERIFY'] = '1'
    # Disable logging for webdriver manager
    os.environ['WDM_LOG'] = str(logging.NOTSET)
    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=chrome_options)


def youtube_too_many_controller() -> int:
    """ Checks user's Google account if there are too many subscriptions or likes for the given google account and
    returns boolean that represents condition
        Args:
        - driver(webdriver): webdriver parameter.
        - req_dict(dict): dictionary object of required parameters
        - has_sign_in_btn (bool): bool parameter to check if page has sign_in_button
        Returns:
        - Boolean(bool)
        """
    toomany_suborlike = False
    return toomany_suborlike


def google_login(driver: webdriver,
                 req_dict: dict,
                 has_login_btn: bool = True,
                 already_in_website: bool = True) -> None:
    """ Logins to Google with given credentials.
    Args:
    - driver(webdriver): webdriver parameter.
    - req_dict(dict): dictionary object of required parameters
    - has_sign_in_btn (bool): bool parameter to check if page has sign_in_button
    Returns:
    - None(NoneType)
    """
    if has_login_btn:
        sign_in_button = driver.find_element(By.CSS_SELECTOR, "#buttons > ytd-button-renderer")
        ActionChains(driver).move_to_element(sign_in_button).click().perform()
    if already_in_website:
        EVENT.wait(0.25)
    else:
        driver.get("https://accounts.google.com/signin")
    EVENT.wait(secrets.choice(range(1, 4)))
    email_area = driver.find_element(By.ID, "identifierId")
    email_area.send_keys(req_dict['yt_email'])
    driver.find_element(By.CSS_SELECTOR, "#identifierNext > div > button").click()
    EVENT.wait(secrets.choice(range(1, 4)))
    pw_area = driver.find_element(By.CSS_SELECTOR, "#password > div.aCsJod.oJeWuf > div > div.Xb9hP > input")
    pw_area.send_keys(req_dict['yt_pw'])
    EVENT.wait(secrets.choice(range(1, 4)))
    driver.find_element(By.CSS_SELECTOR, "#passwordNext > div > button").click()
    EVENT.wait(secrets.choice(range(1, 4)))


class youtube:
    def __init__(self):
        pass

    def upload_video(self, video, title, related_hashtag_keyword, profile="Default"):
        
        options = webdriver.ChromeOptions()
        options.add_argument("--log-level=3")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        prefs = {"profile.managed_default_content_settings.images": 2,
                 "disk-cache-size": 4096,
                 "profile.password_manager_enabled": False,
                 "credentials_enable_service": False}
        options.add_experimental_option('prefs', prefs)
        options.add_experimental_option("excludeSwitches", ["ignore-certificate-errors"])
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--disable-notifications")
        options.add_argument("--proxy-server='direct://'")
        options.add_argument("--proxy-bypass-list=*")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-infobars")
        options.add_argument("--mute-audio")
        options.add_argument("--window-size=1920,1080")

    # Set github token environment for webdriver manager
    os.environ['GH_TOKEN'] = req_dict['github_token']
    # Save binary webdrivers to project location
    os.environ['WDM_LOCAL'] = '1'
    # Enable or Disable SSL verification when downloading webdrivers
    os.environ['WDM_SSL_VERIFY'] = '1'
    # Disable logging for webdriver manager
    os.environ['WDM_LOG'] = str(logging.NOTSET)
    
    path = '/usr/local/bin/chromedriver'
    service = Service(path)
    
    driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), chrome_options=options, service=service)
        
        driver.get("https://studio.youtube.com")
        time.sleep(3)

        # Clicking upload button
        while True:
            try:
                upload_button = driver.find_element(
                    By.XPATH, '//*[@id="upload-icon"]')
                upload_button.click()
                break
            except:
                print("Unable to locate upload button, trying again ...")
            finally:
                time.sleep(5)

        # Setting video path to be upload
        while True:
            try:
                file_input = driver.find_element(
                    By.XPATH, '//input[@name="Filedata"]')
                file_input.send_keys(video)
                break
            except Exception as e:
                print(
                    "Unable to locate video file input, trying again ... \n {}".format(e))
            finally:
                time.sleep(10)

        # Setting a caption
        while True:
            try:
                caption = title + \
                    self.get_RelatedHashtags(
                        related_hashtag_keyword, (90 - len(title)))
                caption_input = driver.find_element(
                    By.XPATH, '//div[contains(@aria-label, "Agrega un título")]')
                caption_input.send_keys(caption)
                break
            except Exception as e:
                print("Unable to locate title field, trying again ... \n {}".format(e))
            finally:
                time.sleep(10)

        # Adding hashtags
        while True:
            try:
                desc = "\n\n" + \
                    self.get_RelatedHashtags(related_hashtag_keyword, 4500)
                desc_input = driver.find_element(
                    By.XPATH, '//div[contains(@aria-label, "Cuéntales a los usuarios sobre el video")]')
                desc_input.send_keys(desc)
                break
            except Exception as e:
                print("Unable to locate desc field, trying again ... \n {}".format(e))
            finally:
                time.sleep(10)

        # Clicking next button 3 times
        while True:
            try:
                next_button = driver.find_element(
                    By.XPATH, '//*[@id="next-button"]')
                for i in range(3):
                    next_button.click()
                    time.sleep(3)
                break
            except:
                print(
                    "Unable to locate next button {i}, trying again ...".format(i))
            finally:
                time.sleep(10)

        # Clicking post button
        while True:
            try:
                driver.find_element(
                    By.XPATH, '//span[text()[contains(., "Se completaron las verificaciones. No se encontraron problemas.")]]')
                print("Verification done ...")
                post_button = driver.find_element(
                    By.XPATH, '//*[@id="done-button"]')
                post_button.click()
                break
            except:
                print("Verification still in progress, trying again ...")
            finally:
                time.sleep(30)
        # bot.quit()

    def get_RelatedHashtags(self, keyword, char_limit):
        try:
            r = requests.get(
                "https://best-hashtags.com/hashtag/" + keyword + "/")
            c = r.content

            soup = BeautifulSoup(c, "html.parser")

            hashtags = []
            for word in ["popular", "medium", "easy"]:
                try:
                    print("Looking for " + word + " hashtags ...")
                    element = soup.find_all("div", {"id": word})
                    element = element[0].find_all("div", {"class": "tag-box"})
                    element = element[0].find_all()
                    element = element[0].text
                    for hashtag in element.split(" "):
                        hashtags.append(hashtag)
                except:
                    next

            hashtags = set(hashtags)
            hashtags = list(hashtags)
            shuffle(hashtags)

            while len(" ".join(hashtags)) > char_limit:
                hashtags = hashtags[:-1]

            return " ".join(hashtags)
        except Exception as e:
            print("Unable to get hashtags ... \n {}".format(e))
            return "#NoHuboHashtagsCompa"
    
#connect mongo
MongoClient = pymongo.MongoClient("mongodb+srv://")

def get_last_video_url(username):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        browser = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36")
        page = browser.new_page()
        page.goto("http://www.tiktok.com/@{}".format(username), timeout = 30000)
        latest_video = page.query_selector(
            'xpath=/html/body/div[2]/div[2]/div[2]/div/div[2]/div[2]/div/div/div[1]/div/div/a')
        url = latest_video.get_property('href')
        browser.close()
        return url


def get_download_url(username):
    url = get_last_video_url(username)
    url = str(url) + '/'
    video_id = re.findall(
        r'https\:\/\/www\.tiktok\.com\/@{}\/video\/(.*?)\/'.format(username), url)[0]
    resopnses = requests.get(
        'https://api-v1.majhcc.com/api/tk?url={}'.format(url))
    return resopnses.json()['link'], video_id


def video_download(self, url: str, filename: str) -> None:
    connection_pool = urllib3.PoolManager()
    resp = connection_pool.request('GET',url )
    f = open(filename, 'wb')
    f.write(resp.data)
    f.close()
    resp.release_conn()
    
    def upload(self):
        driver = self.get_driver()
        for data in self.db(get={'upload': None})[:self.limit]:
            url = data[0]
            if self.db(lookup={'url': url, 'upload': True}):
                meta = data[1]
                filename = self.counter
                url = 'https://studio.youtube.com/channel/UCcF2MpZNT2MeSsN2H-K1gQA/videos/upload?d=ud&filter=%5B%5D&sort=%7B%22columnType%22%3A%22date%22%2C%22sortOrder%22%3A%22DESCENDING%22%7D'
                driver.get(url)
                driver.find_element(by=By.XPATH, value="//input[@type='file']").send_keys(f"ready_to_upload\\{self.username}_{filename}.mp4")
                self.sleep_it(custom={"min": 5, "max": 7})
                driver.find_element(by=By.XPATH,value="//div[@id='textbox' and contains(@aria-label,'title')]").send_keys(f" {meta}")
                self.sleep_it(custom={"min": 5, "max": 7})
                driver.find_element(by=By.XPATH,value="//div[@id='textbox' and contains(@aria-label,'viewers')]").send_keys(f"{meta} \nCredit: {self.username}")
                self.sleep_it(custom={"min": 5, "max": 7})
                driver.find_element(by=By.XPATH,value="//tp-yt-paper-radio-button[@name='VIDEO_MADE_FOR_KIDS_NOT_MFK'] //div[@id='offRadio']").click()
                self.sleep_it(custom={"min": 5, "max": 7})
                driver.find_element(by=By.XPATH, value="//div[contains(text(),'Next')]").click()
                self.sleep_it(custom={"min": 5, "max": 7})
                driver.find_element(by=By.XPATH, value="//div[contains(text(),'Next')]").click()
                self.sleep_it(custom={"min": 5, "max": 7})
                driver.find_element(by=By.XPATH, value="//div[contains(text(),'Next')]").click()
                self.sleep_it(custom={"min": 5, "max": 7})
                driver.find_element(by=By.XPATH, value="//tp-yt-paper-radio-button[@name='PUBLIC']").click()
                self.sleep_it(custom={"min": 5, "max": 7})
                driver.find_element(by=By.XPATH, value="//ytcp-button/div[contains(text(),'Publish')]").click()
                time.sleep(10)
                self.counter += 1
                self.db(store={'url': url, 'upload': True})
        driver.close()
