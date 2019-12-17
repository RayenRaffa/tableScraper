import os
import sys
import csv
import pandas as pd
from pandas import ExcelWriter
from bs4 import BeautifulSoup
import urllib.request
import specialFormatter as sf


def extractTable(table,account,is_pay_table=False):
    output_rows = []
    try:
        table_rows = table.findAll('tr')
    except Exception as e:
        print(f'Error extracting table from {account} : {e}, skipped')
        return [], []
    headers = table_rows[0]
    # Extract table headers
    try:
        columns = headers.findAll('th')
        output_row = ['Account #']
        for column in columns:
            output_row.append(column.text.strip('\n\t$').strip())
        headers = output_row  
    except Exception as e:
        print(f'Error extracting table headers from {account} : {e}, skipped')
        headers = []


    # Extract Certificate Table content
    line_count = 0
    for table_row in table_rows[1:]:
        if is_pay_table and line_count > 20:
            break 
        try:
            columns = table_row.findAll('td')
        except Exception as e:
            print(f'Error extracting table content from {account} : {e}, skipped')
            return headers, []
        output_row = [account]
        for column in columns:
            value = sf.negativeValuesHandler(column.text.strip('\n\t$').strip())
            output_row.append(value)
        output_rows.append(output_row)
        line_count += 1

    return headers, output_rows



def extractRecords(row):
    fields = []
    try:
        data_spans = row.findAll('span')
        for span in data_spans:
            fields.append(span.text.strip(' \n\r'))
    except Exception as e:
        print(f'Error extracting table from {account} : {e}, skipped')
        return []
        
    return fields



def table_to_csv(headers,table_rows,out_file):
    if not os.path.exists(out_file):
        with open(out_file, 'a', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(headers)       
    with open(out_file, 'a', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(table_rows)

    return 0



def extractPaymentsTable(url,payments_table,out_dir='./out/'):
    #Extract Tax Details and Payments Table and write it to csv file
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    accnt_num = url.split('=')[-1]
    headers, output_rows = extractTable(payments_table,accnt_num,True)
    output_file = out_dir + 'PaymentsTable.csv'
    table_to_csv(headers,output_rows,output_file)
    print(f'Payments Table of Account {accnt_num} saved successfully')
    
    return 0



def extractCertificateTable(url,certif_table,out_dir='./out/'):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    
    accnt_num = url.split('=')[-1]
    headers, output_rows = extractTable(certif_table,accnt_num)
    output_file = out_dir + 'CertificateTable.csv'
    table_to_csv(headers,output_rows,output_file)   
    print(f'Certificate Table of Account {accnt_num} saved successfully')

    return 0



def extractMainRecord(url,tax_data, mainRecords):
    # Extract the main record from the page and store it in mainRecords
    # Extracting fields from each line
    # Line 1
    fields = extractRecords(tax_data[0])
    accnt_num = fields[0]
    blq = sf.negativeValuesHandler(fields[1]) 
    principal = sf.negativeValuesHandler(fields[2]).strip('$')
    # Line 2
    fields = extractRecords(tax_data[1])
    owner = fields[0]
    bank_code = fields[1]
    interest = sf.negativeValuesHandler(fields[2]).strip('$')
    # Line 3
    fields = extractRecords(tax_data[2])
    address = fields[0]
    deducitons = sf.negativeValuesHandler(fields[1])
    total = sf.negativeValuesHandler(fields[2]).strip('$')
    # Line 4
    fields = extractRecords(tax_data[3])
    city_state = fields[0]
    int_date = fields[1]
    # Line 5
    fields = extractRecords(tax_data[4])
    location = fields[0]
    l_pay_date = fields[1]


    record = [
        accnt_num,
        blq,
        owner,
        location,
        address,
        city_state,
        principal,
        interest,
        deducitons,
        total,
        int_date,
        l_pay_date,
        bank_code    
    ]
    mainRecords.append(record)
    print(f'Main Records of Account {accnt_num} extracted successfully')

    return mainRecords



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
        page_rows = tax_soup.findAll('div', attrs={'class':'row'})
        tax_data = page_rows[2:7]
        if len(page_rows) >= 15:
            tax_data.append(page_rows[7])
        tax_data.append(page_rows[-4])
    except Exception as e:
        accnt_num = url.split('=')[-1]
        print(f'Error fetching webpage from {accnt_num} : {e} : skipping ..')
        tax_data = None

    if(tax_data):
        #print(f'Debugging : {len(tax_data)}')
        mainRecords = extractMainRecord(url, tax_data, mainRecords)
        if (len(tax_data) == 7):
            # If Certificate Table is available on the page
            extractCertificateTable(url,tax_data[5],out_dir)
            extractPaymentsTable(url,tax_data[6],out_dir)
        else:
            extractPaymentsTable(url,tax_data[5],out_dir)

    if(log_dir):
        sys.stdout = old_stdout
        log_file.close()


    return mainRecords



def main(base_url,config='./Input JC Account Numbers.csv',out_dir='./out/',log_dir=None):
    if(log_dir):
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        old_stdout = sys.stdout
        log_file = open(log_dir+"scrape.log","a")
        sys.stdout = log_file

    if not os.path.exists(out_dir):
            os.makedirs(out_dir)

    mainRecords_headers = [
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
        "Bank Code"]

    urls = sf.generateUrls(base_url,config)
    line_count = 1
    # Debugging : scraping for the first 100 account numbers
    urls = urls[:30]
    mainRecords = []
    for url in urls:
        account = url.split('=')[-1]
        print(f'--> Fetching account {account} ..')
        mainRecords = scrape(url, mainRecords)
        print(f'{line_count*100/len(urls)}% complete. Fetching next account ..')
        line_count += 1

    mainRecords_file = out_dir + 'mainRecords.csv'
    table_to_csv(mainRecords_headers,mainRecords,mainRecords_file)
    print(f'Found {len(mainRecords)} valid records, saved data at {mainRecords_file}')

    if(log_dir):
        sys.stdout = old_stdout
        log_file.close()

    return 0

base_url = 'http://taxes.cityofjerseycity.com/ViewPay?accountNumber='

main(base_url)
#main(base_url,config='./test_config.csv')
