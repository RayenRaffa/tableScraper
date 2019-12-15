import os
import csv
import pandas as pd
from pandas import ExcelWriter
from bs4 import BeautifulSoup
import urllib.request
import specialFormatter as sf


def extractTable(table,is_pay_table=False):
    output_rows = []
    table_rows = table.findAll('tr')
    headers = table_rows[0]
    # Extract table headers
    columns = headers.findAll('th')
    output_row = []
    for column in columns:
        output_row.append(column.text.strip('\n\t$').strip())
    output_rows.append(output_row)

    # Extract Certificate Table content
    line_count = 0
    for table_row in table_rows[1:]:
        if is_pay_table and line_count > 20:
            break 
        columns = table_row.findAll('td')
        output_row = []
        for column in columns:
            value = sf.negativeValuesHandler(column.text.strip('\n\t$').strip())
            output_row.append(value)
        output_rows.append(output_row)
        line_count += 1

    return output_rows



def extractRecords(row):
    fields = []
    data_spans = row.findAll('span')
    for span in data_spans:
        fields.append(span.text.strip(' \n\r'))

    return fields



def table_to_csv(table_rows,out_file):
    with open(out_file, 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(table_rows)

    return 0



def extractMainRecord(url,tax_data, mainRecords):
    # Extract the main record from the page and store it in mainRecords
    # Extracting fields from each line
    # Line 1
    fields = extractRecords(tax_data[0])
    accnt_num = fields[0]
    blq = sf.negativeValuesHandler(fields[1]) 
    principal = sf.negativeValuesHandler(fields[2])
    # Line 2
    fields = extractRecords(tax_data[1])
    owner = fields[0]
    bank_code = fields[1]
    interest = sf.negativeValuesHandler(fields[2])
    # Line 3
    fields = extractRecords(tax_data[2])
    address = fields[0]
    deducitons = sf.negativeValuesHandler(fields[1])
    total = sf.negativeValuesHandler(fields[2])
    # Line 4
    fields = extractRecords(tax_data[3])
    city_state = fields[0]
    int_date = fields[1]
    # Line 5
    fields = extractRecords(tax_data[4])
    location = fields[0]
    l_pay_date = fields[1]


    record = {
        "Account #": accnt_num,
        "B/L/Q": blq,
        "Owner": owner,
        "Location": location,
        "Address": address,
        "City / State": city_state,
        "Principal": principal,
        "Interest": interest,
        "Deductions": deducitons,
        "Total": total,
        "Int. Date": int_date,
        "L. Pay Date": l_pay_date,
        "Bank Code": bank_code    
    }
    mainRecords = mainRecords.append(record,ignore_index=True)
    print(f'Main Records of Account {accnt_num} extracted successfully')

    return mainRecords



def extractPaymentsTable(url,payments_table,out_dir):
    #Extract Tax Details and Payments Table and write it to csv file
    pay_table_dir = out_dir + 'PaymentsTables/'
    if not os.path.exists(pay_table_dir):
        os.makedirs(pay_table_dir)

    output_rows = extractTable(payments_table,True)
    accnt_num = url.split('=')[-1]
    output_file = pay_table_dir + accnt_num + '.csv'
    table_to_csv(output_rows,output_file)
    print(f'Payments Table of Account {accnt_num} saved successfully')
    
    return 0



def extractCertificateTable(url,certif_table,out_dir):
    certif_table_dir = out_dir + 'CertificateTables/'
    if not os.path.exists(certif_table_dir):
        os.makedirs(certif_table_dir)
    
    output_rows = extractTable(certif_table)
    accnt_num = url.split('=')[-1]
    output_file = certif_table_dir + accnt_num + '.csv'
    table_to_csv(output_rows,output_file)   
    print(f'Certificate Table of Account {accnt_num} saved successfully')

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
        print(f'Debugging : {len(tax_data)}')
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

    urls = sf.generateUrls(base_url,config)
    line_count = 1
    # Debugging : scraping for the first 100 account numbers
    urls = urls[:100]

    for url in urls:
        mainRecords = scrape(url, mainRecords)
        print(f'{line_count*100/len(urls)}% complete. Fetching next account ..')
        line_count += 1

    mainRecords_file = out_dir + 'mainRecords.csv'
    with open(mainRecords_file, 'w') as csv_file:
        mainRecords.to_csv(csv_file,index=False)
        print(f'Found {len(mainRecords.index)} valid records, saved data at {mainRecords_file}')

    if(log_dir):
        sys.stdout = old_stdout
        log_file.close()

    return 0

base_url = 'http://taxes.cityofjerseycity.com/ViewPay?accountNumber='

main(base_url)
