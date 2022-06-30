import unittest
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
from  scraper import ScanScraper


class ScanScraperTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(self):
        self.scraper = ScanScraper()
    
    def _accept_cookies(self):
        self.scraper._accept_cookies()  

    def test_navigate_to_3060_cards(self):
        self.scraper._navigate_to_3060_cards()
        actual_value = str(self.scraper.driver.current_url)
        expected_value = 'https://www.scan.co.uk/shop/computer-hardware/gpu-nvidia-gaming/nvidia-geforce-rtx-3060-graphics-cards'
        
        self.assertEqual(expected_value, actual_value)

    def test_in_stock_3060_cards(self):
        
        try:
            container = self.scraper.driver.find_element(By.XPATH, "//ul[@class='productColumns']")
        except NoSuchElementException:
            container = self.scraper.driver.find_element(By.XPATH, "//body/div/div[@role='main']/div/div/div/div/div/ul[1]")
            
        list_of_3060_cards = container.find_elements(By.XPATH, './li')
        hidden_products = self.scraper.driver.find_elements(By.XPATH, "//li[contains(@data-price, '999999.00')]")
    
        in_stock_list_of_links_for_3060 = self.scraper._in_stock_3060_cards()

        in_stock_list_of_links_for_3060 = self.scraper._in_stock_3060_cards()
        
        l1 =[]
        
        expected_output = len(list_of_3060_cards) - len(hidden_products)
        actual_output = len(in_stock_list_of_links_for_3060)
        
        self.assertEqual(expected_output, actual_output)
        self.assertTrue(type(in_stock_list_of_links_for_3060) is type(l1))
        
        return len(in_stock_list_of_links_for_3060)
    
    def test_data_collection(self):
        expected_output = self.test_in_stock_3060_cards()
        self.scraper._data_collection()
        actual_output = self.scraper._data_collection()
        
        self.assertEqual(expected_output, actual_output)
    
    
    
    
    @classmethod
    def tearDownClass(self):
        pass



unittest.main(argv=[''], verbosity=2, exit=False)