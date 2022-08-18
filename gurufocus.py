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
    def __init__(self, wait_time:int, check_data_by_date:bool=True):
        logger.warning(f'Stared program gurufocus.py')
        self.wait_time = wait_time
        self.dividend_data = []
        self.check_data_by_date = check_data_by_date

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

    def download_dividend_data_from_given_ticker(self, ticker:str) -> dict:
        """
        Downloads the data about dividends for specific ticker.

        :return: it returns dictionary with data for specific ticker. If error occurs it returns False.
        """
        self.ticker = ticker
        _dividend_data = {}
        
        def xpath_generator() -> dict:
            """It generates a dict of xpaths for downloading the data."""
            xpaths_to_download = ['Reported Dividend','Ex-Date','Record Date','Pay Date','Type','Frequency']
            xpath_to_download_dict = {xpath_name:f"//table[@class='data-table normal-table']//descendant::*[@data-column='{xpath_name}']" 
                                      for xpath_name in xpaths_to_download}
            # f"//table[@class='data-table normal-table']//tr/td[@data-column='{xpath_name}']"
            # //table[@class='data-table normal-table']//descendant::*[@data-column='Reported Currency']
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
            logger.warning(f'Next page clicked (page no. {i})')

        def check_how_many_elements_in_table(check_xpath:str) -> int:
            """
            Check how many rows is in the table.
    
            :result: a number of rows in a table.
            """
            # //table[@class='data-table normal-table']//tr/td[@data-column='Reported Dividend']/../../tr[position()=10]
            how_many_elements_in_table = len(self.driver.find_elements('xpath',check_xpath))
            logger.warning(f"Found {how_many_elements_in_table} rows in a table to download.")
            return how_many_elements_in_table

        def get_elements_from_one_page_from_table() -> dict:
            """
            It downloads the data from the table of one page.
            :return: a dictionary with data from one page of the table
            """
            one_table_data_list = []
            one_table_data_dict = {}

            how_many_rows_in_table = check_how_many_elements_in_table(xpaths_data['Reported Dividend'])
            counter = 0
            for row in range(1,how_many_rows_in_table+1,1):
                for xpath_name, data in xpaths_data.items():
                    xpath_with_row = f"{data}[{row}]"
                    one_table_data_dict.update({'Ticker':ticker+"_"+str(row),
                                                xpath_name:self.driver.find_element("xpath", xpath_with_row).text,
                                                "id":row,
                                                })
            
            return one_table_data_dict

        xpaths_data = xpath_generator()
        go_to_the_site()
        if not check_if_stock_pays_dividend():
            how_many_pages_on_site = how_many_pages()
            if how_many_pages_on_site == None:
                return False
            else:
                if how_many_pages_on_site == 1:
                    one_table_data_dict =  get_elements_from_one_page_from_table()
                else:
                    one_table_data_dict = get_elements_from_one_page_from_table()
                    print(one_table_data_dict)
                    _dividend_data.update(one_table_data_dict)



            
                


        # go_to_the_site()
        # if not check_if_stock_pays_dividend():
        #     how_many_pages_on_site = how_many_pages()
        #     if how_many_pages_on_site != None:
        #         xpaths_data = xpath_generator()
        #         if how_many_pages_on_site == 1:
        #             how_many_rows_in_table = check_how_many_elements_in_table(xpaths_data['Reported Dividend'])
        #             _dividend_data.update({'Ticker':ticker})
        #             for row in range(1,how_many_rows_in_table,1):
        #                 for xpath_name, data in xpaths_data.items():
        #                     xpath_row_position = f"{data}/../../tr[position()={row}]/td"
        #                     _dividend_data.update({xpath_name:self.driver.find_element("xpath", xpath_row_position).text})
        #                     _dividend_data.update({"id":row})
        #             return _dividend_data
        #         else: 
        #             for i in range(1, how_many_pages_on_site+1, 1):
        #                 how_many_rows_in_table = check_how_many_elements_in_table(xpaths_data['Reported Dividend'])
        #                 for row in range(1,how_many_rows_in_table+1,1):
        #                     #print(ticker+"_"+str(row*i))
        #                     for xpath_name, data in xpaths_data.items():
        #                         xpath_with_row = f"{data}[{row}]"
        #                         _dividend_data.update({'Ticker':ticker+"_"+str(row*i)})
        #                         _dividend_data.update({xpath_name:self.driver.find_element("xpath", xpath_with_row).text})
        #                         _dividend_data.update({"id":row*i})
        #                 next_page_click(i)
        #             return _dividend_data
        #     else:
        #         return False
        # else: 
        #     return False
    
    def save_dividend_data_to_file(self) -> pickle:
        """
        Saves data from every iteration to pickle file.

        :return: it saves the list of dictionaries in __init__ method - a main output - into pickle file.
        """
        save_pickle_dividends_file = open('dividends.pkl', 'wb')
        pickle.dump(self.dividend_data, save_pickle_dividends_file)
        save_pickle_dividends_file.close()
        logger.warning("Saved data to dividends.pkl")

    def restore_dividends_data(self):
        """
        It checks if there is a pickle file, where previous data are held. If so,
        it upgrades the main list of dictionaries (which at the end is an output).
        """ 
        if os.path.isfile('dividends.pkl'):
            self.restore_dividends_file = pickle.load(open('dividends.pkl','rb'))
            self.dividend_data = self.restore_dividends_file
            logger.warning("Dividends data has been restored from .pkl file.")
            return True
        else:
            logger.warning("Dividends data has not been restored from .pkl file. There's no such file.")
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
        self.restore_dividends_data()
        tickers = self.adjust_tickers_from_yahoo_to_gurufocus()
        for ticker in tickers.values():
            downloaded_data_dict = self.download_dividend_data_from_given_ticker(ticker=ticker)
            if downloaded_data_dict == False:
                continue
            else:
                self.dividend_data.append(downloaded_data_dict)
                self.save_dividend_data_to_file()
                print(self.dividend_data)
        self.quit()

get_data = DividendScraper(wait_time=5)
get_data.main()