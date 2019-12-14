# This file contains special formatiing function(s) to clean scraped data



def negativeValuesHandler(value):
    # This looks to replace paranthesis indicating a negative value ( in accounting representation)
    # It replaces the () with - 
    originalLength = len(value)
    value.strip('()')
    if len(value) < originalLength:
        value.strip('$')
        try:
            f_value = float(value)
            value = '-' + value
        except Exception as e:
            print(f'not a number : {e}')
    else:
        value.strip('$')

def generateUrls(base_url,config='./Input JC Account Numbers.csv'):
    # Read account numbers from config file and generate URLs to be scraped
    # Returns a list of valid, hopefully, URLs
    urls = []
    with open(config) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        err_count = 0
        for row in csv_reader:
            try:
                accntNum = float(row[0])
                url = base_url + row[0]
                urls.append(url)
            except Exception as e:
                print(f'Error parsing line for Account Number : {e}')
                err_count += 1
        print(f'Corrupt lines found : {err_count}')
        print(f'Found {len(urls)} usable lines ( Acc Nums ) !')

    return urls





base_url = http://taxes.cityofjerseycity.com/ViewPay?accountNumber=