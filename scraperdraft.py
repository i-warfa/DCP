from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains


from time import sleep
import urllib.request
import json
import os
import shutil
import uuid
import pandas as pd
import boto3
from sqlalchemy import create_engine


# Reminder to Update all Doc-String including info on sub-functions called within a main-function.


class ScanScraper:
    
    """ A Web Scraper Class which collects data on Nvidia RTX 3060 Graphics Cards.
        Contains all the functions that will navigate the webpage, extract product information and store the information either locally or on the cloud.
    """

    def __init__(self, landing_page_url: str = "https://www.scan.co.uk"):

        options = Options()
        options.add_argument("--headless") # Runs Chrome in headless mode.
        options.add_argument('--disable-gpu')  # applicable to windows os only.
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument('--no-sandbox') # Bypass OS security model.
        options.add_argument("--disable-logging") # Disables all logs.
        options.add_argument("--window-size=1920,1080") # Sets the Width and Height of chrome window.
        options.add_argument('start-maximized') # Maximises Window.
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36')
        options.add_argument("--disable-extensions")
        options.add_argument('disable-infobars')
    
        service = Service(executable_path=ChromeDriverManager().install())
        
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.get(landing_page_url)
        
        # self.driver.get_screenshot_as_file("screenshot.png") # Helps with Diagnostics when issue occurs running scraper in headless mode.
        
        print("\nWeb Scraper initiated. Web Driver executable is now running.\n")
        
    def scrape_site(self):

        """ This method collates all the public and protected functions in the scraper class and calls each of the function.
            It is the main methodthat operates the scraper.
        """
        
        self.__accept_cookies()
        self.__navigate_to_3060_cards()
        self.__in_stock_3060_cards()
        self.__data_collection()
        self.__initiate_psql_database()
        self._quit_driver()


    def __accept_cookies(self, xpath: str = "//div[@class='inner']//button"):
        
        """ Automatically accepts webpage cookies."""
        
        try:
            sleep(2)
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath)))
            self.driver.find_element(By.XPATH, xpath).click()
        except TimeoutException:
            print("No Cookies Found!")
    

    def __navigate_to_3060_cards(self):
    
        """ Automates all the actions that will navigate to the webpage to display all the Graphics Card listings. 
            Returns the URL of the Webpage.
        """
        
        try:
            sleep(1)
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//div[@class='menuLevel2']//span[contains(text(),'Components')]")))
            self.driver.find_element(By.XPATH, "//div[@class='menuLevel2']//span[contains(text(),'Components')]").click()
        except TimeoutException:
            raise Exception("Could not click components tab")

        try:
            sleep(1)
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//a[normalize-space()='GPU - NVIDIA Gaming']")))
            self.driver.find_element(By.XPATH, "//a[normalize-space()='GPU - NVIDIA Gaming']").click()
        except TimeoutException:
            raise Exception("Could not redirect to Nvidia Graphics Cards Family page!")
        
        try:
            sleep(1)
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.LINK_TEXT, "GeForce RTX 3060 (3584 Cores)")))
            self.driver.find_element(By.LINK_TEXT, "GeForce RTX 3060 (3584 Cores)").click()
            # self.driver.find_element(By.XPATH, "//label[@for='filterInStock']").click()
        except TimeoutException:
            raise Exception("Could not redirect to RTX 3060 Graphics Cards page!")
        return self.driver.current_url


    def __in_stock_3060_cards(self):
        
        """ Returns a list of links for all the in-stock graphics on the webpage."""
        
        sleep(1)
        try:
            container = self.driver.find_element(By.XPATH, "(//ul[@class='productColumns'])")
            # Alternative Web Element to get 'container': 
            # container = self.driver.find_element(By.XPATH, "//div[@class='productsCont productList list']//ul[@class='productColumns']")
        except NoSuchElementException:
            container = self.driver.find_element(By.XPATH, "//body/div/div[@role='main']/div/div/div/div/div/ul[1]")

        list_of_3060_cards = container.find_elements(By.XPATH, './li')
        # list of the out of stock cards that are 'hidden web elements':
        hidden_products = self.driver.find_elements(By.XPATH, "//li[contains(@data-price, '999999.00')]")
        
        # list of the in-stock cards obtained by comparing the 2 lists above and returning non-matching elements:
        in_stock_3060_cards = []
        for i in list_of_3060_cards:
            if i not in hidden_products:
                in_stock_3060_cards.append(i)
        
        print(f"\nThere are {len(in_stock_3060_cards)} cards in stock")
        
        # list of links for the in-stock cards obtained by extracting the 'href' via <a> of the web elements:
        in_stock_list_of_links_for_3060 = []
        for rtx_3060 in in_stock_3060_cards:
            in_stock_list_of_links_for_3060.append(rtx_3060.find_element(By.TAG_NAME, 'a').get_attribute('href'))
        
        # self.driver.get_screenshot_as_file("screenshot2.png")
        
        return in_stock_list_of_links_for_3060


    def __make_folder(self):
        
        global root_dir, raw_data

        """ Creates a 'raw-data' folder in the directory to store product information, 
            if it has not been created already.
        """
        
        root_dir = os.getcwd()
        raw_data = os.path.join(root_dir, 'raw_data')
        is_raw_data_there = os.path.exists(raw_data)

        if is_raw_data_there == True:
            shutil.rmtree(raw_data)
        else:
            os.makedirs(raw_data)

        # return self.raw_data


    def __aws_s3_client(self):

        """ Create a low-level client with the service name."""
        
        self.s3 = boto3.client('s3')
        self.s3_client = boto3.Session().client(service_name='s3')


    def __data_collection(self):
        
        """ Scrapes Product Name, SKU, Unique ID, Price, Webpage Link and Product Image for each product entry.
            Stores each product entry in a 'raw-data' folder locally and uploads it to an AWS S3 Bucket.
        """
        
        self.__make_folder()
        # self.raw_data = self.__make_folder()
        list_of_links_for_3060 = self.__in_stock_3060_cards()
        self.product_list = []
        
        self.__aws_s3_client()
        
        # Loops through each product and scrapes product details. 
        # Saves details locally in a 'raw_data' folder and uploads the folder to aws s3 bucket.
        for link in list_of_links_for_3060[0:len(list_of_links_for_3060)]:

            indv_product_dictionary = {
                'SKU': [],
                'Product Name': [],
                'Unique ID': [],
                'Price (£)': [],
                'Link': [],
                'Product Image URL': []
            }

            self.driver.get(link)
            sleep(1)
            indv_product_dictionary['Link'].append(link)

            # Get Product SKU/Friendly ID:
            try:
                sku = self.driver.find_element(By.XPATH, "(//strong[@itemprop='sku'])[1]")
                indv_product_dictionary['SKU'].append(sku.text)
            except NoSuchElementException:
                indv_product_dictionary['SKU'].append('N/A')
            
            # Get Product Name:
            try:
                product_name = self.driver.find_element(By.XPATH, "//h1[@itemprop='name']")
                indv_product_dictionary['Product Name'].append(product_name.text)
            except NoSuchElementException:
                indv_product_dictionary['Product Name'].append('N/A')

            # Generate UUID (Unique):
            try:
                unique_id = uuid.uuid4()
                str(unique_id)
                indv_product_dictionary['Unique ID'].append(str(unique_id))
            except:
                indv_product_dictionary['Unique ID'].append('N/A')

            # Get Image URL:
            try:
                element = self.driver.find_element(By.XPATH, "//img[@class='zoomable-image'][1]")
                image_url = element.get_attribute('src')
                indv_product_dictionary['Product Image URL'].append(image_url)
            except NoSuchElementException:
                indv_product_dictionary['Product Image URL'].append('N/A')

            # Get Item Price:
            try:
                price = self.driver.find_element(By.XPATH, "(//span[@class='price'])[4]")
                price = str(price.text)
                indv_product_dictionary['Price (£)'].append(price.strip('£'))
            except NoSuchElementException:
                indv_product_dictionary['Price (£)'].append('N/A')

            # append each product dictionary to a list.
            self.product_list.append(indv_product_dictionary)

            # Create a folder for each product entry, named after its SKU.
            product_entries = os.path.join((root_dir), (raw_data), f"{(sku.text)}")
            os.makedirs(product_entries)
            with open(f'{product_entries}\data.json', 'w', encoding='utf-8') as fp:
                json.dump(indv_product_dictionary, fp, ensure_ascii=False)
            
            # Create an 'images' Folder for each product image.
            images_folder = os.path.join(product_entries, "images")
            os.makedirs(images_folder)
            
            # Overcome 'HTTPError: HTTP Error 403: Forbidden' error code by modifying 'user-agent' variable that is sent with the request.
            opener=urllib.request.build_opener()
            opener.addheaders=[('User-Agent','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36')]
            urllib.request.install_opener(opener)
            urllib.request.urlretrieve(image_url, f'{images_folder}\{sku.text}.jpg')
            
            sleep(1)

            # Upload individual data.json files to the corresponding product folder at the s3 bucket destination
            # e.g. : "s3://scanscraperbucket/raw_data/product_entry_1/"
            # Format as such:  s3_client.upload_file(file_name, bucket, s3_object_name)
            self.s3.upload_file(f'{product_entries}\data.json', 'scanscraperbucket', f'raw_data/{sku.text}/data.json')


            # Upload individual product images to an 'Images' folder at the s3 bucket destination 
            # e.g. : "s3://scanscraperbucket/raw_data/product_entry_1/Images/"
            # Format as such:  s3_client.upload_file(file_name, bucket, s3_object_name)
            self.s3.upload_file(f'{images_folder}\{sku.text}.jpg', 'scanscraperbucket', f'raw_data/{sku.text}/images/{sku.text}.jpg')


        # Export the file containing all the GPU Product Data to a Json File and save within 'raw_data' Folder.
        # Should be at the same directory level as the individual product entries
        # Rememebr the 'product_list' variable contains all the individual products details as a list variable.
        with open(f'{raw_data}/raw_data.json', 'w', encoding='utf-8') as f:
            json.dump(self.product_list, f, ensure_ascii=False)
        
        # Upload said Json file to s3 bucket.
        # Format as such:  s3_client.upload_file(file_name, bucket, s3_object_name)
        self.s3.upload_file(f'{raw_data}/raw_data.json', 'scanscraperbucket', 'raw_data/raw_data.json')

        # Does Number of sub-folder created equal to the number of products scraped?
        self.product_folder_count = len(next(os.walk(raw_data))[1])
        print(f"\n{self.product_folder_count} sub-folders have been created within the 'raw_data' folder of the root directory\n")

        # Transform the GPU Product List into a Panda DataFrame for AWS RDS Database storage.
        self.product_list_df = pd.DataFrame(self.product_list)    
        print(f"{self.product_list_df}")
        
        return self.product_folder_count


    def __initiate_psql_database(self):
        
        """ Configures & Initiates the connection to the AWS RDS PostgreSQL Database.
            Uploads the scraped product data to the database.
        """

        DATABASE_TYPE = 'postgresql'
        DBAPI = 'psycopg2'
        ENDPOINT = "scanscraperdb.cbq5lslbgwez.us-east-1.rds.amazonaws.com" # Change it for your AWS endpoint
        USER = 'postgres'
        PASSWORD = "cinnamon"
        PORT = 5432
        DATABASE = 'postgres'

        engine = create_engine(f"{DATABASE_TYPE}+{DBAPI}://{USER}:{PASSWORD}@{ENDPOINT}:{PORT}/{DATABASE}")
        engine.connect()
        
        # Upload product list dataframe to PostgreSQL database.
        self.product_list_df.to_sql('gpu_products_data_set', engine, if_exists='replace')

    
    def _quit_driver(self):
            
            """ Closes the browser and quits the webdriver executable."""

            sleep(4)
            self.driver.quit()
            print("\nEnd of session. Web Scraper is terminated. Webdriver excutable is no longer running.\n")



if __name__ == '__main__':
    scraper = ScanScraper()
    scraper.scrape_site()

