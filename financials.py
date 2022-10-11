import pickle
import os
import re
from datetime import date
import config
import logging

logger_1 = config.Logger.setup(name='finacials', file_name='financials.log')


class FinancialScraper:
    """Scraper of financial data from income statement, balance sheet and cashflow"""

    def __init__(self, wait_time: int, check_data_by_date: bool = True, clear_log: bool = False):
        """
        :wait_time:time in seconds for Selenium's wait option for handling operations such as
        waiting for element to be visible on the website.

        :check_data_by_date: a) if True, the last date of statement will be checked, and downloading data 
        will be skipped if the last date has been downloaded before, 
        and hence it is already in the pickle file (financials.pkl)
        b) if False, the data for all tickers will be downloaded again, 
        no matter the last statement date.
        """
        logger_1.info('Stared program financials.py')
        self.check_data_by_date = check_data_by_date
        self.clear_log = clear_log

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
            self.tickers_quotes = pickle.load(open('tickers.pkl', 'rb'))
            for ticker in self.tickers_quotes:
                ticker = ticker.split(re.findall(_ticker_regex, ticker)[0])[1]
                _tickers.append(ticker)
            return _tickers
        else:
            logger_1.warning("No tickers.pkl file.")
            return _tickers

    def accept_cookie(self) -> bool:
        """
        Checks if there is a popup with cookies. If so, it clicks accept button.
        """
        cookie_button_accept_xpath = "//button[@class='btn primary']"
        try:
            config.wait.until(config.EC.visibility_of_element_located(
                (config.By.XPATH, cookie_button_accept_xpath)))
            config.driver.find_element(
                "xpath", cookie_button_accept_xpath).click()
            logger_1.warning("Cookies accepted.")
            return True
        except config.TimeoutException as e:
            logger_1.warning("Cookies confirmation not needed.")
            return False

    def expand_all_data_in_tables(self):
        """
        To get necessary data clicking the link to expand tables is obligatory.
        """
        expand_all_data_xpath = "//*[starts-with(text(),'Expand All')]"
        try:
            config.wait.until(config.EC.visibility_of_element_located(
                (config.By.XPATH, expand_all_data_xpath)))
            config.driver.find_element("xpath", expand_all_data_xpath).click()
            logger_1.warning("'Expand all' clicked.")
        except config.TimeoutException as e:
            logger_1.warning("The table is already expanded.")
        return True

    def click_on_financial_statement_link(self, xpath: str) -> bool:
        """
        This function clicks the links to specific statements for actual ticker (stock).
        """
        try:
            logger_1.warning(f"CLICKING: {xpath}")
            config.driver.find_element("xpath", xpath).click()
            config.wait.until(config.EC.visibility_of_element_located(
                (config.By.XPATH, "(//span[@class='Va(m)'])[last()]")))
            logger_1.warning(f"CLICKED: {xpath}")

            return True
        except config.TimeoutException:
            logger_1.warning(
                f'Error: {config.TimeoutException}. Probably no data for that ticker.')
            return False

    def restore_finacials_data(self):
        """
        It checks if there is a pickle file, where previous data are held. If so,
        it upgrades the main list of dictionaries (which at the end is an output).
        """
        if os.path.isfile('financials.pkl'):
            self.restore_financials_file = pickle.load(
                open('financials.pkl', 'rb'))
            self.financial_data = self.restore_financials_file
            logger_1.warning(
                "Financial data has been restored from .pkl file.")
            return True
        else:
            logger_1.warning(
                "Financial data has not been restored from .pkl file. There's no such file.")
            return False

    def quit(self):
        """
        It ends the Selenium's session.
        """
        config.driver.quit()

    def get_xpaths_for_financial_data(self, list_with_financial_positions_to_generate: list,
                                      income_statement: bool = False,
                                      balance_sheet: bool = False,
                                      cash_flow: bool = False,
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
                positions_with_xpath_dict.update({financial_position.replace(" ", "_"):
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

            :return: it saves the list of dictionaries in __init__ method - a main output - into pickle file.
            """
            save_pickle_financials_file = open('financials.pkl', 'wb')
            pickle.dump(self.financial_data, save_pickle_financials_file)
            save_pickle_financials_file.close()
            logger_1.warning("Saved data to financials.pkl")

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
                logger_1.warning(
                    f'Checking the last date for {ticker_to_check}')
                config.driver.get(
                    f'https://finance.yahoo.com/quote/{ticker_to_check}/financials?p={ticker_to_check}')
                self.accept_cookie()
                try:
                    config.wait.until(config.EC.visibility_of_element_located(
                        (config.By.XPATH, last_date_xpath)))
                    last_date = config.driver.find_element(
                        "xpath", last_date_xpath).text
                    last_date = f"{last_date.split('/')[0]}_{last_date.split('/')[2]}"
                    logger_1.warning(f'Last date check:{last_date}')
                except config.TimeoutException:
                    logger_1.warning(f"Error finding the last available date of statement config.TimeoutException \
                                    Probably the table is empty for that ticker ({ticker_to_check}).")
                    last_date = None
                return last_date

            is_financials_pkl = self.restore_finacials_data()
            if is_financials_pkl == False:
                pass
            else:
                try:
                    filtered_list = list(
                        filter(lambda d: d['Ticker'] == ticker_to_check, self.financial_data))
                    if not filtered_list:
                        logger_1.warning(
                            f'{ticker_to_check}: Item does not exists')
                        return False
                    else:
                        if self.check_data_by_date == True:
                            last_date = get_last_date()
                            if last_date in filtered_list[0]["Month_and_year_of_data"]:
                                logger_1.warning(
                                    "There is a data point for last statement's date")
                                return True
                        else:
                            return True
                except KeyError:
                    logger_1.warning(
                        f'KeyError - there is no table for that ticker: {ticker_to_check}.')
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
                how_many_columns_in_table = len(config.driver.find_elements(
                    "xpath", "//div[@class='D(tbr) C($primaryColor)']/div"))
                return how_many_columns_in_table

            def get_currency() -> str:
                """
                Gets information about what currency actual data are presented. 
                If there is no information the data is considered as USD.

                :result: currency as string, eg. "CAD".
                """
                try:
                    currency_xpath = "//span/span[contains(text(), 'Currency in')]"
                    currency = config.driver.find_element(
                        "xpath", currency_xpath).text
                    currency = currency.split('.')[0].rsplit()[-1]
                except config.NoSuchElementException:
                    currency = 'USD'

                return currency

            def get_financial_data_for_specific_statement(range_end, ticker):
                """
                A sub function of a function get_financial_data_for_ticker. It updates the dictionary for actual ticker.
                """
                logger_1.warning(f"Downloading data for: {ticker}")
                months_and_years_list = []

                for i in range(2, range_end+1, 1):
                    # range_end == 2 means that the table is empty.
                    if range_end == 2:
                        _financial_data.update({"Ticker": ticker})
                        _financial_data.update(
                            {"Date_of_download": date_of_download})
                    else:
                        for key, value in xpaths_dict.items():
                            try:
                                financial_value = config.driver.find_element(
                                    "xpath", f"{value}/../../../div[{i}]").text
                            except config.NoSuchElementException:
                                logger_1.warning(
                                    f"{key} / Error: config.NoSuchElementException")
                                continue

                            date_of_statement = config.driver.find_element(
                                "xpath", f"//span[text()='Breakdown']/../../div[{i}]").text
                            if date_of_statement != "TTM":
                                month_and_year = f"{date_of_statement.split('/')[0]}_{date_of_statement.split('/')[2]}"
                            else:
                                month_and_year = "TTM"
                            months_and_years_list.append(month_and_year)

                            currency = get_currency()

                            _financial_data.update({"Ticker": ticker})
                            _financial_data.update(
                                {"Month_and_year_of_data": list(set(months_and_years_list))})
                            _financial_data.update(
                                {"Date_of_download": date_of_download})
                            _financial_data.update({"Currency": currency})
                            _financial_data.update(
                                {f"{key}|{month_and_year}": financial_value})

            # INCOME STATEMENT
            xpaths_dict = self.get_xpaths_for_financial_data(self.income_statement_positions_list,
                                                             income_statement=True)
            how_many_columns = how_many_columns_in_table()
            get_financial_data_for_specific_statement(
                range_end=how_many_columns, ticker=ticker)

            # BALANCE SHEET
            xpaths_dict = self.get_xpaths_for_financial_data(self.balance_sheet_positions_list,
                                                             balance_sheet=True)
            how_many_columns = how_many_columns_in_table()
            get_financial_data_for_specific_statement(
                range_end=how_many_columns, ticker=ticker)

            # CASHFLOW
            xpaths_dict = self.get_xpaths_for_financial_data(self.cash_flow_positions_list,
                                                             cash_flow=True)
            how_many_columns = how_many_columns_in_table()
            get_financial_data_for_specific_statement(
                range_end=how_many_columns, ticker=ticker)

            return _financial_data

        _tickers_list = self.get_tickers_links_and_covert_to_tickers()
        for ticker in _tickers_list[207:208]:
            check_if_data_exists = check_if_data_has_been_downloaded_before(
                ticker_to_check=ticker)
            if (not check_if_data_exists) or (check_if_data_exists != KeyError):
                logger_1.warning(f"Downloading ticker: {ticker}")
                config.driver.get(
                    f'https://finance.yahoo.com/quote/{ticker}/financials?p={ticker}')
                self.accept_cookie()
                self.financial_data.append(
                    get_financial_data_for_ticker(ticker))
                save_financial_data_to_file()
            else:
                logger_1.warning(f'Skipping {ticker}.')
                continue

    def main(self):
        """
        A core function.
        """
        attempt = config.rerun_attempt_load()
        logger_1.info(f'Running attempt no. {attempt}')

        try:
            self.clear_log_files(files_to_delete=['financials.log'])
            self.get_financials_data()
            self.quit()
        except:
            attempt += 1
            config.rerun_attempt_save(attempt)
            if attempt == 1:
                logger_1.exception("Error. Rerunning.")
            os.system("python main.py yahoo -f")
