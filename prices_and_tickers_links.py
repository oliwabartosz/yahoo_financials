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

level = logging.INFO
logging.basicConfig(format='%(asctime)s - %(name)-12s: %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=level)
console = logging.StreamHandler()

class PricesAndTickerLinksScraper():
    """Download prices for tickers from yahoo as dictionary or tickers links as list"""

    def __init__(self, wait_time:int, log_name:str, pickle_filename:str, log_filename:str):
        """
        :wait_time:time in seconds for Selenium's wait option for handling operations such as
        waiting for element to be visible on the website.
        :log_name: name of the log area.
        :pickle_filename: put a filename to save as pickle files.
        :log_filename: put a filename to save as logfile.
        """

        self.log_name = log_name
        self.pickle_filename = pickle_filename
        self.log_filename = log_filename

        self.logger = logging.getLogger(self.log_name)
        file_handler = logging.FileHandler(log_filename)
        formatter = logging.Formatter('%(asctime)s - %(name)-12s: %(levelname)-8s %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.info('Stared program prices_and_tickers_links.py')

        self.wait_time = wait_time
        self.tickers_and_prices_list = []
        self.tickers_links = []


        # SELENIUM SETTINGS 
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--start-maximized")
        options.add_experimental_option("detach", True)
        try:
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        except:
            pass
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
                self.logger.info('Cookie Accept Button not found.')
    
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
        self.logger.info('Logged in.')

    def go_to_screeners_url(self) -> None:
        """
        Redirects to the page with previously set screeners. 
        """
        screeners_url = f"https://finance.yahoo.com/screener/"
        self.driver.get(screeners_url)           
        self.logger.info(f"Entered to: {screeners_url}")

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
            self.logger.info(f'Entered to: {choose_screener} ')

    def change_offset_to_100(self):
        """Changes offset to 100 in URL"""   
        self.driver.get(f"{self.driver.current_url}?offset=0&count=100")
        self.logger.info('Set table count to 100.')
        
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
            self.logger.info("Next button disabled - it means that scraper is on a last page")
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
            self.logger.info("Next button clicked")
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
        self.logger.info(f'Tickers are in {how_many_pages} pages.')
        return how_many_pages

    
    def get_tickers_and_prices_from_one_table_view(self) -> dict:
        """
        Downloads the tickers and its prices from one table view (one table view is ca. 100 queries)
        
        :return: a dictionary, i.e. {ticker:price}
        """
        tickers_and_prices_dict = {}
        ticker_xpath = "//a[contains(@data-test, 'quoteLink' )]"

        how_many_tickers_per_site = len(self.driver.find_elements("xpath", ticker_xpath))
        self.logger.info(f"Tickers per current table view: {how_many_tickers_per_site}")

        for i in range(1, (int(how_many_tickers_per_site)+1), 1):
            self.wait.until(EC.visibility_of_element_located((By.XPATH, f'({ticker_xpath})[{i}]')))
            ticker = self.driver.find_element("xpath", f'({ticker_xpath})[{i}]').text
            price_xpath = f"//td[contains(@aria-label,'Price')]/fin-streamer[@data-symbol='{ticker}']"
            price = self.driver.find_element("xpath", price_xpath).text
            tickers_and_prices_dict.update({ticker:price})
            self.logger.info(f"Downloaded: {ticker}:{price}")

        return tickers_and_prices_dict

    def get_tickers_links_from_one_table_view(self):
        """
        Gets the data from table and updates the main list with ticker links.
        """
        ticker_xpath = "//a[contains(@data-test, 'quoteLink' )]"

        how_many_tickers_per_site = len(self.driver.find_elements("xpath", ticker_xpath))
        self.logger.info(f"Tickers per current table view: {how_many_tickers_per_site}")

        for i in range(1, (int(how_many_tickers_per_site)+1), 1):
            self.wait.until(EC.visibility_of_element_located((By.XPATH, f'({ticker_xpath})[{i}]')))
            ticker = self.driver.find_element("xpath", f'({ticker_xpath})[{i}]').get_attribute('href')
            self.tickers_links.append(ticker)
            self.logger.info(f"Downloaded: {ticker}")

    def delete_file(self, file:str):
        """
        It deletes selected file.

        :file: input a file to delete as string.\n
        e.g. delete_file('file.pkl')
        """
        if os.path.exists(file):
            os.remove(file)
            self.logger.info(f"The file: {file} has been deleted.")
        else:
            pass

    def save_to_pickle(self, prices:bool, tickers_links:bool) -> pickle:
        """
        It saves tickers and prices list to pickle file. 
        """
        if prices:
            object_to_file = self.tickers_and_prices_list
        elif tickers_links:
            object_to_file = self.tickers_links

        with open(self.pickle_filename, 'wb') as save_pickle_tickers_file:
            pickle.dump(object_to_file, save_pickle_tickers_file)
        
        self.logger.info('The data has been saved to pickle file.')

    def logout_yahoo(self):
        """
        Logouts from yahoo
        """
        logout_confirmation_button = "//input[@class='pure-button puree-button-secondary page-button']"
        logout_url = "https://login.yahoo.com/config/login/?.intl=us&.lang=en-US&.src=finance&logout_all=1&.direct=1&.done=https://www.yahoo.com"
        
        self.driver.get(logout_url)
        self.driver.find_element("xpath", logout_confirmation_button).click()
        self.logger.info('Logged out.')
    
    def get_tickers_and_prices(self):
        self.login_to_yahoo()
        #self.accept_cookie()
        self.go_to_screeners_url()
        self.click_selected_screener('USA_Mid_Large_Mega_Cap')
        screener_url = self.get_screener_url()
        self.change_offset_to_100()
        how_many_pages = self.get_how_many_pages()
        for page in range(0, (how_many_pages)+1, 1):
            self.logger.info(f"{'='*10}\nPage number {int(page)} is being downloaded.")
            self.logger.info(self.driver.current_url)
            data = self.get_tickers_and_prices_from_one_table_view()
            self.tickers_and_prices_list.append(data)
            self.save_to_pickle(prices=True, tickers_links=False)
            self.go_to_next_page(page=page+1,screener_url=screener_url)
        self.logout_yahoo
        self.driver.quit()
        
    def get_tickers_links(self):
        self.delete_file('tickers.pkl')
        self.login_to_yahoo()
        self.go_to_screeners_url()
        self.click_selected_screener('USA_Mid_Large_Mega_Cap')
        screener_url = self.get_screener_url()
        self.change_offset_to_100()
        how_many_pages = self.get_how_many_pages()
        for page in range(0, (how_many_pages)+1, 1):
            self.logger.info(f"{'='*10}\nPage number {int(page)} is being downloaded.")
            self.logger.info(self.driver.current_url)
            self.get_tickers_links_from_one_table_view()
            self.save_to_pickle(prices=False, tickers_links=True)
            self.go_to_next_page(page=page+1,screener_url=screener_url)
        self.logout_yahoo
        self.driver.quit()
