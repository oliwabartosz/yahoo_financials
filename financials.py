from main import *
from datetime import date


logging.basicConfig(filename='financials.log', filemode='w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

class FinancialScraper:

    def __init__(self, wait_time:int):
        logging.warning('Stared program financials.py')
        self.wait_time = wait_time
        self.financial_data = {}

        # SELENIUM SETTINGS 
        options = Options()
        #options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("detach", True)
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, wait_time)

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
            
    def get_tickers_links(self):
        if os.path.isfile('tickers.pkl'):
            self.tickers_quotes = pickle.load(open('tickers.pkl','rb'))
            return self.tickers_quotes
        else:
            logging.warning("No tickers.pkl file.")
            return False

    def transform_tickers_links_to_financial_statments_links(self):
        pass

    def expand_all_data_in_tables(self):
        expand_all_data_xpath ="//*[starts-with(text(),'Expand All')]"
        try:
            self.wait.until(EC.visibility_of_element_located((By.XPATH, expand_all_data_xpath)))
            self.driver.find_element("xpath", expand_all_data_xpath).click()
            logging.warning("'Expand all' clicked.")
        except TimeoutException as e:
            print("The table is already expanded.")
        return True

    def generate_xpaths_for_financial_data(self, list_with_finacial_positions_to_generate:list, 
                                            income_statement:bool=False,
                                            balance_sheet:bool=False,
                                            cash_flow:bool=False,
                                            ):
        positions_with_xpath_dict = {}
        income_statement_xpath = "//a//span[text()='Income Statement']"
        balance_sheet_xpath = "//a//span[text()='Balance Sheet']"
        cash_flow_xpath = "//a//span[text()='Cash Flow']"

        def xpath_generator():
            for financial_position in list_with_finacial_positions_to_generate:
                positions_with_xpath_dict.update({financial_position.replace(" ","_"): 
                f"//span[@class='Va(m)' and text()='{financial_position}']"})
        
        def click_on_financial_statement_link(xpath:str):
            print("CLICKING:", xpath)
            self.driver.find_element("xpath", xpath).click()
            self.wait.until(EC.visibility_of_element_located((By.XPATH, "(//span[@class='Va(m)'])[last()]")))
            #time.sleep(10)
            print('CLICKED:', xpath)
            return True
        
        if income_statement == True:
            self.expand_all_data_in_tables()
            xpath_generator()
        elif balance_sheet == True:
            click_on_financial_statement_link(balance_sheet_xpath)
            self.expand_all_data_in_tables()
            xpath_generator()
        elif cash_flow == True:
            click_on_financial_statement_link(cash_flow_xpath)
            self.expand_all_data_in_tables()
            xpath_generator()

        return positions_with_xpath_dict
   
    def check_if_exists_in_base_by_date(self):
        pass
    
    def grab_financials_data(self):

        def accept_cookie():
            cookie_button_accept_xpath = "//button[@class='btn primary']"
            self.wait.until(EC.visibility_of_element_located((By.XPATH, cookie_button_accept_xpath)))
            try:
                self.driver.find_element("xpath", cookie_button_accept_xpath).click()
                logging.warning("Cookies accepted.")
                return True
            except TimeoutException as e:
                return False
        

                        
        def grab_financial_data_for_ticker():
            
            ############ teraz połącz balance sheet i cashflows
            _financial_data = {}
            date_of_download = date.today().strftime("%m/%d/%Y")

            def how_many_columns_in_table():
                how_many_columns_in_table = len(self.driver.find_elements("xpath","//div[@class='D(tbr) C($primaryColor)']/div"))
                return how_many_columns_in_table
            

            def grap_financial_data_for_specific_statement(range_end):
                
                for i in range(2, range_end+1, 1):
                    for key, value in xpaths_dict.items():
                        try:
                            financial_value = self.driver.find_element("xpath", f"{value}/../../../div[{i}]").text
                        except NoSuchElementException:
                            continue
                        date_of_statement = self.driver.find_element("xpath", f"//span[text()='Breakdown']/../../div[{i}]").text
                    
                        if date_of_statement != "TTM":
                            month_and_year = f"{date_of_statement.split('/')[0]}_{date_of_statement.split('/')[2]}"
                        else:
                            month_and_year = "TTM"
                            
                        _financial_data.update({"Date_of_download":date_of_download})
                        _financial_data.update({"Date_of_statment":date_of_statement})
                        _financial_data.update({f"{key}|{month_and_year}":financial_value})

            # INCOME STATEMENT
            xpaths_dict = self.generate_xpaths_for_financial_data(self.income_statement_positions_list, 
                                                                    income_statement=True)
            how_many_columns = how_many_columns_in_table()
            grap_financial_data_for_specific_statement(range_end=how_many_columns)

            # BALANCE SHEET
            xpaths_dict = self.generate_xpaths_for_financial_data(self.balance_sheet_positions_list, 
                                                                    balance_sheet=True)
            how_many_columns = how_many_columns_in_table()
            grap_financial_data_for_specific_statement(range_end=how_many_columns)


            xpaths_dict = self.generate_xpaths_for_financial_data(self.cash_flow_positions_list, 
                                                                    cash_flow=True)
            how_many_columns = how_many_columns_in_table()                                                       
            grap_financial_data_for_specific_statement(range_end=how_many_columns)
            
            return _inancial_data

        self.driver.get('https://finance.yahoo.com/quote/HLX/financials?p=HLX') 
        #self.driver.get('https://finance.yahoo.com/quote/BCE/financials?p=BCE')     
        accept_cookie()
        self.financial_data.update(grab_financial_data_for_ticker())

    def main(self):
        self.get_tickers_links()
        self.check_if_exists_in_base_by_date()
        self.grab_financials_data()
        print(self.financial_data)

grab_data = FinancialScraper(wait_time=5)
grab_data.main()