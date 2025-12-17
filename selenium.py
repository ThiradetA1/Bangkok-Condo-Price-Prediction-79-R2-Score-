import time
import pandas as pd
import re
import numpy as np
import random
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException 

def clean_price(text):
    if not text: return None
    clean = re.sub(r'[^\d]', '', text)
    return int(clean) if clean else None

def convert_floor_to_number(floor_text):
    if not floor_text: return None
    text = floor_text.replace('ชั้นที่', '').strip()
    if '-' in text:
        try:
            low, high = text.split('-')
            return (float(low) + float(high)) / 2
        except: return None
    elif re.match(r'^\d+$', text): return float(text)
    elif '+' in text: return float(re.sub(r'[^\d]', '', text)) + 2
    return None

def extract_keywords(title_text):
    if not title_text: return {'is_corner': 0, 'is_river_view': 0, 'near_bts': 0}
    text = title_text.lower()
    return {
        'is_corner': 1 if 'มุม' in text or 'corner' in text else 0,
        'is_river_view': 1 if 'แม่น้ำ' in text or 'river' in text else 0,
        'near_bts': 1 if 'bts' in text or 'mrt' in text or 'ใกล้รถไฟฟ้า' in text else 0
    }

def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_argument("--disable-dev-shm-usage") 
    chrome_options.add_argument("--no-sandbox")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


def scrape_pages_robust(start_page=1, end_page=200):
    
    filename = "livinginsider_big_data5.csv"
    
    cols_order = [
        'price', 'project_name', 'size_sqm', 'floor_range', 'floor_num', 
        'bedroom', 'bathroom', 'title_text', 'is_corner', 'is_river_view', 'near_bts'
    ]
    
    if not os.path.exists(filename):
        pd.DataFrame(columns=cols_order).to_csv(filename, index=False, encoding="utf-8-sig")

    print(f"🚀 Starting scrape from page {start_page} to {end_page}...")

    driver = init_driver()

    for page in range(start_page, end_page + 1):
        
        if page % 50 == 0:
            print("♻️ Restarting browser to clear memory...")
            driver.quit()
            time.sleep(2)
            driver = init_driver()

        max_retries = 3
        for attempt in range(max_retries):
            try:
                url = f"https://www.livinginsider.com/searchword/Condo/Buysell/{page}/รวมประกาศ-ขาย-คอนโด.html"
                print(f"--> Processing Page {page}/{end_page} (Attempt {attempt+1}) : {url}")
                
                driver.get(url)
                time.sleep(random.uniform(3, 5)) 
                
                if "403 Forbidden" in driver.title or "Error" in driver.title:
                    print("    Blocked or Error page. Waiting longer...")
                    time.sleep(10)
                    raise Exception("Page load error")

                cards = driver.find_elements(By.CLASS_NAME, "istock-list")
                page_data = []

                for card in cards:
                    try:
                        item = {}
                        
                        try: item['price'] = clean_price(card.find_element(By.CLASS_NAME, "text_price").text)
                        except: item['price'] = None
                        
                        try: item['project_name'] = card.find_element(By.CLASS_NAME, "text_location").text.strip()
                        except: item['project_name'] = "Unknown"

                        details = card.find_elements(By.CLASS_NAME, "ic-detail")
                        
                        item['size_sqm'] = np.nan
                        item['floor_range'] = None
                        item['floor_num'] = np.nan
                        item['bedroom'] = 0
                        item['bathroom'] = 0

                        if len(details) >= 4:
                            size_match = re.search(r"(\d+(\.\d+)?)", details[0].text)
                            if size_match: item['size_sqm'] = float(size_match.group(1))
                            
                            raw_floor = details[1].text.replace('\n', ' ').strip()
                            item['floor_range'] = raw_floor
                            item['floor_num'] = convert_floor_to_number(raw_floor)
                            
                            bed_match = re.search(r'(\d+)', details[2].text)
                            item['bedroom'] = int(bed_match.group(1)) if bed_match else 0
                            
                            bath_match = re.search(r'(\d+)', details[3].text)
                            item['bathroom'] = int(bath_match.group(1)) if bath_match else 0

                        try:
                            title_elem = card.find_element(By.TAG_NAME, "a")
                            title_text = title_elem.get_attribute("title") or card.text
                            item['title_text'] = title_text
                            item.update(extract_keywords(title_text))
                        except:
                            item['title_text'] = ""
                            item.update(extract_keywords(""))

                        if item['price'] and item['price'] > 500000 and item['size_sqm'] and item['size_sqm'] > 10:
                            page_data.append(item)
                    except: continue
                
                if page_data:
                    df_page = pd.DataFrame(page_data)
                    
                    for col in cols_order:
                        if col not in df_page.columns:
                            df_page[col] = np.nan
                            
                    df_page = df_page[cols_order] 
                    
                    df_page.to_csv(filename, mode='a', header=False, index=False, encoding="utf-8-sig")
                    print(f"    ✅ Saved {len(df_page)} rows.")
                else:
                    print(f"    ⚠️ No data found on page {page}.")
                
                break 

            except (WebDriverException, Exception) as e:
                print(f"Error on page {page}: {e}")
                if "no such window" in str(e) or "target window already closed" in str(e) or "refused" in str(e):
                    try: driver.quit()
                    except: pass
                    time.sleep(3)
                    driver = init_driver()
                if attempt == max_retries - 1:
                    print(f"Skipping page {page}.")
                else:
                    time.sleep(5)

    driver.quit()
    print("\n✅ Scraping Completed.")

if __name__ == "__main__":
    scrape_pages_robust(start_page=405, end_page=505)
