from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import pandas as pd
import os

class dataIngestionTool:
    def __init__(self,
                 web_link = 'https://vbpl.vn/pages/portal.aspx',
                 chromeDriver_path = r'C:\Users\VICTUS\Documents\developer\chromedriver-win64\chromedriver.exe',
                 
    ):
        try: 
            self.webpage_link = web_link

            self.service = Service(chromeDriver_path)
            self.driver = webdriver.Chrome(service=self.driver)
            print("🟢 Tạo driver thành công.")
        except Exception as e:
            print(f"⭕ Lỗi khi tạo driver: {e}")

    def ingest_data(self, keyword: str):
        """
        Phương thức tải về toàn bộ văn bản pháp luật và metadata liên quan tới keyword được truyền vào.
        
        # Arg:
        - `keyword`: Keyword truyền vào.

        # Output:
        - Một biến json duy nhất lưu trữ văn bản pháp luật và metadata tương ứng.
        """

        self.driver.get(self.webpage_link)
        keyword = keyword.strip()

        metadata = []
        metadata.clear() # Đảm bảo metadata luôn rỗng khi bắt đầu ingest dữ liệu.

        print(f'🔬 Bắt đầu tìm kiếm: {keyword} ...')
        search_box = self.driver.find_element(By.ID, "AdvanceKeyword")
        search_box.clear()
        search_box.send_keys(keyword)
        search_box.send_keys(Keys.ENTER)

        time.sleep(0.5)
        try:
            numberOfResult_object = self.driver.find_element(By.XPATH, '//span[contains(text(), "Tìm thấy")]/strong')
            numberOfResult = int(numberOfResult.text)
            print(f"🔬 Đã tìm thấy {numberOfResult} văn bản pháp luật theo từ khóa {keyword}.")
        except Exception as e:
            print(f"⭕ Lỗi khi tìm tài liệu văn bản pháp luật theo từ khóa {keyword}: {e}")
            return []
        
        iteractor = 0
        
        while True:
            ul_element_object = self.driver.find_element(By.CLASS_NAME, "listLaw")
            li_elements = ul_element_object.find_elements(By.TAG_NAME, "li")

            '''
            
            '''
            print()



