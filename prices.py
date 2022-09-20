from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ThreadPoolExecutor
from selenium.common.exceptions import TimeoutException
from time import sleep
import pickle
import os
import logging
import json

logging.basicConfig(filename='prices.log', filemode='w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

console = logging.StreamHandler()
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger().addHandler(console)

logger = logging.getLogger('prices.area1')

class PricesScraper():
    """Download tickers from yahoo finance into a list"""

    def __init__(self, wait_time:int):
        """
        :wait_time:time in seconds for Selenium's wait option for handling operations such as
        waiting for element to be visible on the website.
        """
        logger.warning('Stared program prices.py')
        self.wait_time = wait_time
        self.tickers_and_prices = []    

        # SELENIUM SETTINGS 
        options = Options()
        #options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("detach", True)
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, wait_time)
        
    def accept_cookie(self) -> None:
            """
            It clicks accept button for cookie confirmation.
            """ 
            cookie_button_accept_xpath = "//button[@class='btn primary']"
            try:
                self.wait.until(EC.visibility_of_element_located((By.XPATH, cookie_button_accept_xpath)))
                self.driver.find_element("xpath", cookie_button_accept_xpath).click()
            except TimeoutException:
                logger.warning('Cookie Accept Button not found.')
    
    def login_to_yahoo(self) -> None:
        """
        It goes to login page and type username and password" 
        """
        with open('login.json') as login_file:
            login_data = json.load(login_file)

        login = login_data['login']
        password = login_data['password']
        login_username_xpath = "//input[@id='login-username']"
        login_passwd_xpath = "//input[@id='login-passwd']"

        def enter_login_or_pass(text, xpath):
            input_form = self.driver.find_element("xpath", xpath)
            input_form.send_keys(text)
            input_form.send_keys(Keys.ENTER)
            sleep(3)

        self.driver.get('https://login.yahoo.com/')
        enter_login_or_pass(login, login_username_xpath)
        enter_login_or_pass(password, login_passwd_xpath)
        logger.warning('Logged in.')

    def go_to_screeners_url(self) -> None:
        """
        Redirects to the page with previously set screeners. 
        """
        screeners_url = f"https://finance.yahoo.com/screener/"
        self.driver.get(screeners_url)           
        logger.warning(f"Entered to: {screeners_url}")

    def click_selected_screener(self, choose_screener) -> None:
        USA_Mid_Large_Mega_Cap_xpath = "//a[contains(text(), 'USA_Mid_Large_Mega')]"

        if choose_screener == 'USA_Mid_Large_Mega_Cap':
            self.driver.find_element('xpath', USA_Mid_Large_Mega_Cap_xpath).click()
            logger.warning(f'Entered to: {choose_screener} ')
            sleep(3)
        
        self.driver.get(f"{self.driver.current_url}?offset=0&count=100")
        logger.warning('Set table count to 100.')
        
    def logout_yahoo(self):
        logout_confirmation_button = "//input[@class='pure-button puree-button-secondary page-button']"
        logout_url = "https://login.yahoo.com/config/login/?.intl=us&.lang=en-US&.src=finance&logout_all=1&.direct=1&.done=https://www.yahoo.com"
        
        self.driver.get(logout_url)
        self.driver.find_element("xpath", logout_confirmation_button).click()
        logger.warning('Logged out.')




        

get_prices = PricesScraper(wait_time=5)
get_prices.login_to_yahoo()
get_prices.accept_cookie()
get_prices.go_to_screeners_url()
get_prices.click_selected_screener('USA_Mid_Large_Mega_Cap')
get_prices.logout_yahoo()