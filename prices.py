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
import re

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
        self.tickers_and_prices_list = []    

        # SELENIUM SETTINGS 
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--start-maximized")
        options.add_experimental_option("detach", True)
        #self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
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
            sleep(self.wait_time)

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

    def get_screener_url(self) -> str:
        """Takes current URL.
        
        :return: a string with current URL.
        """
        current_url = self.driver.current_url
        return current_url

    def click_selected_screener(self, choose_screener:str) -> None:
        """
        Clicks selected screener from screeners list.
        """
        USA_Mid_Large_Mega_Cap_xpath = "//a[contains(text(), 'USA_Mid_Large_Mega')]"

        if choose_screener == 'USA_Mid_Large_Mega_Cap':
            self.driver.find_element('xpath', USA_Mid_Large_Mega_Cap_xpath).click()
            sleep(self.wait_time)
            logger.warning(f'Entered to: {choose_screener} ')

    def change_offset_to_100(self):
        """Changes offset to 100 in URL"""   
        self.driver.get(f"{self.driver.current_url}?offset=0&count=100")
        logger.warning('Set table count to 100.')
        
    def go_to_next_page(self, page:int, screener_url:str):
        """It redirects to url with offset for a given page"""

        offset = page * 100 # converts page to offset in url
        self.driver.get(f'{screener_url}?count=100&offset={offset}')


    def check_if_next_button_is_available(self) -> bool:
        """
        Checks if the NEXT button underneath the table is enabled (blue) or disabled (gray)

        :return: True if button is enabled, False if it is disabled
        """
        next_button_disabled_xpath = "//button[@class='Va(m) H(20px) Bd(0) M(0) P(0) Fz(s) Pstart(10px) O(n):f Fw(500) C($gray)' and @disabled]"
        next_button_enabled_xpath = "//button[@class='Va(m) H(20px) Bd(0) M(0) P(0) Fz(s) Pstart(10px) O(n):f Fw(500) C($linkColor)']"
        
        if len(self.driver.find_elements("xpath", next_button_disabled_xpath)) > 0:
            logger.warning("Next button disabled - it means that scraper is on a last page")
            return False
        else:
            bool_value = True if len(self.driver.find_elements("xpath", next_button_enabled_xpath)) > 0 else False
            return bool_value

    def click_next_button(self) -> None:
        """
        Clicks next button if enabled.
        """
        next_button_enabled_xpath = "//button[@class='Va(m) H(20px) Bd(0) M(0) P(0) Fz(s) Pstart(10px) O(n):f Fw(500) C($linkColor)']"
        bool_value = self.check_if_next_button_is_available()
        
        if bool_value == True:
            self.driver.find_element("xpath", next_button_enabled_xpath).click()
            logger.warning("Next button clicked")
        else:
            pass
    
    def get_how_many_pages(self) -> int:
        """
        It takes a text and returns the number of how many pages is in table for offset of 100

        :return: an integer (whole number) of pages that the table is divided for offset equal to 100.
        """
        how_many_tickers_xpath = "//span[@class='Mstart(15px) Fw(500) Fz(s)']"
        how_many_tickers = self.driver.find_element("xpath", how_many_tickers_xpath).text
        
        how_many_pages = int(re.findall('\d+', how_many_tickers)[2]) // 100
        logger.warning(f'Tickers are in {how_many_pages} pages.')
        return how_many_pages

    
    def get_tickers_and_prices_from_one_table_view(self) -> dict:
        """
        Downloads the tickers and its prices from one table view (one table view is ca. 100 queries)
        
        :return: a dictionary, i.e. {ticker:price}
        """
        tickers_and_prices_dict = {}
        ticker_xpath = "//a[contains(@data-test, 'quoteLink' )]"

        how_many_tickers_per_site = len(self.driver.find_elements("xpath", ticker_xpath))
        logger.warning(f"Tickers per current table view: {how_many_tickers_per_site}")

        for i in range(1, (int(how_many_tickers_per_site)+1), 1):
            self.wait.until(EC.visibility_of_element_located((By.XPATH, f'({ticker_xpath})[{i}]')))
            ticker = self.driver.find_element("xpath", f'({ticker_xpath})[{i}]').text
            price_xpath = f"//td[contains(@aria-label,'Price')]/fin-streamer[@data-symbol='{ticker}']"
            price = self.driver.find_element("xpath", price_xpath).text
            tickers_and_prices_dict.update({ticker:price})
            logger.warning(f"Downloaded: {ticker}:{price}")

        return tickers_and_prices_dict

    def save_to_pickle(self) -> pickle:
        """
        It saves tickers and prices list to pickle file. 
        """
        save_pickle_tickers_file = open('prices.pkl', 'wb')
        pickle.dump(self.tickers_and_prices_list, save_pickle_tickers_file)
        save_pickle_tickers_file.close()
        logger.warning('The data has been saved to pickle file.')

    def logout_yahoo(self):
        """
        Logouts from yahoo
        """
        logout_confirmation_button = "//input[@class='pure-button puree-button-secondary page-button']"
        logout_url = "https://login.yahoo.com/config/login/?.intl=us&.lang=en-US&.src=finance&logout_all=1&.direct=1&.done=https://www.yahoo.com"
        
        self.driver.get(logout_url)
        self.driver.find_element("xpath", logout_confirmation_button).click()
        logger.warning('Logged out.')
    
    def get_tickers_and_prices(self):
        self.login_to_yahoo()
        self.accept_cookie()
        self.go_to_screeners_url()
        self.click_selected_screener('USA_Mid_Large_Mega_Cap')
        screener_url = self.get_screener_url()
        self.change_offset_to_100()
        how_many_pages = self.get_how_many_pages()
        for page in range(0, (how_many_pages)+1, 1):
            logger.warning(f"{'='*10}\nPage number {int(page)} is being downloaded.")
            logger.warning(self.driver.current_url)
            data = self.get_tickers_and_prices_from_one_table_view()
            self.tickers_and_prices_list.append(data)
            self.save_to_pickle()
            self.go_to_next_page(page=page+1,screener_url=screener_url)
        self.logout_yahoo
        self.driver.quit()
        

get_prices = PricesScraper(wait_time=5)
get_prices.get_tickers_and_prices()