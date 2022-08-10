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
import pandas as pd
import requests
import re
import datetime
import shutil
import glob
import time
import logging

from datetime import date


logging.basicConfig(filename='financials.log', filemode='w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

class FinancialScraper:

    def __init__(self, wait_time:int):
        logging.warning('Stared program financials.py')
        self.wait_time = wait_time
        

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

        :return: it returns a list with tickers from coverted links
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
            logging.warning("No tickers.pkl file.")
            return _tickers

    def accept_cookie(self) -> bool:
        cookie_button_accept_xpath = "//button[@class='btn primary']"
        try:
            self.wait.until(EC.visibility_of_element_located((By.XPATH, cookie_button_accept_xpath)))
            self.driver.find_element("xpath", cookie_button_accept_xpath).click()
            print("Cookies accepted.")
            logging.warning("Cookies accepted.")
            return True
        except TimeoutException as e:
            print("Cookies confirmation not needed.")
            logging.warning("Cookies confirmation not needed.")
            return False

    def expand_all_data_in_tables(self):
        expand_all_data_xpath ="//*[starts-with(text(),'Expand All')]"
        try:
            self.wait.until(EC.visibility_of_element_located((By.XPATH, expand_all_data_xpath)))
            self.driver.find_element("xpath", expand_all_data_xpath).click()
            print("'Expand all' clicked.")
            logging.warning("'Expand all' clicked.")
        except TimeoutException as e:
            logging.warning("The table is already expanded.")
            print("The table is already expanded.")
        return True

    def click_on_financial_statement_link(self, xpath:str) -> bool:
        try:
            logging.warning(f"CLICKING: {xpath}")
            print("CLICKING:", xpath)
            self.driver.find_element("xpath", xpath).click()
            self.wait.until(EC.visibility_of_element_located((By.XPATH, "(//span[@class='Va(m)'])[last()]")))
            logging.warning(f"CLICKED: {xpath}")
            print('CLICKED:', xpath)
            return True
        except TimeoutException as e:
            logging.warning(f'Error: {e}. Probably no data for that ticker.')
            return False

    def restore_finacials_data(self):
        if os.path.isfile('financials.pkl'):
            self.restore_financials_file = pickle.load(open('financials.pkl','rb'))
            self.financial_data = self.restore_financials_file
            logging.warning("Financials data has been restored from .pkl file.")
            return True
        else:
            logging.warning("Financials data has not been restored from .pkl file. There's no such file.")
            return False

    def quit(self):
        self.driver.quit()


    def get_xpaths_for_financial_data(self, list_with_finacial_positions_to_generate:list, 
                                            income_statement:bool=False,
                                            balance_sheet:bool=False,
                                            cash_flow:bool=False,
                                            ) -> dict:
        """
        It downloads the texts of 

        Example:
        https://finance.yahoo.com/quote/BCE/?p=BCE -> BCE

        :return: it returns a list with tickers from coverted links
        """                         

        positions_with_xpath_dict = {}
        income_statement_xpath = "//a//span[text()='Income Statement']"
        balance_sheet_xpath = "//a//span[text()='Balance Sheet']"
        cash_flow_xpath = "//a//span[text()='Cash Flow']"


        def xpath_generator():
            for financial_position in list_with_finacial_positions_to_generate:
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

        def save_finacials_data_to_file() -> pickle:
            save_pickle_financials_file = open('financials.pkl', 'wb')
            pickle.dump(self.financial_data, save_pickle_financials_file)
            save_pickle_financials_file.close()
            logging.warning("Saved data to financials.pkl")
            
        def check_if_data_has_been_downloaded_before(ticker_to_check):

            def check_date() -> str:
                last_date_xpath = "//span[text()='Breakdown']/../../div[3]"
                print('Checking the last date')
                logging.warning(f'Checking the last date')
                self.driver.get(f'https://finance.yahoo.com/quote/{ticker_to_check}/financials?p={ticker_to_check}')
                self.accept_cookie()
                self.wait.until(EC.visibility_of_element_located((By.XPATH, last_date_xpath)))
                last_date = self.driver.find_element("xpath", last_date_xpath).text
                last_date = f"{last_date.split('/')[0]}_{last_date.split('/')[2]}"
                print(f'Last date check: {last_date}')
                logging.warning(f'Last date check:{last_date}')
                return last_date

            is_financials_pkl = self.restore_finacials_data()
            if is_financials_pkl == False:
                pass
            else:
                filtered_list = list(filter(lambda d: d['Ticker'] == ticker_to_check, self.financial_data))
                if not filtered_list:
                    print(f'{ticker_to_check}: Item does not exists')
                    logging.warning(f'{ticker_to_check}: Item does not exists')
                    return False
                else:
                    last_date = check_date()
                    if last_date in  filtered_list[0]["Month_and_year_of_data"]:
                        print("There is a data point for last statement's date")
                        return True

        def get_financial_data_for_ticker(ticker) -> dict:
            
            _financial_data = {}
            date_of_download = date.today().strftime("%m/%d/%Y")

            def how_many_columns_in_table() -> int:
                how_many_columns_in_table = len(self.driver.find_elements("xpath","//div[@class='D(tbr) C($primaryColor)']/div"))
                return how_many_columns_in_table
                        
            def get_financial_data_for_specific_statement(range_end, ticker):
                logging.warning(f"Downloading data for: {ticker}")
                months_and_years_list = []

                for i in range(2, range_end+1, 1):
                    for key, value in xpaths_dict.items():
                        try:
                            financial_value = self.driver.find_element("xpath", f"{value}/../../../div[{i}]").text
                        except NoSuchElementException:
                            logging.warning(f"{key} / Error: NoSuchElementException, line: 237")
                            continue

                        date_of_statement = self.driver.find_element("xpath", f"//span[text()='Breakdown']/../../div[{i}]").text
                        if date_of_statement != "TTM":
                            month_and_year = f"{date_of_statement.split('/')[0]}_{date_of_statement.split('/')[2]}"
                        else:
                            month_and_year = "TTM"
                        months_and_years_list.append(month_and_year)
                        
                        _financial_data.update({"Ticker":ticker})
                        _financial_data.update({"Month_and_year_of_data":list(set(months_and_years_list))})
                        _financial_data.update({"Date_of_download":date_of_download})
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
        for ticker in _tickers_list:
            check_if_data_exists = check_if_data_has_been_downloaded_before(ticker_to_check=ticker)
            if not check_if_data_exists:
                print(f"Downloading ticker: {ticker}")
                logging.warning(f"Downloading ticker: {ticker}")
                self.driver.get(f'https://finance.yahoo.com/quote/{ticker}/financials?p={ticker}') 
                self.accept_cookie()
                self.financial_data.append(get_financial_data_for_ticker(ticker))
                save_finacials_data_to_file()
            else:
                print(f'Skipping {ticker}.')
                logging.warning(f'Skipping {ticker}.')
                continue

    def main(self):
        self.restore_finacials_data()
        self.get_financials_data()
        self.quit()
        print(self.financial_data)

get_data = FinancialScraper(wait_time=5)
get_data.main()