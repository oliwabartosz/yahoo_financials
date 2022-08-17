from xml.etree.ElementPath import xpath_tokenizer
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
import re
import time

import logging

from datetime import date


logging.basicConfig(filename='gurufocus.log', filemode='w', format='%(asctime)s - %(message)s', 
                    datefmt='%d-%b-%y %H:%M:%S')
console = logging.StreamHandler()
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger().addHandler(console)
logger = logging.getLogger('gurufocus.area1')

class DividendScraper:
    def __init__(self, wait_time:int):
        logger.warning(f'Stared program gurufocus.py')
        self.wait_time = wait_time
        self.dividend_data = []

        # SELENIUM SETTINGS 
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("detach", True)
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, wait_time)

    def get_tickers_links_and_covert_to_tickers(self) -> list:
        """
        It converts links for tickers downloaded by using tickers.py
        into tickers:

        Example:
        https://finance.yahoo.com/quote/BCE/?p=BCE -> BCE

        :return: it returns a list with tickers from converted links.
        """ 
        _tickers = []
        _ticker_regex = r"https:\/\/finance\.yahoo\.com\/quote\/[A-Z-.]+\?p="
        if os.path.isfile('tickers.pkl'):
            tickers_quotes = pickle.load(open('tickers.pkl','rb'))
            for ticker in tickers_quotes:
                ticker = ticker.split(re.findall(_ticker_regex, ticker)[0])[1]
                _tickers.append(ticker)
            return _tickers
        else:
            logger.warning("No tickers.pkl file.")
            return _tickers
    
    def adjust_tickers_from_yahoo_to_gurufocus(self) -> dict:
        """
        It takes the tickers from list and cut all unnecessary things (like dashes, etc.)
        to adjust to gurufocus tickers database.

        :return: a dictionary with tickers adjusted to gurufocus.
        Key is ticker from yahoo, value is from gurufocus, eg. ("BRK-A":"BRK")
        """
        adjusted_tickers_dict = {}
        tickers_exceptions = {
            'BRK-A':'NEOE:BRK',
            'BRK-B':'NEOE:BRK',
        }

        tickers_to_adjust = self.get_tickers_links_and_covert_to_tickers()
        if not tickers_to_adjust:
            logger.warning(f"List with tickers is empty! Exiting.")
            self.quit()
            exit(1)
        else:
            for ticker in tickers_to_adjust:
                ticker_adjusted = re.sub('(-|\.)[A-Z]*', '', ticker)
                adjusted_tickers_dict.update({ticker:ticker_adjusted})
                adjusted_tickers_dict.update(tickers_exceptions)
            logger.warning("Dictionary with adjusted tickers to gurufocus has been generated.")
            
            # Removing duplicates in values
            temporary_dict = {val:key for key, val in adjusted_tickers_dict.items()}
            duplicates_removed_dict = {val:key for key, val in temporary_dict.items()}
            adjusted_tickers_dict.update(duplicates_removed_dict)

            return adjusted_tickers_dict

    def download_dividend_data_from_given_ticker(self, ticker:str):
        """
        Downloads the data about dividends for specific ticker.
        """
        self.ticker = ticker
        _dividend_data = {}
        
        def xpath_generator() -> dict:
            """It generates a dict of xpaths for downloading the data."""
            xpaths_to_download = ['Reported Dividend','Ex-Date','Record Date','Pay Date','Type','Frequency']
            xpath_to_download_dict = {xpath_name:f"//table[@class='data-table normal-table']//tr/td[@data-column='{xpath_name}']" 
                                      for xpath_name in xpaths_to_download}

            return xpath_to_download_dict

        def go_to_the_site(ticker:str=self.ticker):
            """
            It opens the chosen site.
            :ticker: a string that is specific ticker, taken from the main function ('download_dividend_data').
            """
            logger.warning(f"Entering do https://www.gurufocus.com/stock/{ticker}/dividend")
            self.driver.get(f"https://www.gurufocus.com/stock/{ticker}/dividend")
            
        def check_if_stock_pays_dividend() -> bool:
            """
            Check if specific xpath exists and returns True or False.
            """
            check_xpath = "//strong[contains(text(),'does not pay dividend.')]"
            element_exist = True if len(self.driver.find_elements("xpath", check_xpath)) > 0 else False
            if element_exist:
                logger.warning(f"check_if_stock_pays_dividend returned {element_exist}. Skipping that.")
            else:
                logger.warning(f"check_if_stock_pays_dividend returned {element_exist}. Getting the data.")
            return element_exist

        def how_many_pages() -> int:
            """
            This function looks for how many pages are available on GuruFocus' dividend website's table.
            It can return False to skip downloading specific ticker, especially when it doesn't exists.
        
            :return: a number of how many pages are in the table or False when TimeoutException occurs.
            """
            how_many_pages_xpath = "//div[@class='aio-tabs-item right-float']"
            try:
                self.wait.until(EC.visibility_of_element_located((By.XPATH, "//span[@class='t-label' and text()='/100']")))
            except TimeoutException:
                logger.warning(f"Error: TimeoutException. Returning None")
                return None
            how_many_pages_str = self.driver.find_element("xpath", how_many_pages_xpath).text
            logger.warning(f"how_many_pages_int as string returned: {how_many_pages_str}")
            how_many_pages_int = int(how_many_pages_str.split()[1])
            if how_many_pages_int % 10 == 0:
                how_many_pages_int = how_many_pages_int // 10
            else:
                how_many_pages_int = (how_many_pages_int // 10) + 1

            if how_many_pages_int == 0:
                how_many_pages_int = 1

            logger.warning(f"how_many_pages_int: {how_many_pages_int}")
            return how_many_pages_int

        def next_page_click(i:int):
            """
            It clicks the next page in table with dividends.
            """
            next_page_xpath = "//i[@class='el-icon el-icon-arrow-right']"
            self.wait.until(EC.visibility_of_element_located((By.XPATH, next_page_xpath)))
            self.driver.find_element("xpath", next_page_xpath).click()
            logger.warning(f'Next page clicked (page no. {i+1})')
            
        go_to_the_site()
        if not check_if_stock_pays_dividend():
            how_many_pages_on_site = how_many_pages()
            if how_many_pages_on_site != None:
                xpaths_data = xpath_generator()

                if how_many_pages_on_site == 1:
                    _dividend_data.update({'Ticker':ticker})
                    for xpath_name, data in xpaths_data.items():
                        _dividend_data.update({xpath_name:self.driver.find_element("xpath", data).text})
                    return _dividend_data
                else:
                    _dividend_data.update({'Ticker':ticker})
                    for i in range(1, how_many_pages_on_site+1, 1):
                        for xpath_name, data in xpaths_data.items():
                            _dividend_data.update({xpath_name:self.driver.find_element("xpath", data).text})
                        next_page_click(i)
                    return _dividend_data
            else:
                return False
        else: 
            return False

    def quit(self):
        """
        It ends the Selenium's session.
        """ 
        self.driver.quit()

    def main(self):
        """
        A core function. It updates main dictionary with data (output)
        """
        tickers = self.adjust_tickers_from_yahoo_to_gurufocus()
        for ticker in tickers.values():
            downloaded_data_dict = self.download_dividend_data_from_given_ticker(ticker=ticker)
            if downloaded_data_dict == False:
                continue
            else:
                self.dividend_data.append(downloaded_data_dict)
                print(self.dividend_data)
        self.quit()

get_data = DividendScraper(wait_time=5)
get_data.main()