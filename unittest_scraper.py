import unittest
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
import yaml
import os
import shutil
import uuid
import shortuuid
import pandas as pd
import boto3
from sqlalchemy import create_engine
from  boxscraper import BoxScraper


class BoxScraperTestCase(unittest.TestCase):

    def setUp(self):
        self.scraper = BoxScraper()
    
    
    def test_navigate_to_3060_cards(self):
        url = 'https://www.box.co.uk/rtx-3060-graphics-cards'
        self.scraper.driver.get(url)

        actual_value = str(self.scraper.driver.current_url)
        expected_value = 'https://www.box.co.uk/rtx-3060-graphics-cards'
        self.assertEqual(expected_value, actual_value)


    def test_in_stock_3060_cards(self):
        url = 'https://www.box.co.uk/rtx-3060-graphics-cards'
        self.scraper.driver.get(url)
        
        number_of_cards_in_stock = self.scraper.driver.find_element(By.css, "div[class='product-list-header'] span")
        number_of_cards_in_stock = int(number_of_cards_in_stock)

        if self.scraper.driver.find_elements(By.XPATH, "(//div[@class='product-list p-small-list'])//h3"):
            list_of_3060_cards = self.scraper.driver.find_elements(By.XPATH, "(//div[@class='product-list p-small-list'])//h3")
            print("Found the container holding the list of cards on first attempt!")
        else:
            list_of_3060_cards =  self.scraper.driver.find_elements(By.XPATH, "(//div[@class='product-list  p-small-list'])//h3")
            print("Found the container holding the list of cards on second attempt!")

        expected_output = len(number_of_cards_in_stock)
        actual_output = len(list_of_3060_cards)
        self.assertEqual(expected_output, actual_output)
        
        return len(number_of_cards_in_stock)
    
    def test_data_collection(self):
        url = 'https://www.box.co.uk/rtx-3060-graphics-cards'
        self.scraper.driver.get(url)
        sleep(25)
        self.scraper.driver.refresh()
        expected_output = self.scraper.n
        # self.scraper._data_collection()
        actual_output = self.scraper.__data_collection()
        self.assertEqual(expected_output, actual_output)
    

    def tearDown(self):
        sleep(1)
        self.scraper.driver.quit()
    
    
    # @classmethod
    # def tearDownClass(self):
    #     pass



unittest.main(argv=[''], verbosity=2, exit=False)