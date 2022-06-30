from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

import urllib.request
from time import sleep
import pandas as pd
import json
import os
import shutil
import uuid


class ScanScraper:
    
    """ A Web Scraper Class which collects data on Nvidia RTX 3060 Graphics Cards.
        Contains all the functions that will navigate the webpage, extract product information and store the information locally.
    """
    
    def __init__(self, landing_page_url: str = "https://www.scan.co.uk"):
        self.driver = webdriver.Chrome(executable_path="C:\\Users\\User\\miniconda3\\chromedriver.exe")
        self.driver.maximize_window()
        self.driver.get(landing_page_url)
        self.accept_cookies()
    
    
    def scrape(self):
        self.navigate_to_3060_cards()
        self._in_stock_3060_cards()
        self._data_collection()


    def accept_cookies(self, xpath: str = "//div[@class='inner']//button"):
        
        """ Automatically accepts webpage cookies."""
        
        try:
            sleep(1)
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath)))
            self.driver.find_element(By.XPATH, xpath).click()
        except TimeoutException:
            print("No Cookies Found!")


    def navigate_to_3060_cards(self):
    
        """ Automates all the actions that will navigate to the webpage showcasing all the Graphics Card listings. Returns the URL of the Webpage."""
        
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

    def _in_stock_3060_cards(self):
        
        """ Returns a list of links for all the in-stock graphics on the webpage."""
        
        sleep(1)
        try:
            container = self.driver.find_element(By.XPATH, "//ul[@class='productColumns']")
        except NoSuchElementException:
            container = self.driver.find_element(By.XPATH, "//body/div/div[@role='main']/div/div/div/div/div/ul[1]")

        list_of_3060_cards = container.find_elements(By.XPATH, './li')
        hidden_products = self.driver.find_elements(By.XPATH, "//li[contains(@data-price, '999999.00')]")
        in_stock_3060_cards = []
        
        for i in list_of_3060_cards:
            if i not in hidden_products:
                in_stock_3060_cards.append(i)
        
        print(f"There are {len(in_stock_3060_cards)} cards in stock")
        
        in_stock_list_of_links_for_3060 = []
        
        for rtx_3060 in in_stock_3060_cards:
            in_stock_list_of_links_for_3060.append(rtx_3060.find_element(By.TAG_NAME, 'a').get_attribute('href'))
        
        return in_stock_list_of_links_for_3060


    def _make_folder(self):
        
        """ Creates a 'raw-data' folder in the directory to store product information, 
            if it has not been created already.
        """
        
        global root_dir, raw_data
        
        root_dir = os.getcwd()
        raw_data = os.path.join(root_dir, 'raw_data')
        is_raw_data_there = os.path.exists(raw_data)

        if is_raw_data_there == True:
            shutil.rmtree(raw_data)
        else:
            os.makedirs(raw_data)

        return raw_data
    
    def _data_collection(self):
        
        """ Scrapes Product Name, SKU, Unique ID, Price, Webpage Link and Product Image for each product entry.
            Stores each product entry in 'raw-data' folder.        
        """
        self._make_folder()
        raw_data = self._make_folder()
        list_of_links_for_3060 = self._in_stock_3060_cards()
        product_list = []
        Product_Image_URL = []

        for link in list_of_links_for_3060[0:len(list_of_links_for_3060)]:

            product_dictionary = {
                'Product Name': [],
                'SKU': [],
                'Unique ID': [],
                'Price': [],
                'Link': [],
                'Product Image URL': []
            }

            self.driver.get(link)
            sleep(1)
            product_dictionary['Link'].append(link)

            # Get Product Name
            try:
                product_name = self.driver.find_element(By.XPATH, "//h1[@itemprop='name']")
                product_dictionary['Product Name'].append(product_name.text)
            except NoSuchElementException:
                product_dictionary['Product Name'].append('N/A')

            # Get Product SKU/Friendly ID
            try:
                sku = self.driver.find_element(By.XPATH, "(//strong[@itemprop='sku'])[1]")
                product_dictionary['SKU'].append(sku.text)
            except NoSuchElementException:
                product_dictionary['SKU'].append('N/A')

            # Generate UUID (Unique)
            try:
                unique_id = uuid.uuid4()
                str(unique_id)
                product_dictionary['Unique ID'].append(str(unique_id))
            except:
                product_dictionary['Unique ID'].append('N/A')

            # Get Image URL
            try:
                element = self.driver.find_element(By.XPATH, "//img[@class='zoomable-image'][1]")
                image_url = element.get_attribute('src')
                Product_Image_URL.append(image_url)
                product_dictionary['Product Image URL'].append(image_url)
            except NoSuchElementException:
                product_dictionary['Product Image URL'].append('N/A')

            # Item Price
            try:
                price = self.driver.find_element(By.XPATH, "(//span[@class='price'])[4]")
                product_dictionary['Price'].append(price.text)
            except NoSuchElementException:
                product_dictionary['Price'].append('N/A')

            # append each product dictionary to a list.
            product_list.append(product_dictionary)

            # Create a folder for each product, named after its SKU.
            product_entries = os.path.join(root_dir, raw_data, f"{(sku.text)}")
            os.makedirs(product_entries)
            with open(f'{product_entries}\data.json', 'w') as fp:
                json.dump(product_dictionary, fp)
            
            # Create an image Folder for each image
            images_folder = os.path.join(product_entries, "Images")  
            os.makedirs(images_folder)
            
            # Overcome 'HTTPError: HTTP Error 403: Forbidden' error code by modifying 'user-agent' variable that is send with the request.
            opener=urllib.request.build_opener()
            opener.addheaders=[('User-Agent','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.115 Safari/537.36')]
            urllib.request.install_opener(opener)
            urllib.request.urlretrieve(image_url, f'{images_folder}\{sku.text}.jpg')
            
        return len(next(os.walk(raw_data))[1])


if __name__ == '__main__':
    scraper = ScanScraper()
    scraper.scrape()




