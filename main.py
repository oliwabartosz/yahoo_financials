#!venv/bin/python

from turtle import clear
from prices_and_tickers_links import PricesAndTickerLinksScraper
from financials import FinancialScraper
from gurufocus import DividendScraper
# from gurufocus import logger_1
import argparse

args_sources = ['Y', 'G']
args_whats = ['T', 'P']

parser = argparse.ArgumentParser(
    description='Download data from Yahoo or Gurufocus')
subparser = parser.add_subparsers(dest='command')
yahoo = subparser.add_parser('yahoo')
gurufocus = subparser.add_parser('gurufocus')

yahoo.add_argument('-t', '--tickers', action='store_true',
                   help="Download tickers links from Yahoo")
yahoo.add_argument('-p', '--prices', action='store_true',
                   help="Download prices from Yahoo")
yahoo.add_argument('-f', '--financial', action='store_true',
                   help='Download financial data from Yahoo')
yahoo.add_argument('-c', '--clear_log', action='store_true',
                   help='Deletes log files.')
gurufocus.add_argument('-d', '--dividends', action='store_true',
                       help='Download dividends from GuruFocus')
gurufocus.add_argument('-c', '--clear_log',
                       action='store_true', help='Deletes log files.')

args = parser.parse_args()

if __name__ == '__main__':
    if args.command == 'yahoo':
        if args.prices:
            prices = PricesAndTickerLinksScraper(
                log_name='prices.area',
                pickle_filename='prices.pkl',
                log_filename='prices.log'
            )
            prices.get_tickers_and_prices()
        elif args.tickers:
            tickers_links = PricesAndTickerLinksScraper(
                log_name='tickers_links.area',
                pickle_filename='tickers.pkl',
                log_filename='tickers.log'
            )

            tickers_links.get_tickers_links()

        # elif args.tickers and args.clear_log:
        #         tickers_links = PricesAndTickerLinksScraper(
        #         log_name='tickers_links.area',
        #         pickle_filename='tickers.pkl',
        #         log_filename='tickers.log',
        #         clear_log=True
        #     )

        elif args.financial:
            financial_data = FinancialScraper(check_data_by_date=True)
            financial_data.main()

    elif args.command == 'gurufocus':
        if args.dividends:
            dividends = DividendScraper(time_delta=0)
            dividends.main()
        if args.clear_log:
            dividends = DividendScraper(time_delta=0, clear_log=True)
