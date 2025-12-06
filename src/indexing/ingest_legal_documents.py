import os
import json
import time # <-- Thêm thư viện time để tạo deploy_key
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

class DataIngestionTool:
    """
    Một công cụ để cào dữ liệu văn bản pháp luật từ trang vbpl.vn.
    """
    def __init__(self, web_link: str = 'https://vbpl.vn/pages/portal.aspx'):
        """
        Khởi tạo WebDriver, tự động quản lý chromedriver.

        Args:
            web_link (str, optional): Link của trang web cần cào. Mặc định là 'https://vbpl.vn/pages/portal.aspx'.
        """
        self.webpage_link = web_link
        try:
            self.service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=self.service)
            print("🟢 Tạo driver thành công.")
        except Exception as e:
            print(f"⭕ Lỗi khi tạo driver: {e}")
            self.driver = None

    def ingest_data(self, keyword: str, output_dir: str):
        """
        Tải về toàn bộ văn bản pháp luật và metadata liên quan tới keyword.

        Args:
            keyword (str): Từ khóa tìm kiếm.
            output_dir (str): Thư mục để lưu file JSON kết quả.
        """
        if not self.driver:
            print("Driver chưa được khởi tạo. Dừng thực thi.")
            return

        self.driver.get(self.webpage_link)
        keyword = keyword.strip()
        all_documents = []

        print(f'\n============== Bắt đầu tìm kiếm: "{keyword}" ==============')
        try:
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "AdvanceKeyword"))
            )
            search_box.clear()
            search_box.send_keys(keyword)
            search_box.send_keys(Keys.ENTER)

            result_count_object = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//span[contains(text(), "Tìm thấy")]/strong'))
            )
            number_of_results = int(result_count_object.text)
            print(f"🔬 Đã tìm thấy {number_of_results} văn bản pháp luật.")
            if number_of_results == 0:
                return
        except TimeoutException:
            print(f"⭕ Không tìm thấy kết quả nào cho từ khóa '{keyword}' hoặc trang tải quá lâu.")
            return
        except Exception as e:
            print(f"⭕ Lỗi khi tìm kiếm: {e}")
            return

        page_number = 1
        
        while True:
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "listLaw"))
                )
                ul_element = self.driver.find_element(By.CLASS_NAME, "listLaw")
                li_elements = ul_element.find_elements(By.TAG_NAME, "li")
                print(f"🔍 Đang xử lý trang {page_number} với {len(li_elements)} kết quả...")
                
                page_data = []
                for li in li_elements:
                    try:
                        a_tag = li.find_element(By.CSS_SELECTOR, "p.title > a")
                        detail_link = a_tag.get_attribute("href")
                        
                        doc_info = {
                            "Tên văn bản": a_tag.text.strip(),
                            "Link chi tiết": detail_link,
                            "Mô tả": li.find_element(By.CSS_SELECTOR, "div.des > p").text.strip(),
                            "PDF": li.find_element(By.CSS_SELECTOR, "li.source > a").get_attribute("href"),
                            "Ban hành": li.find_element(By.CSS_SELECTOR, "div.right > p.green:nth-of-type(1)").text.split(":", 1)[-1].strip(),
                            "Hiệu lực": li.find_element(By.CSS_SELECTOR, "div.right > p.green:nth-of-type(2)").text.split(":", 1)[-1].strip(),
                            "Trạng thái": li.find_element(By.CSS_SELECTOR, "div.right > p.red").text.split(":", 1)[-1].strip(),
                            "Nội dung": ""
                        }
                        page_data.append(doc_info)
                    except NoSuchElementException:
                        continue
                        
                main_window = self.driver.current_window_handle
                for doc in page_data:
                    print(f"  🔗 Đang lấy nội dung cho: {doc['Tên văn bản'][:50]}...")
                    self.driver.switch_to.new_window('tab')
                    self.driver.get(doc["Link chi tiết"])
                    try:
                        content_div = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.ID, "toanvancontent"))
                        )
                        doc["Nội dung"] = content_div.text
                    except TimeoutException:
                        print(f"  ❌ Không tìm thấy nội dung cho văn bản này.")
                    finally:
                        self.driver.close()
                        self.driver.switch_to.window(main_window)

                all_documents.extend(page_data)

                old_ul_element = self.driver.find_element(By.CLASS_NAME, "listLaw")
                next_page_link = self.driver.find_element(By.XPATH, f"//div[@class='paging']//a[text()='{page_number + 1}']")
                next_page_link.click()
                
                WebDriverWait(self.driver, 10).until(EC.staleness_of(old_ul_element))
                page_number += 1

            except NoSuchElementException:
                print("✅ Đã xử lý hết các trang kết quả cho từ khóa này.")
                break
            except Exception as e:
                print(f"⭕ Lỗi khi xử lý trang {page_number}: {e}. Dừng lại.")
                break
        
        self.save_to_json(all_documents, keyword, output_dir)

    def save_to_json(self, data: list, keyword: str, output_dir: str):
        """Lưu dữ liệu vào file JSON."""
        if not data:
            print("Không có dữ liệu để lưu cho từ khóa này.")
            return

        os.makedirs(output_dir, exist_ok=True)
        
        safe_keyword = "".join(c for c in keyword if c.isalnum() or c in (' ', '_')).rstrip()
        filename = f"metadata_law_{safe_keyword.replace(' ', '_')}.json"
        json_path = os.path.join(output_dir, filename)

        df = pd.DataFrame(data)
        df.to_json(json_path, orient="records", force_ascii=False, indent=4)
        print(f"💾 Đã lưu thành công {len(data)} văn bản vào file: {json_path}")

    def quit(self):
        """Đóng trình duyệt."""
        if self.driver:
            self.driver.quit()
            print("\n🚪 Đã đóng driver.")


if __name__ == '__main__':
    KEYWORDS_TO_SEARCH = [
        "khám chữa bệnh",
        "bảo hiểm y tế",
        "thanh toán bảo hiểm",
        "chuyển tuyến",
        "giấy chuyển tuyến",
        "đăng ký khám chữa bệnh ban đầu",
        "mã định danh y tế",
        "thẻ bảo hiểm y tế",
        "hồ sơ bệnh án",
        "quy trình khám bệnh",
        "xét nghiệm",
        "viện phí",
        "thuốc và vật tư y tế",
        "thanh toán trực tuyến",
        "đồng chi trả",
        "quyền lợi người bệnh",
    ]

    deploy_key = time.strftime("%Y%m%d-%H%M%S")
    print(f"🔑 Deploy key cho lần chạy này: {deploy_key}")

    BASE_OUTPUT_DIRECTORY = os.path.join(r".\data\legal_documents\raw", deploy_key)
    
    # --- PHẦN THỰC THI ---
    ingestion_tool = DataIngestionTool()
    
    try:
        if ingestion_tool.driver:
            for keyword in KEYWORDS_TO_SEARCH:
                ingestion_tool.ingest_data(keyword=keyword, output_dir=BASE_OUTPUT_DIRECTORY)
    finally:
        ingestion_tool.quit()
