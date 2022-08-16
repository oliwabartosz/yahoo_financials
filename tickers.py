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

logging.basicConfig(filename='tickers.log', filemode='w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

console = logging.StreamHandler()
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger().addHandler(console)

logger = logging.getLogger('tickers.area1')


class TickerScraper():
    """Download tickers from yahoo finance into a list"""

    def __init__(self, wait_time:int):
        """
        :wait_time:time in seconds for Selenium's wait option for handling operations such as
        waiting for element to be visible on the website.
        """
        logger.warning('Stared program tickers.py')
        self.wait_time = wait_time
        self.gathered_tickers_list = []    

        # SELENIUM SETTINGS 
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("detach", True)
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, wait_time)

        
    def get_base_url(self, sha:str, offset:int=0) -> str:
        """
        Gets the base url based on SHA and offset. 

        :sha: SHA is created for specific filters such as country and stock exchange.  
        :offset: the purpose is pagination.
        :return: url with sha as string.
        """
        base_url = f"https://finance.yahoo.com/screener/unsaved/{sha}?count=100&dependentField=sector&dependentValues=&offset={offset}"
        logger.warning(base_url)
        return base_url
    
    def go_to_base_url(self, sha:str):
        """
        It goes to base url and accepts cookies
        """

        def accept_cookie():
            """
            It clicks accept button for cookie confirmation.
            """ 
            cookie_button_accept_xpath = "//button[@class='btn primary']"
            self.wait.until(EC.visibility_of_element_located((By.XPATH, cookie_button_accept_xpath)))
            self.driver.find_element("xpath", cookie_button_accept_xpath).click()

        self.driver.get(self.get_base_url(sha))
        accept_cookie()

    def check_how_many_stocks(self) -> int:
        """This function looks for how many stocks links are available on Yahoo Finance page, 
        and returns integer with information how many links are per page
        
        :return: number of how many stocks is for selected filter (based on SHA), hence how many tickers to get.
        """
        how_many_stocks_xpath = "//div[@class='Fw(b) Fz(36px)']"
        self.wait.until(EC.visibility_of_element_located((By.XPATH, how_many_stocks_xpath)))
        how_many_stocks = self.driver.find_element("xpath", how_many_stocks_xpath).text
        logger.warning(f"number of sites to paginate: {int(int(how_many_stocks)/100)}")
        return int(int(how_many_stocks)/100)

    def get_tickers_to_list(self):
        """
        Gets list of ticker links, and updated to the main list of __init__ method (an general output)
        """

        def append_ticker_if_doesnt_exists_in_gathered_data(ticker, list_of_downloaded_tickers:list, i:int):
            if ticker not in list_of_downloaded_tickers:
                 list_of_downloaded_tickers.append(ticker)
                 logger.warning(f"{i}. {ticker.split('=')[1]} has been added to the ticker's list.")
            else:
                logger.warning(f"{i}. {ticker.split('=')[1]} was in the ticker's list.")


        tickers_xpath = "//a[contains(@data-test, 'quoteLink' )]"
        how_many_tickers_per_site = len(self.driver.find_elements("xpath", tickers_xpath))
        logger.warning(f"how_many_tickers_per_site: {how_many_tickers_per_site}")

        for i in range(1, (int(how_many_tickers_per_site)+1), 1):
            ticker = self.driver.find_element("xpath", f'({tickers_xpath})[{i}]').get_attribute('href')
            append_ticker_if_doesnt_exists_in_gathered_data(ticker=ticker, 
                                                            list_of_downloaded_tickers=self.gathered_tickers_list, 
                                                            i=i)
        
        logger.warning(f"{'='*10}\nGathered {len(self.gathered_tickers_list)} tickers so far.")

    def save_tickers_data(self):
        """
        It saves ticker links to pickle file as list. 
        """
        save_pickle_tickers_file = open('tickers.pkl', 'wb')
        pickle.dump(self.gathered_tickers_list, save_pickle_tickers_file)
        save_pickle_tickers_file.close()

    def quit(self):
        """
        It ends the Selenium's session.
        """ 
        self.driver.quit()

    def restore_tickers_data(self):
        """
        It checks if there is a pickle file, where previous data are held. If so,
        it upgrades the main list (which at the end is an output).
        """ 
        if os.path.isfile('tickers.pkl'):
            self.restore_tickers_file = pickle.load(open('tickers.pkl','rb'))
            self.gathered_tickers_list = self.restore_tickers_file
            return True
        else:
            return False


    def main(self, sha:str):
        """Core instructions"""

        self.restore_tickers_data()
        self.go_to_base_url(sha=sha)
        self.check_how_many_stocks()
        self.get_tickers_to_list()

        offset_total = self.check_how_many_stocks()
        for offset in range(100, (offset_total*100)+100, 100):
            logger.warning(f"{'='*10}\nPage number {int(offset/100)+1} is being downloaded.")
            self.driver.get(self.get_base_url(sha, offset))
            self.get_tickers_to_list()
            self.save_tickers_data()
        logger.warning(f"{'='*10}\nGathered tickers in total: {len(self.gathered_tickers_list)}")
        self.quit()





