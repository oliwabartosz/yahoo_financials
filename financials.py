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
            
    def get_tickers_links(self):
        if os.path.isfile('tickers.pkl'):
            self.tickers_quotes = pickle.load(open('tickers.pkl','rb'))
            return self.tickers_quotes
        else:
            logging.warning("No tickers.pkl file.")
            return False

    def transform_tickers_links_to_financial_statments_links(self):
        pass

    def generate_xpaths_for_financial_data(self):
        positions_with_xpath_dict = {}
                                            # 'Total Assets',
	                                        # 'Current Assets',
	                                        # 'Total non-current assets',
	                                        # 'Current Liabilities',
	                                        # 'Total Debt',
	                                        # 'Net Debt',
	                                        # 'Ordinary Shares Number',
        list_with_finacial_positions_to_generate = [
                                            'Total Revenue', 
                                            'Diluted EPS',
                                            'Total Expenses',
                                            'EBIT', 
                                            ]

        for financial_position in list_with_finacial_positions_to_generate:
            positions_with_xpath_dict.update({financial_position.replace(" ","_"): 
                                            f"//span[@class='Va(m)' and text()='{financial_position}']"})
        
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
        
        def expand_all_data_in_tables():
            expand_all_data_xpath ="//*[starts-with(text(),'Expand All')]"
            self.wait.until(EC.visibility_of_element_located((By.XPATH, expand_all_data_xpath)))
            self.driver.find_element("xpath", expand_all_data_xpath).click()
            logging.warning("'Expand all' clicked.")
            return True
                
        def grab_financial_data_for_ticker():
            
            ############ teraz połącz balance sheet i cashflows
            financial_data = {}
            date_of_download = date.today().strftime("%m/%d/%Y")

            xpaths_dict = self.generate_xpaths_for_financial_data()
            for i in range(2, 7, 1):
                for key, value in xpaths_dict.items():
                    financial_value = self.driver.find_element("xpath", f"{value}/../../../div[{i}]").text
                    date_of_statement = self.driver.find_element("xpath", f"//span[text()='Breakdown']/../../div[{i}]").text
                   
                    if date_of_statement != "TTM":
                        month_and_year = f"{date_of_statement.split('/')[0]}_{date_of_statement.split('/')[2]}"
                    else:
                        month_and_year = "TTM"
                        
                    financial_data.update({"Date_of_download":date_of_download})
                    financial_data.update({"Date_of_statment":date_of_statement})
                    financial_data.update({f"{key}|{month_and_year}":financial_value})

            return financial_data

        
        self.driver.get('https://finance.yahoo.com/quote/HLX/financials?p=HLX')     
        accept_cookie()
        expand_all_data_in_tables()
        self.financial_data.update(grab_financial_data_for_ticker())

    def main(self):
        self.get_tickers_links()
        self.check_if_exists_in_base_by_date()
        self.grab_financials_data()
        print(self.financial_data)

grab_data = FinancialScraper(wait_time=5)
grab_data.main()