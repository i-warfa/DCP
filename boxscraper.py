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
import requests
import mimetypes
import urllib.request
import json
import os
import shutil
import uuid
import shortuuid
import pandas as pd
import boto3
from sqlalchemy import create_engine


class BoxScraper():
    
    """ A Web Scraper Class which collects data on Nvidia RTX 3060 Graphics Cards.
        Contains all the functions that will navigate the webpage, extract product information and store the information either locally or on the cloud.
    """

    def __init__(self, landing_page_url: str = "https://www.box.co.uk"):

        options = Options()
        options.add_argument("--headless")
        options.add_argument('--disable-gpu')
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-logging")
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36')
        options.add_argument("--disable-extensions")
        options.add_argument('disable-infobars')
    
        service = Service(executable_path=ChromeDriverManager().install())
        
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_window_size(1920,1080)
        self.driver.maximize_window()

        self.actions = ActionChains(self.driver)
        
        self.driver.get(landing_page_url)
        sleep(27)
        
        # Helps with Diagnostics when issue occurs running scraper in headless mode.
        # self.driver.get_screenshot_as_file("screenshot1.png")

        # sleep(1)
        self.driver.refresh()
        sleep(1)
        self.driver.maximize_window()
        # self.driver.get_screenshot_as_file("screenshot2.png")

        print("\nWeb Scraper initiated. Web Driver executable is now running.\n")


    def scrape_site(self):

        """ This method collates all the public and protected functions in the scraper class and calls each of the function.
            It is the main methodthat operates the scraper.
        """
        
        self.__navigate_to_3060_cards()
        self.__list_of_3060_cards()
        self.__data_collection()
        self.__initiate_psql_database()
        self._quit_driver()


    def __navigate_to_3060_cards(self):
        
        """ Automatically accepts webpage cookies."""
        
        sleep(3)
        try:
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//a[normalize-space()='Computing']")))
            computing_tab = self.driver.find_element(By.XPATH, "//a[normalize-space()='Computing']")
            self.actions.move_to_element(computing_tab).perform()
        except TimeoutException:
            print("No computing tab found!")
        
        sleep(3)
        try:
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//a[normalize-space()='Components + Storage']")))
            components_and_storage = self.driver.find_element(By.XPATH, "//a[normalize-space()='Components + Storage']")
            self.actions.move_to_element(components_and_storage).perform()
        except TimeoutException:
            print("No component tab found!")
        
        sleep(1)
        # self.driver.get_screenshot_as_file("screenshot3.png")

        sleep(3)
        try:
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "(//a[contains(text(),'RTX 3060 Graphics Cards')])[1]")))
            product_3060_cards = self.driver.find_element(By.XPATH, "(//a[contains(text(),'RTX 3060 Graphics Cards')])[1]")
            self.actions.move_to_element(product_3060_cards).perform()
            self.actions.click(product_3060_cards).perform()
        except TimeoutException:
            print("No 3060 graphics product tab found!")
        
        sleep(1)
        # self.driver.get_screenshot_as_file("screenshot4.png")


    def __scroll_down(self):
        """A method for scrolling the page."""

        # Get scroll height.
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:

            # Scroll down to the bottom.
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load the page.
            sleep(3)

            # Calculate new scroll height and compare with last scroll height.
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:

                break

            last_height = new_height


    def __list_of_3060_cards(self):
        
        """ Returns a list of links for all the in-stock graphics on the webpage."""

        sleep(1)
        self.__scroll_down()

        list_of_3060_cards =  self.driver.find_elements(By.XPATH, "//div[@class='product-list p-small-list']//h3")
        
        print(f"\nThere are {len(list_of_3060_cards)} cards in stock")
        
        # list of links for  cards obtained by extracting the 'href' via <a> of the web elements:
        list_of_links_for_3060 = []
        for rtx_3060 in list_of_3060_cards:
            list_of_links_for_3060.append(rtx_3060.find_element(By.TAG_NAME, 'a').get_attribute('href'))
        
        return list_of_links_for_3060


    def __make_folder(self):
        
        global root_dir, raw_data

        """ Creates a 'raw-data' folder in the directory to store product information, 
            if it has not been created already.
        """
        
        root_dir = os.getcwd()
        raw_data = os.path.join(root_dir, 'raw_data')
        self.is_raw_data_there = os.path.exists(raw_data)

        if self.is_raw_data_there == True:
            shutil.rmtree(raw_data)
        else:
            os.makedirs(raw_data)


    def __aws_s3_client(self):

        """ Create a low-level client with the service name."""

        self.s3 = boto3.client('s3')    # self.s3_client = boto3.Session().client(service_name='s3')

        r = boto3.resource('s3')
        if not r.Bucket('boxscraperbucket').creation_date is None:
            bucket = r.Bucket('boxscraperbucket')
            bucket.objects.all().delete()


    def __data_collection(self):

        """ Scrapes Product Name, SKU, Unique ID, Price, Webpage Link and Product Image for each product entry.
            Stores each product entry in a 'raw-data' folder locally and uploads it to an AWS S3 Bucket.
        """
        
        self.__make_folder()
        self.__aws_s3_client()

        list_of_links_for_3060 = self.__list_of_3060_cards()

        if len(list_of_links_for_3060) >= 9:
            self.n = 9
        else:
            self.n = len(list_of_links_for_3060)
        
        self.product_list = []

        # Loops through each product and scrapes product details. 
        # Saves details locally in a 'raw_data' folder and uploads the folder to aws s3 bucket.
        for link in list_of_links_for_3060[0:self.n]:

            indv_product_dictionary = {
                'SKU': [],
                'Brand': [],
                'Product Name': [],
                'Unique ID': [],
                'Price (£)': [],
                'Link': [],
                'Product Image URL': []
            }
            
            self.driver.get(link)

            sleep(5)
            
            # Append link to dictionary:
            indv_product_dictionary['Link'].append(link)
            
            # Get SKU/Friendly ID:
            self.sku = shortuuid.uuid()
            indv_product_dictionary['SKU'].append(self.sku)
            
            # Get Product Brand and Name:
            try:
                product_brand = self.driver.find_element(By.XPATH, "(//span[@class='breadcrumb-item'][5]//span)").text
                indv_product_dictionary['Brand'].append(product_brand.text)
            except NoSuchElementException:
                indv_product_dictionary['Brand'].append('N/A')
            
            try:
                product_name = self.driver.find_element(By.XPATH, "//h2[@class='p-title-desc']")
                indv_product_dictionary['Product Name'].append(product_name.text)
            except NoSuchElementException:
                indv_product_dictionary['Product Name'].append('N/A')

            # Generate UUID (Unique):
            try:
                unique_id = uuid.uuid4()
                unique_id = str(unique_id)
                indv_product_dictionary['Unique ID'].append(str(unique_id))
            except:
                indv_product_dictionary['Unique ID'].append('N/A')

            # Get Image URL:
            try:
                self.image_url = self.driver.find_element(By.XPATH, "(//img[@class='p-image-button pq-images-small pq-images-show'])[1]").get_attribute('src')
                indv_product_dictionary['Product Image URL'].append(self.image_url)
            except NoSuchElementException:
                indv_product_dictionary['Product Image URL'].append('N/A')
    
            # Get Item Price:
            try:
                price = self.driver.find_element(By.XPATH, "(//span[@class='pq-price'])[1]")
                price = str(price.text)
                indv_product_dictionary['Price (£)'].append(price.strip('£'))
            except NoSuchElementException:
                indv_product_dictionary['Price (£)'].append('N/A')

            # append each product dictionary to a list.
            self.product_list.append(indv_product_dictionary)

            # Create a folder for each product entry, named after its SKU.
            product_entries = os.path.join((root_dir), (raw_data), f"{self.sku}")
            os.makedirs(product_entries)
            with open(f'{product_entries}\data.json', 'w', encoding='utf-8') as fp:
                json.dump(indv_product_dictionary, fp, ensure_ascii=False)


            # Create an 'images' Folder for each product image.
            images_folder = os.path.join(product_entries, "images")
            os.makedirs(images_folder)
            sleep(1)


            # Upload individual data.json files to the corresponding product folder at the s3 bucket destination.
            # Format as such:  s3_client.upload_file(file_name, bucket, s3_object_name)
            self.s3.upload_file(f'{product_entries}\data.json', 'boxscraperbucket', f'raw_data/{self.sku}/data.json')
            sleep(1)


            # Upload individual product images to an 'Images' folder at the s3 bucket destination 
            # e.g. : "s3://boxscraperbucket/raw_data/product_entry_1/Images/"
            # Format as such:  s3_client.upload_file(file_name, bucket, s3_object_name)
            # Overcome 'HTTPError: HTTP Error 403: Forbidden' error code by modifying 'user-agent' variable that is sent with the request.
            opener=urllib.request.build_opener()
            opener.addheaders=[('User-Agent','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36')]
            urllib.request.install_opener(opener)
            urllib.request.urlretrieve(self.image_url, f'{images_folder}\{self.sku}.jpg')
            sleep(1)            
            self.s3.upload_file(f'{images_folder}\{self.sku}.jpg', 'boxscraperbucket', f'raw_data/{self.sku}/images/{self.sku}.jpg')


        # Export the file containing all the GPU Product Data to a Json File and save locally within the 'raw_data' Folder.
        with open(f'{raw_data}/raw_data.json', 'w', encoding='utf-8') as f:
            json.dump(self.product_list, f, ensure_ascii=False)
        

        # Upload said Json file to s3 bucket.
        # Format as such:  s3_client.upload_file(file_name, bucket, s3_object_name)
        self.s3.upload_file(f'{raw_data}/raw_data.json', 'boxscraperbucket', 'raw_data/raw_data.json')

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
        shutil.rmtree(raw_data)
        self.driver.quit()
        print("\nEnd of session. Web Scraper is terminated. Webdriver excutable is no longer running.\n")



if __name__ == '__main__':
    scraper = BoxScraper()
    scraper.scrape_site()
