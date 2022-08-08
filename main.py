#!/usr/bin/env python3

from tickers import TickerScraper

if __name__ == '__main__':
    __SHA_USA__ = 'faebc1d6-b91c-41c4-a506-d2c6e6fc96a8'
    __SHA_CANADA__ = 'e6400abd-ea79-47e4-a637-fa0d6f928183'

    get_list_of_stocks_USA = TickerScraper(wait_time=5)
    get_list_of_stocks_USA.main(sha=__SHA_USA__)

    get_list_of_stocks_CANADA = TickerScraper(wait_time=5)
    get_list_of_stocks_CANADA.main(sha=__SHA_CANADA__)



