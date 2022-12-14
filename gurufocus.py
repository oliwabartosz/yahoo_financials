import pickle
import os
import re
import json
from time import sleep
import time
from datetime import datetime, timedelta
import config
from tqdm import tqdm

logger_1 = config.Logger.setup(name='gurufocus', file_name='dividends.log')


class DividendScraper:
    def __init__(self, time_delta: int = 0, check_data_by_date: bool = True, clear_log: bool = False):
        logger_1.info(f'Stared program gurufocus.py')
        self.dividend_data = []
        self.check_data_by_date = check_data_by_date
        self.timedelta = time_delta
        self.clear_log = clear_log
        logger_1.info(f'Timedelta set to {self.timedelta}')

        self.day = datetime.now() - timedelta(days=self.timedelta)
        self.day = self.day.strftime("%Y-%m-%d")

    def login(self) -> None:
        login_xpath = "//input[@id='login-dialog-name-input']"
        password_xpath = "//input[@id='login-dialog-pass-input']"

        with open('login.json') as login_file:
            login_data = json.load(login_file)

        login = login_data['login']
        password = login_data['password']

        def enter_login_and_pass(text: str, xpath: str):
            input_form = config.driver.find_element("xpath", xpath)
            input_form.send_keys(text)
            input_form.send_keys(config.Keys.ENTER)
            sleep(config.sleep_time)

        config.driver.get('https://www.gurufocus.com/login')
        logger_1.info(f"Opened login page")
        enter_login_and_pass(login, login_xpath)
        enter_login_and_pass(password, password_xpath)
        logger_1.info("Logged in.")

    def clear_log_files(self, files_to_delete: list):
        """ 
        Checks if clear_log is True. If it is, it deletes files specified in a list.

        file_to_delete: a list of files to delete
        """
        if self.clear_log:
            for file in files_to_delete:
                os.remove(file) if os.path.exists(file) == True else None
        else:
            pass

    def logout(self) -> None:
        logout_xpath = "//i[@class='p-r-md gfp-log-out']"
        logout = config.driver.find_element("xpath", logout_xpath)
        config.driver.execute_script("arguments[0].click();", logout)

    def get_tickers_links_and_convert_to_tickers(self) -> list:
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
            tickers_quotes = pickle.load(open('tickers.pkl', 'rb'))
            for ticker in tickers_quotes:
                ticker = ticker.split(re.findall(_ticker_regex, ticker)[0])[1]
                _tickers.append(ticker)
            return _tickers
        else:
            logger_1.info("No tickers.pkl file.")
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
            'BRK-A': 'NEOE:BRK',
            'BRK-B': 'NEOE:BRK',
            'BML': 'TSE:4694',
        }

        tickers_to_adjust = self.get_tickers_links_and_convert_to_tickers()
        if not tickers_to_adjust:
            logger_1.info(f"List with tickers is empty! Exiting.")
            self.quit()
            exit(1)
        else:
            for ticker in tickers_to_adjust:
                ticker_adjusted = re.sub('(-|\.)[A-Z]*', '', ticker)
                adjusted_tickers_dict.update({ticker: ticker_adjusted})
                adjusted_tickers_dict.update(tickers_exceptions)
            logger_1.info(
                "Dictionary with adjusted tickers to gurufocus has been generated.")

            # Removing duplicates in values
            temporary_dict = {val: key for key,
                              val in adjusted_tickers_dict.items()}
            duplicates_removed_dict = {
                val: key for key, val in temporary_dict.items()}
            adjusted_tickers_dict.update(duplicates_removed_dict)

            return adjusted_tickers_dict

    def check_last_download_date(self, ticker_to_check: str) -> bool:
        """
        Checks the last download date in previously downloaded data and if it is the same with a date given it returns True.
        The day is computed by subtracting the day of running program by specified timedelta. 

        :return: True if date is equal to the date of last download presented in previously downloaded data
        else False. 
        """
        try:
            filtered_list = list(filter(lambda d: (d['Ticker'] == ticker_to_check) & (
                d['Last_Download_date'] == self.day), self.dividend_data))
        except TypeError:
            return False
        except KeyError:
            return False
        if not filtered_list:
            logger_1.info(
                f'{ticker_to_check}: No data found (\'Last_Download_date\') == {self.day}. Downloading data.')
            return False
        else:
            logger_1.info(
                f'Last_Download_date is equal to set date {self.day}. Download skipped.')
            return True

    def download_dividend_data_from_given_ticker(self, ticker: str) -> list:
        """
        Downloads the data about dividends for specific ticker.

        :return: it returns a list with data for specific ticker. If error occurs it returns False.
        """
        self.ticker = ticker
        dividend_data_for_one_ticker = []

        def xpath_generator() -> dict:
            """It generates a dict of xpaths for downloading the data."""
            xpaths_to_download = ['Reported Currency', 'Reported Dividend',
                                  'Ex-Date', 'Record Date', 'Pay Date', 'Type', 'Frequency']
            xpath_to_download_dict = {xpath_name: f"//table[@class='data-table normal-table']//descendant::*[@data-column='{xpath_name}']"
                                      for xpath_name in xpaths_to_download}
            return xpath_to_download_dict

        def go_to_the_site(ticker: str = self.ticker):
            """
            It opens the chosen site.
            :ticker: a string that is specific ticker, taken from the main function ('download_dividend_data').
            """
            logger_1.info(
                f"Entering do https://www.gurufocus.com/stock/{ticker}/dividend")
            config.driver.get(
                f"https://www.gurufocus.com/stock/{ticker}/dividend")

        def check_if_stock_pays_dividend() -> bool:
            """
            Check if specific xpath exists and returns True or False.
            """
            check_xpath = "//strong[contains(text(),'does not pay dividend.')]"
            element_exist = True if len(config.driver.find_elements(
                "xpath", check_xpath)) > 0 else False
            if element_exist:
                logger_1.info(
                    f"check_if_stock_pays_dividend returned {element_exist}. Skipping that.")
            else:
                logger_1.info(
                    f"check_if_stock_pays_dividend returned {element_exist}. Getting the data.")
            return element_exist

        def how_many_pages() -> int:
            """
            This function looks for how many pages are available on GuruFocus' dividend website's table.
            It can return False to skip downloading specific ticker, especially when it doesn't exists.

            :return: a number of how many pages are in the table or False when TimeoutException occurs.
            """
            how_many_pages_xpath = "//div[@class='aio-tabs-item right-float']"
            try:
                config.wait.until(config.EC.visibility_of_element_located(
                    (config.By.XPATH, "//span[@class='t-label' and text()='/100']")))
            except config.TimeoutException:
                logger_1.info(f"Error: TimeoutException. Returning None")
                return None
            how_many_pages_str = config.driver.find_element(
                "xpath", how_many_pages_xpath).text
            logger_1.info(
                f"how_many_pages_int as string returned: {how_many_pages_str}")
            how_many_pages_int = int(how_many_pages_str.split()[1])
            if how_many_pages_int % 10 == 0:
                how_many_pages_int = how_many_pages_int // 10
            else:
                how_many_pages_int = (how_many_pages_int // 10) + 1

            if how_many_pages_int == 0:
                how_many_pages_int = 1

            logger_1.info(f"how_many_pages_int: {how_many_pages_int}")
            return how_many_pages_int

        def next_page_click(i: int):
            """
            It clicks the next page in table with dividends.
            """
            next_page_xpath = "//button[@class='btn-next']"
            config.wait.until(config.EC.visibility_of_element_located(
                (config.By.XPATH, next_page_xpath)))
            next_page = config.driver.find_element("xpath", next_page_xpath)
            config.driver.execute_script("arguments[0].click();", next_page)
            # config.wait.until(config.EC.element_to_be_clickable((config.By.XPATH, next_page_xpath)))
            # next_page.click()
            logger_1.info(f'Next page clicked (page no. {i})')

        def check_how_many_elements_in_table(check_xpath: str) -> int:
            """
            Check how many rows is in the table.

            :result: a number of rows in a table.
            """
            how_many_elements_in_table = len(
                config.driver.find_elements('xpath', check_xpath))
            logger_1.info(
                f"Found {how_many_elements_in_table} rows in a table to download.")
            return how_many_elements_in_table

        def check_last_Ex_Date(ticker_to_check: str) -> bool:
            """
            It take the Ex-Date value for first row in data table on the website for specific ticker,
            and compares it with the previously downloaded data.py

            :return: True, if the Ex-Date for Ticker has been found, otherwise False (empty list).
            """
            xpaths_data = xpath_generator()
            ex_date_xpath = xpaths_data['Ex-Date']
            try:
                last_ex_date = config.driver.find_element(
                    "xpath", ex_date_xpath).text
            except config.NoSuchElementException:
                # When it doesn't found a ticker this error occurs
                return False
            try:
                filtered_list = list(filter(lambda d: (d['Ticker'] == ticker_to_check) & (
                    d['Ex-Date'] == last_ex_date), self.dividend_data))
            except TypeError:
                return False
            if not filtered_list:
                logger_1.info(
                    f'{ticker_to_check}: No data found (\'Ex-date\'). Downloading data.')
                return False
            else:
                if last_ex_date in filtered_list[0]["Ex-Date"]:
                    logger_1.info(
                        f"{ticker_to_check}: Data is up to date. Skipping that ticker.")
                    return True
                logger_1.info(
                    'check_last_Ex_Date: Something went wrong. Returned None')

        def get_elements_from_one_page_from_table(page_no: int) -> list:
            """
            It downloads the data from the table of one page.

            :page_no: a number of page which is currently scraped.
            :return: a list with data from one page of the table
            """
            one_table_data_list = []

            xpaths_data = xpath_generator()
            how_many_rows_in_table = check_how_many_elements_in_table(
                xpaths_data['Reported Dividend'])

            for row in range(1, how_many_rows_in_table+1, 1):
                one_table_data_dict = {}
                for key, value in xpaths_data.items():
                    try:
                        value_text = config.driver.find_element(
                            "xpath", f"{value}[{row}]").text
                    except config.NoSuchElementException:
                        value_text = 'No column found'
                    logger_1.info(
                        f"Downloading the table: ticker: {ticker}, row: {row}, page: {page_no}, data: {key}: {value_text}")
                    one_table_data_dict.update({'Ticker': ticker,
                                                key: value_text,
                                                'Last_Download_date': time.strftime("%Y-%m-%d")
                                                })

                one_table_data_list.append(one_table_data_dict)

            return one_table_data_list

        go_to_the_site()
        if not check_if_stock_pays_dividend():
            how_many_pages_on_site = how_many_pages()
            check_last_download_date = self.check_last_download_date(
                ticker_to_check=ticker)
            if not check_last_download_date:
                check_if_data_exists = check_last_Ex_Date(
                    ticker_to_check=ticker)
                if how_many_pages_on_site == None:
                    return False
                elif check_if_data_exists == True or None:
                    return False
                else:
                    if how_many_pages_on_site == 1:
                        one_table_data_dict = get_elements_from_one_page_from_table(
                            page_no=1)
                        dividend_data_for_one_ticker.extend(
                            one_table_data_dict)
                        return dividend_data_for_one_ticker
                    else:
                        for page in range(1, how_many_pages_on_site+1, 1):
                            one_table_data_dict = get_elements_from_one_page_from_table(
                                page_no=page)
                            dividend_data_for_one_ticker.extend(
                                one_table_data_dict)
                            next_page_click(page)
                        return dividend_data_for_one_ticker
            else:
                return False

    def save_dividend_data_to_file(self) -> pickle:
        """
        Saves data from every iteration to pickle file.

        :return: it saves the list of dictionaries in __init__ method - a main output - into pickle file.
        """
        save_pickle_dividends_file = open('dividends.pkl', 'wb')
        pickle.dump(self.dividend_data, save_pickle_dividends_file)
        save_pickle_dividends_file.close()
        logger_1.info("Saved data to dividends.pkl")

    def restore_dividends_data(self):
        """
        It checks if there is a pickle file, where previous data are held. If so,
        it upgrades the main list of dictionaries (which at the end is an output).
        """
        if os.path.isfile('dividends.pkl'):
            self.restore_dividends_file = pickle.load(
                open('dividends.pkl', 'rb'))
            self.dividend_data = self.restore_dividends_file
            logger_1.info("Dividends data has been restored from .pkl file.")
            return True
        else:
            logger_1.info(
                "Dividends data has not been restored from .pkl file. There's no such file.")
            return False

    def quit(self):
        """
        It ends the Selenium's session.
        """
        config.driver.quit()

    def main(self):
        """
        A core function. It updates main dictionary with data (output)
        """
        attempt = config.rerun_attempt_load()
        logger_1.info(f'Running attempt no. {attempt}')
        try:
            self.clear_log_files(files_to_delete=['dividends.log'])
            self.restore_dividends_data()
            tickers = self.adjust_tickers_from_yahoo_to_gurufocus()
            # for ticker in list(tickers.values())[0:4]:
            self.login()
            for number, ticker in enumerate(tqdm(tickers.values())):
                is_last_download_day_equal_to_today = self.check_last_download_date(
                    ticker_to_check=ticker)
                if is_last_download_day_equal_to_today:
                    continue
                downloaded_data_list = self.download_dividend_data_from_given_ticker(
                    ticker=ticker)
                if downloaded_data_list == False:
                    continue
                else:
                    try:
                        self.dividend_data.extend(downloaded_data_list)
                    except TypeError:
                        # if there is no data for a ticker, it returns empty list (NoneType)
                        pass
                    self.save_dividend_data_to_file()
            self.logout()
            self.quit()
            config.rerun_attempt_save(0)
        except:
            attempt += 1
            config.rerun_attempt_save(attempt)
            if attempt == 1:
                logger_1.exception("Error. Rerunning.")
            os.system("python main.py gurufocus -d")
# https://www.gurufocus.com/stock/BML/dividend -> ERROR
