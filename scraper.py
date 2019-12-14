import os
import csv
import pandas as pd
from pandas import ExcelWriter
from bs4 import BeautifulSoup
import urllib.request
import specialFormatter



def extractMainRecord(url,tax_data, mainRecords):
        #Extract the main record from the page and store it in mainRecords



def extractPaymentsTable(url,payments_data,out_dir):
    #Extract Tax Details and Payments Table and write it to csv file


def extractCertificateTable(url,certif_table,out_dir):
    certif_table_dir = out_dir + 'CertificateTables/'
    if not os.path.exists(certif_table_dir):
        os.makedirs(certif_table_dir)
    
    output_rows = []
    table_rows = table.findAll('tr')
    headers = table_rows[0]
    # Extract table headers
    columns = table_row.findAll('th')
    output_row = []
    for column in columns:
        output_row.append(column.text)
    output_rows.append(output_row)

    # Extract Certificate Table content
    for table_row in table_rows[1:]:
        columns = table_row.findAll('td')
        output_row = []
        for column in columns:
            value = negativeValuesHandler(column.text)
            output_row.append(value)
        output_rows.append(output_row)
    
    accnt_num = url.split('=')[-1]
    output_file = certif_table_dir + accnt_num + '.csv'
    with open(output_file, 'wb') as csv_file:
        with csv.writer(csv_file) as writer:
        writer.writerows(output_rows)

    return 0



def scrape(url,mainRecords, out_dir='./out/',log_dir=None):
    if(log_dir):
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        old_stdout = sys.stdout
        log_file = open(log_dir+"scrape.log","a")
        sys.stdout = log_file

    try:
        tax_page = urllib.request.urlopen(url)
        tax_soup = BeautifulSoup(tax_page, 'html.parser')
        tax_data = tax_soup.find_all('div', attrs={'class':'row'})
    except Exception as e:
        accnt_num = url.split('=')[-1]
        print(f'Error fetching webpage from {accnt_num} : {e} : skipping ..')
        tax_data = None

    if(len(tax_data) in range(6,8)):
        mainRecords = extractMainRecord(tax_data[0:4], mainRecords)
        extractPaymentsTable(tax_data[-1],out_dir)
        if (len(tax_data) == 7):
            # If Certificate Table is available on the page
            extractCertificateTable(tax_data[5],out_dir)




mainRecords = pd.DataFrame(columns=[
    "Account #",
    "B/L/Q",
    "Owner",
    "Location",
    "Address",
    "City / State",
    "Principal",
    "Interest",
    "Deductions",
    "Total",
    "Int. Date",
    "L. Pay Date",
    "Bank Code"])