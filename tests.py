import unittest
from financials import FinancialScraper
from main import *


class TestTickersScraper(unittest.TestCase):
    pass

class TestFinancials(unittest.TestCase):

    def test_get_tickers_links_if_there_is_input_file(self):
        self.assertTrue(FinancialScraper.get_tickers_links(self))
    
    def test_get_tickers_links_if_there_is_not_input_file(self):
        
        def rename_files(name1, name2):
            os.rename(name1,name2)
            print(f"changed name to {name2}" if f"{name2}" in os.listdir() else f"couldn't change {name1} to {name2}")

        rename_files('tickers.pkl','tickers_.pkl')
        self.assertFalse(FinancialScraper.get_tickers_links(self))
        rename_files('tickers_.pkl','tickers.pkl')
    


if __name__ == '__main__':
    unittest.main()