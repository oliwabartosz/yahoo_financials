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
import logging

from datetime import date


logging.basicConfig(filename='financials.log', filemode='w', format='%(asctime)s - %(message)s', 
                    datefmt='%d-%b-%y %H:%M:%S')
console = logging.StreamHandler()
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger().addHandler(console)

logger = logging.getLogger('financials.area1')

class FinancialScraper:
    """Scraper of financial data from income statement, balance sheet and cashflow"""

    def __init__(self, wait_time:int, check_data_by_date:bool=True):
        """
        :wait_time:time in seconds for Selenium's wait option for handling operations such as
        waiting for element to be visible on the website.

        :check_data_by_date: a) if True, the last date of statement will be checked, and downloading data 
        will be skipped if the last date has been downloaded before, 
        and hence it is already in the pickle file (financials.pkl)
        b) if False, the data for all tickers will be downloaded again, 
        no matter the last statement date.
        """ 
        logger.info('Stared program financials.py')
        self.wait_time = wait_time
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

        self.financial_data = []
        self.income_statement_positions_list = [
                                            'Total Revenue', 
                                            'Diluted EPS',
                                            'Total Expenses',
                                            'EBIT', 
                                            ]
        self.balance_sheet_positions_list = [    
                                        'Total Assets',
	                                    'Current Assets',
	                                    'Total non-current assets',
	                                    'Current Liabilities',
	                                    'Total Debt',
	                                    'Net Debt',
	                                    'Ordinary Shares Number',
                                        ]
        self.cash_flow_positions_list = [ 
                                    'Operating Cash Flow',
                                    'Investing Cash Flow',
                                    'Financing Cash Flow',
                                    'Cash Dividends Paid',
                                    'Free Cash Flow',
                                    ]
            
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
            self.tickers_quotes = pickle.load(open('tickers.pkl','rb'))
            for ticker in self.tickers_quotes:
                ticker = ticker.split(re.findall(_ticker_regex, ticker)[0])[1]
                _tickers.append(ticker)
            return _tickers
        else:
            logger.warning("No tickers.pkl file.")
            return _tickers

    def accept_cookie(self) -> bool:
        """
        Checks if there is a popup with cookies. If so, it clicks accept button.
        """ 
        cookie_button_accept_xpath = "//button[@class='btn primary']"
        try:
            self.wait.until(EC.visibility_of_element_located((By.XPATH, cookie_button_accept_xpath)))
            self.driver.find_element("xpath", cookie_button_accept_xpath).click()
            logger.warning("Cookies accepted.")
            return True
        except TimeoutException as e:
            logger.warning("Cookies confirmation not needed.")
            return False

    def expand_all_data_in_tables(self):
        """
        To get necessary data clicking the link to expand tables is obligatory.
        """ 
        expand_all_data_xpath ="//*[starts-with(text(),'Expand All')]"
        try:
            self.wait.until(EC.visibility_of_element_located((By.XPATH, expand_all_data_xpath)))
            self.driver.find_element("xpath", expand_all_data_xpath).click()
            logger.warning("'Expand all' clicked.")
        except TimeoutException as e:
            logger.warning("The table is already expanded.")
        return True

    def click_on_financial_statement_link(self, xpath:str) -> bool:
        """
        This function clicks the links to specific statements for actual ticker (stock).
        """ 
        try:
            logger.warning(f"CLICKING: {xpath}")
            self.driver.find_element("xpath", xpath).click()
            self.wait.until(EC.visibility_of_element_located((By.XPATH, "(//span[@class='Va(m)'])[last()]")))
            logger.warning(f"CLICKED: {xpath}")

            return True
        except TimeoutException:
            logger.warning(f'Error: {TimeoutException}. Probably no data for that ticker.')
            return False

    def restore_finacials_data(self):
        """
        It checks if there is a pickle file, where previous data are held. If so,
        it upgrades the main list of dictionaries (which at the end is an output).
        """ 
        if os.path.isfile('financials.pkl'):
            self.restore_financials_file = pickle.load(open('financials.pkl','rb'))
            self.financial_data = self.restore_financials_file
            logger.warning("Financial data has been restored from .pkl file.")
            return True
        else:
            logger.warning("Financial data has not been restored from .pkl file. There's no such file.")
            return False

    def quit(self):
        """
        It ends the Selenium's session.
        """ 
        self.driver.quit()


    def get_xpaths_for_financial_data(self, list_with_financial_positions_to_generate:list, 
                                            income_statement:bool=False,
                                            balance_sheet:bool=False,
                                            cash_flow:bool=False,
                                            ) -> dict:
        """
        Generates a dictionary of positions in specific statement and their xpaths.

        :list_with_financial_positions_to_generate: a list from _init_ method, with names of categories to download.\n
        :income_statement: if True, the data are downloaded from Income Statement. balance_sheet and cash_flow attributes must be set to False.\n
        :balance_sheet: if True, the data are downloaded from Balance Sheet. income_statement and cash_flow attributes must be set to False.\n
        :cash_flow: :balance_sheet: if True, the data are downloaded from Balance Sheet. income_statement and balance_sheet attributes must be set to False.\n
        :return: a dictionary with position name and xpath eg.: "Total_Debt":"//span[@class='Va(m)' and text()='{"Total Debt"}'"
        """                         

        positions_with_xpath_dict = {}
        income_statement_xpath = "//a//span[text()='Income Statement']"
        balance_sheet_xpath = "//a//span[text()='Balance Sheet']"
        cash_flow_xpath = "//a//span[text()='Cash Flow']"


        def xpath_generator():
            """
            It generates xpaths from lists that are in __init__ method.
            """ 
            for financial_position in list_with_financial_positions_to_generate:
                positions_with_xpath_dict.update({financial_position.replace(" ","_"): 
                f"//span[@class='Va(m)' and text()='{financial_position}']"})
        
        if income_statement == True:
            self.expand_all_data_in_tables()
            xpath_generator()
        elif balance_sheet == True:
            self.click_on_financial_statement_link(balance_sheet_xpath)
            self.expand_all_data_in_tables()
            xpath_generator()
        elif cash_flow == True:
            self.click_on_financial_statement_link(cash_flow_xpath)
            self.expand_all_data_in_tables()
            xpath_generator()

        return positions_with_xpath_dict
      
    def get_financials_data(self):
        """
        A general function that collects the data. It has ... main function in it:
        -> save_financial_data_to_file - saves data from every iteration to pickle file.\n
        -> check_if_data_has_been_downloaded_before -> it checks if it is necessary to download data again taking date.\n
        -> get_financial_data_for_ticker -> get the data for specific ticker from income statement, balance sheet and cashflow.\n

        :return: it updates the list of dictionaries in __init_ method - a main output.
        """ 
        def save_financial_data_to_file() -> pickle:
            """
            Saves data from every iteration to pickle file.

            :return: it saves the list of dictionaries in __init_ method - a main output - into pickle file.
            """
            save_pickle_financials_file = open('financials.pkl', 'wb')
            pickle.dump(self.financial_data, save_pickle_financials_file)
            save_pickle_financials_file.close()
            logger.warning("Saved data to financials.pkl")
            
        def check_if_data_has_been_downloaded_before(ticker_to_check):
            """
            It checks by the last date of the statement, if the previously downloaded data are in the pickle file.

            :return: it returns True (data has been downloaded before) or False (data has not been downloaded before) 
            but can also return KeyError if the table for actual ticker is empty.
            """

            def get_last_date() -> str:
                """
                It gets the last date from the table with data on the website.
                
                :return: last date of the statement as str eg. "12_2021". Can return None if the table for actual ticker 
                is empty.
                """

                last_date_xpath = "//span[text()='Breakdown']/../../div[3]"
                logger.warning(f'Checking the last date for {ticker_to_check}')
                self.driver.get(f'https://finance.yahoo.com/quote/{ticker_to_check}/financials?p={ticker_to_check}')
                self.accept_cookie()
                try:
                    self.wait.until(EC.visibility_of_element_located((By.XPATH, last_date_xpath)))
                    last_date = self.driver.find_element("xpath", last_date_xpath).text
                    last_date = f"{last_date.split('/')[0]}_{last_date.split('/')[2]}"
                    logger.warning(f'Last date check:{last_date}')
                except TimeoutException:
                    logger.warning(f"Error finding the last available date of statement TimeoutException \
                                    Probably the table is empty for that ticker ({ticker_to_check}).")
                    last_date = None
                return last_date

            is_financials_pkl = self.restore_finacials_data()
            if is_financials_pkl == False:
                pass
            else:
                try:
                    filtered_list = list(filter(lambda d: d['Ticker'] == ticker_to_check, self.financial_data))
                    if not filtered_list:
                        logger.warning(f'{ticker_to_check}: Item does not exists')
                        return False
                    else:
                        if self.check_data_by_date == True:
                            last_date = get_last_date()
                            if last_date in filtered_list[0]["Month_and_year_of_data"]:
                                logger.warning("There is a data point for last statement's date")
                                return True
                        else:
                            return True
                except KeyError:
                    logger.warning(f'KeyError - there is no table for that ticker: {ticker_to_check}.')
                    return KeyError

        def get_financial_data_for_ticker(ticker) -> dict:
            """
            Collects data for one ticker.

            :return: a dictionary where key is financial position and value is collected amount, eg.
            {"Ticker": "BCE", "Total_Debt": 1000, ...}
            """
            _financial_data = {}
            date_of_download = date.today().strftime("%m/%d/%Y")

            def how_many_columns_in_table() -> int:
                """
                Checks how many columns is in the table for actual ticker.

                :return: the number of columns, eg. 4.
                """
                how_many_columns_in_table = len(self.driver.find_elements("xpath","//div[@class='D(tbr) C($primaryColor)']/div"))
                return how_many_columns_in_table

            def get_currency() -> str:
                """
                Gets information about what currency actual data are presented. 
                If there is no information the data is considered as USD.

                :result: currency as string, eg. "CAD".
                """
                try: 
                    currency_xpath = "//span/span[contains(text(), 'Currency in')]"
                    currency = self.driver.find_element("xpath", currency_xpath).text
                    currency = currency.split('.')[0].rsplit()[-1]
                except NoSuchElementException:
                    currency = 'USD'
                
                return currency
   
            def get_financial_data_for_specific_statement(range_end, ticker):
                """
                A sub function of a function get_financial_data_for_ticker. It updates the dictionary for actual ticker.
                """
                logger.warning(f"Downloading data for: {ticker}")
                months_and_years_list = []

                for i in range(2, range_end+1, 1):
                    ## range_end == 2 means that the table is empty.
                    if range_end == 2:
                        _financial_data.update({"Ticker":ticker})
                        _financial_data.update({"Date_of_download":date_of_download})
                    else:
                        for key, value in xpaths_dict.items():
                            try:
                                financial_value = self.driver.find_element("xpath", f"{value}/../../../div[{i}]").text
                            except NoSuchElementException:
                                logger.warning(f"{key} / Error: NoSuchElementException")
                                continue

                            date_of_statement = self.driver.find_element("xpath", f"//span[text()='Breakdown']/../../div[{i}]").text
                            if date_of_statement != "TTM":
                                month_and_year = f"{date_of_statement.split('/')[0]}_{date_of_statement.split('/')[2]}"
                            else:
                                month_and_year = "TTM"
                            months_and_years_list.append(month_and_year)

                            currency = get_currency()
                            
                            _financial_data.update({"Ticker":ticker})
                            _financial_data.update({"Month_and_year_of_data":list(set(months_and_years_list))})
                            _financial_data.update({"Date_of_download":date_of_download})
                            _financial_data.update({"Currency": currency})
                            _financial_data.update({f"{key}|{month_and_year}":financial_value})
                        

            # INCOME STATEMENT
            xpaths_dict = self.get_xpaths_for_financial_data(self.income_statement_positions_list, 
                                                                    income_statement=True)
            how_many_columns = how_many_columns_in_table()
            get_financial_data_for_specific_statement(range_end=how_many_columns, ticker=ticker)

            # BALANCE SHEET
            xpaths_dict = self.get_xpaths_for_financial_data(self.balance_sheet_positions_list, 
                                                                    balance_sheet=True)
            how_many_columns = how_many_columns_in_table()
            get_financial_data_for_specific_statement(range_end=how_many_columns, ticker=ticker)

            # CASHFLOW
            xpaths_dict = self.get_xpaths_for_financial_data(self.cash_flow_positions_list, 
                                                                    cash_flow=True)
            how_many_columns = how_many_columns_in_table()                                                       
            get_financial_data_for_specific_statement(range_end=how_many_columns, ticker=ticker)
            
            return _financial_data

        _tickers_list = self.get_tickers_links_and_covert_to_tickers()
        for ticker in _tickers_list[207:208]:
            check_if_data_exists = check_if_data_has_been_downloaded_before(ticker_to_check=ticker)
            if (not check_if_data_exists) or (check_if_data_exists != KeyError):
                logger.warning(f"Downloading ticker: {ticker}")
                self.driver.get(f'https://finance.yahoo.com/quote/{ticker}/financials?p={ticker}') 
                self.accept_cookie()
                self.financial_data.append(get_financial_data_for_ticker(ticker))
                save_financial_data_to_file()
            else:
                logger.warning(f'Skipping {ticker}.')
                continue

    def main(self):
        """
        A core function.
        """
        self.get_financials_data()
        self.quit()
        print(self.financial_data)

get_data = FinancialScraper(wait_time=5, check_data_by_date=True)
get_data.main()