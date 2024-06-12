import time
import csv
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Konfigurasi Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument('--disable-dev-shm-usage')
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

s = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=s, options=options)

# Inisialisasi list untuk menyimpan data
data_list = []

# Fungsi untuk scraping detail kunci
def scrape_key_details(soup):
    car_data = {
        'Kondisi': "N/A",
        'Tahun Kendaraan': "N/A",
        'Kilometer': "N/A",
        'Warna': "N/A",
        'Cakupan mesin': "N/A",
        'Transmisi': "N/A",
        'Penumpang': "N/A"
    }
    specs = soup.select(".c-key-details__item")
    for spec in specs:
        try:
            key = spec.select_one("span.u-text-7").text.strip()
            value = spec.select_one("span.u-text-bold").text.strip()
            if key in car_data:
                car_data[key] = value
        except Exception as e:
            print(f"Error parsing key detail: {e}")
            continue
    return car_data

# Fungsi untuk scraping spesifikasi tambahan
def scrape_specifications(soup):
    additional_data = {
        'Pintu': "N/A",
        'Dirakit': "N/A",
        'Tipe Bahan Bakar': "N/A"
    }
    spec_tab = soup.select_one("#tab-specifications")
    if spec_tab:
        spec_items = spec_tab.select(".u-border-bottom.u-padding-ends-xs.u-flex.u-flex--justify-between")
        for item in spec_items:
            try:
                key = item.select("span")[0].text.strip()
                value = item.select("span")[1].text.strip()
                if key in additional_data:
                    additional_data[key] = value
            except Exception as e:
                print(f"Error parsing specification: {e}")
                continue
    return additional_data

# Fungsi untuk scraping satu halaman
def scrape_page(page_number):
    url = f'https://www.mobil123.com/mobil-dijual/indonesia?type=used&page_number={page_number}&page_size=25'
    driver.get(url)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h2.listing__title a"))
        )
    except TimeoutException:
        print(f"TimeoutException at page {page_number}")
        return

    car_elements = driver.find_elements(By.CSS_SELECTOR, "h2.listing__title a")
    car_urls = [car.get_attribute('href') for car in car_elements]

    for car_url in car_urls:
        driver.get(car_url)
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1.u-text-bold"))
            )
        except TimeoutException:
            print(f"TimeoutException at car URL: {car_url}")
            continue

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        car_details = {}

        try:
            car_details['Title'] = soup.select_one("h1.u-text-bold").text.strip()
        except Exception as e:
            print(f"Error parsing title: {e}")
            car_details['Title'] = "N/A"

        try:
            car_details['Harga'] = soup.select_one("div.listing__price.u-text-4.u-text-bold").text.strip()
        except Exception as e:
            print(f"Error parsing price: {e}")
            car_details['Harga'] = "N/A"

        # Scraping key details
        key_details = scrape_key_details(soup)
        car_details.update(key_details)

        # Scraping additional specifications
        specifications = scrape_specifications(soup)
        car_details.update(specifications)

        data_list.append(car_details)
        time.sleep(1)  # Tambahkan jeda 1 detik antara permintaan detail setiap mobil

# Fungsi untuk memuat data lama dan menggabungkan dengan data baru
def load_and_update_data():
    try:
        existing_data = pd.read_csv('data/car_details.csv')
    except FileNotFoundError:
        existing_data = pd.DataFrame()  # Jika file tidak ditemukan, inisialisasi dengan DataFrame kosong

    if data_list:
        new_data_df = pd.DataFrame(data_list)
        combined_data = pd.concat([existing_data, new_data_df], ignore_index=True)
        combined_data.drop_duplicates(inplace=True)

        combined_data.to_csv('car_data.csv', index=False)

if __name__ == '__main__':
    # Scraping dua halaman pertama sebagai contoh
    for page in range(1, 3):
        scrape_page(page)
        time.sleep(5)  # Tambahkan jeda 5 detik antara permintaan setiap halaman

    # Memuat data lama dan menggabungkan dengan data baru
    load_and_update_data()

    # Tutup driver
    driver.quit()
