from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
import time
import sqlite3
from sqlite3 import Error
from datetime import datetime

def create_connection(db_file):
    """
    create a database connection to the SQLite database
    specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
        raise e

    return conn

def initialize_database(db_connection):
    sql_create_data_table = """ CREATE TABLE IF NOT EXISTS radiodata (
                                        DateTimeUTC text PRIMARY KEY,
                                        TempCelcius num,
                                        SessionStatus text,
                                        ReceivePower num DEFAULT 0,
                                        SignalStrengthRatio num DEFAULT 0,
                                        SignaltoNoiseRatio num DEFAULT 0,
                                        Beacons NUM DEFAULT 0
                                    ); """
    if db_connection is not None:
        try:
            c = db_connection.cursor()
            c.execute(sql_create_data_table)
        except Error as e:
            print(e)
            raise e
    else:
        print("Attempted to initialize a non-existant database.")
        raise Exception()

def create_webdriver(address, isHeadless=True):
    driver = None
    options = Options()
    options.headless = isHeadless
    try:
        driver = webdriver.Firefox(options=options)
        return driver
    except Exception as e:
        print(e)
        raise e

    return driver

def scrape_radio_data(driver):
    data = []
    data.append(driver.find_elements(By.XPATH, '/html/body/div[3]/div[2]/div[2]/table/tbody/tr[10]')) # Date and time
    data.append(driver.find_elements(By.XPATH, '/html/body/div[3]/div[2]/div[2]/table/tbody/tr[17]')) # Session Status
    data.append(driver.find_elements(By.XPATH, '/html/body/div[3]/div[2]/div[3]/table/tbody/tr[1]')) # Temp
    data.append(driver.find_elements(By.XPATH, '/html/body/div[3]/div[2]/div[3]/table/tbody/tr[9]')) # receive power
    data.append(driver.find_elements(By.XPATH, '/html/body/div[3]/div[2]/div[3]/table/tbody/tr[10]')) # Signal strength
    data.append(driver.find_elements(By.XPATH, '/html/body/div[3]/div[2]/div[3]/table/tbody/tr[11]')) # Signal/Noise Ratio
    data.append(driver.find_elements(By.XPATH, '/html/body/div[3]/div[2]/div[3]/table/tbody/tr[13]')) # Beacons
    return data

def data_formatter(data):
    formatted_data = [[None, None] for i in range(len(data))]
    for i in range(len(data)):
        formatted_data[i] = data[i][0].text.split('\n')
        formatted_data[i][0] = formatted_data[i][0].replace(' :', '')
        formatted_data[i][0] = formatted_data[i][0].replace(' ', '')
    formatted_data[0][1] = formatted_data[0][1][:-4]
    # Reformat the date and time to be in Year/Month/Day Hour:Min:Sec format
    temp_date = datetime.strptime(formatted_data[0][1], "%H:%M:%S %m/%d/%Y")
    formatted_data[0][1] = temp_date.strftime("%Y/%m/%d %H:%M:%S")
    # Get only the Celcius number from the temp field
    formatted_data[1][1] = formatted_data[1][1].split()[0]
    # get only the number from the receive power field
    formatted_data[3][1] = formatted_data[3][1].split()[0]
    # get only the number from the Signal strength field
    formatted_data[4][1] = formatted_data[4][1].split("d")[0]
    # get only the number from the Signal/Noise Ratio field
    formatted_data[5][1] = formatted_data[5][1].split()[0]
    # get only the number from the Beacons field and convert to a value between 0 and 1
    formatted_data[6][1] = int(formatted_data[6][1].split()[0])/100.0

    return formatted_data

def main():
    db = create_connection('radio_data.db')
    initialize_database(db)
    address = "http://192.198.25.1"
    driver = create_webdriver(address)
    driver.get(address)
    while(True):
        time.sleep(2)
        data = scrape_radio_data(driver)
        data = data_formatter(data)
        table_values = []
        for element in data:
            table_values.append(element[1])
        db.execute("INSERT INTO radiodata VALUES (?, ?, ?, ?, ?, ?, ?)", table_values)
        db.commit()
        driver.refresh()
    db.close()

if __name__ == '__main__':
    main()
