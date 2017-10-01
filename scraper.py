# Enable future and backwards compatability:
from __future__ import absolute_import, division, generators, unicode_literals, print_function, nested_scopes, with_statement
from urllib.request import urlopen
import os
from bs4 import BeautifulSoup as BeautifulSoup
import pandas as pd

# =================================================================================================
# This script is for scrapping 10-K financial filing data from the SEC website
# =================================================================================================

# @Description: A method for getting a list of filing URLs and their respective years in a list.
# @Params: ticker (string) - Denotes which company we are collecting the URLs for
# @Returns: href (list) - Contains tuples of the report year and URL for each filing
def get_list(ticker):
  # Store the base URL components in variables
  base_url_part1 = "http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="
  base_url_part2 = "&type=&dateb=&owner=&start="
  base_url_part3 = "&count=100&output=xml"
  # The list where we will store the URLs and their respective lists
  href = []
  # Create a variable page_number that goes from 0 to 2000 at intervals of 100 this variable will
  # denote the page number that we land on in the base URL. Each page holds 100 examples which is
  # why we skip by intervals of 100
  for page_number in range(0, 2000, 100):
    # Construct the base URL
    base_url = base_url_part1 + ticker + \
        base_url_part2 + str(page_number) + base_url_part3
    # Open the page, scrape it and store it in sec_soup
    sec_page = urlopen(base_url)
    sec_soup = BeautifulSoup(sec_page, "lxml")
    # Find all the filings on the current page
    filings = sec_soup.findAll('filing')
    # For each filing with a filing type, 10-K and years after 2008, store the URL and respective
    # year
    for filing in filings:
      report_year = int(filing.datefiled.get_text()[0:4])
      if (filing.type.get_text() == "10-K") & (report_year > 2008):
        print(filing.filinghref.get_text())
        href.append((report_year, filing.filinghref.get_text()))

  return href

# @Description: A method for scraping and saving financial filings.
# @Params: data_list (list) - Contains tuples of the report year and URL for each filing
# @Params: dir_path (string) - The parent path where each filing will be saved
def download_report(data_list, dir_path):
  # base URL for scraping
  target_base_url = 'http://www.sec.gov'

  # Denotes the filing type. This is how we specify that we want to grab the .htm files on filing
  # page
  target_file_type = u'10-K'
  # Iterate through data_list and store each URL in data_list
  url_list = []
  for pair in data_list:
    print(pair)
    url_list.append(pair[1])
  # Iterate through url_list, find the page and scrape for the relevant filings
  for report_url in url_list:
    report_page = urlopen(report_url)
    report_soup = BeautifulSoup(report_page, "lxml")
    # Get each row on the page
    page_table = report_soup.findAll('tr')
    # Iterate through all the rows on the page and try to find the URL for the
    # .htm filing
    for item in page_table:
      try:
        # Get column elements in each row
        if item.findAll('td')[3].get_text() == target_file_type:
          htm_path = dir_path + "/full_html_filings"
          # See if we have the storage directory created
          if not os.path.exists(htm_path):
            os.makedirs(htm_path)
          # Get the link to filing xml
          target_url = target_base_url + \
              item.findAll('td')[2].find('a')['href']
          print("Target URL found!")
          print("Target URL is:", target_url)

          file_name = target_url.split('/')[-1]
          print(file_name)
          # Open the found URL and scrape
          htm_report = urlopen(target_url)
          path = os.path.join(htm_path, file_name)
          output = open(path, 'wb')
          output.write(htm_report.read())
          output.close()
          # Store individual tables for each filing
          result = [item for item in data_list if item[1] == report_url]
          report_year = result[0][0]
          print(report_year)
          # Create the path structure where we will store the tables for each
          # report
          table_base_path = dir_path + "/extracted_tables/" + str(report_year)
          # Grab each table from the filings and store them separately
          get_tables(path, table_base_path)
      except Exception as e:
        print(e)
        pass

# @Description: A method for extracting tables from each downloaded filing.
# @Params: file_path (string) - The location of the filing we are grabbing tables from
# @Params: table_base_path (string) - The parent path where each table will be saved
def get_tables(file_path, table_base_path):
  # grab htm file
  htm = open(file_path).read()
  # get all tables within htm file
  soup = BeautifulSoup(htm, "lxml")
  tables = soup.find_all("table")
  # Iterate through the tables list and save each table to its own file
  i = 1
  for table in tables:
    # print(table)
    if not os.path.exists(table_base_path):
      os.makedirs(table_base_path)

    file_name = "unclassified_table_" + str(i) + ".html"
    path = os.path.join(table_base_path, file_name)
    output = open(path, 'w')
    table = str(table)
    output.write(table)
    output.close()
    i += 1


# START
def main():
  # Import the ticker symbols from the CSV file of company filings that you want to 
  # scrape
  TickerFile = pd.read_csv("companylist.csv")
  tickers = TickerFile['Symbol'].tolist()
  # For each company in the ticker symbol list, run the following commands
  for ticker in tickers:
    # Run get_list() to obtain a list of filing URLs and year lists
    data_list = get_list(ticker)
    print(data_list)
    # Intialize the local directory for storing all scraped data
    base_path = "./filings_data"
    # Add the current company ticker symbol as a directory for clean separation
    dir_path = base_path + "/" + ticker
    # Run this to download and save the reports
    download_report(data_list, dir_path)

if __name__ == "__main__":
  main()
