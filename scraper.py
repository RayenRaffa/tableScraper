import os
import csv
import pandas as pd
from pandas import ExcelWriter
from bs4 import BeautifulSoup
import urllib.request
import specialFormatter


def extractRecords(row):
    fields = []
    data_spans = row.findAll('span')
    for span in data_spans:
        fields.append(span.text)

    return fields



def extractTable(table,is_pay_table=False):
    output_rows = []
    table_rows = table.findAll('tr')
    headers = table_rows[0]
    # Extract table headers
    columns = headers.findAll('th')
    output_row = []
    for column in columns:
        output_row.append(column.text)
    output_rows.append(output_row)

    # Extract Certificate Table content
    line_count = 0
    for table_row in table_rows[1:]:
        if is_pay_table and line_count > 20:
            break 
        columns = table_row.findAll('td')
        output_row = []
        for column in columns:
            value = negativeValuesHandler(column.text)
            output_row.append(value)
        output_rows.append(output_row)
        line_count += 1

    return output_rows



def table_to_csv(table_rows,out_file):
    with open(out_file, 'wb') as csv_file:
        with csv.writer(csv_file) as writer:
        writer.writerows(table_rows)

    return 0



def extractMainRecord(url,tax_data, mainRecords):
    #Extract the main record from the page and store it in mainRecords
    

    return mainRecords



def extractPaymentsTable(url,payments_table,out_dir):
    #Extract Tax Details and Payments Table and write it to csv file
    pay_table_dir = out_dir + 'PaymentsTables/'
    if not os.path.exists(pay_table_dir):
        os.makedirs(pay_table_dir)

    output_rows = extractTable(payments_table)
    accnt_num = url.split('=')[-1]
    output_file = pay_table_dir + accnt_num + '.csv'
    table_to_csv(output_rows,output_file)   
    
    return 0



def extractCertificateTable(url,certif_table,out_dir):
    certif_table_dir = out_dir + 'CertificateTables/'
    if not os.path.exists(certif_table_dir):
        os.makedirs(certif_table_dir)
    
    output_rows = extractTable(certif_table)
    accnt_num = url.split('=')[-1]
    output_file = certif_table_dir + accnt_num + '.csv'
    table_to_csv(output_rows,output_file)   

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
        mainRecords = extractMainRecord(url,tax_data[0:4], mainRecords)
        extractPaymentsTable(url,tax_data[-1],out_dir)
        if (len(tax_data) == 7):
            # If Certificate Table is available on the page
            extractCertificateTable(url,tax_data[5],out_dir)




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