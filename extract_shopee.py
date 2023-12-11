import os
import time
from time import sleep
import pandas as pd
import numpy as np
from urllib.parse import unquote
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

class ShopeeScraper:
    def __init__(self):
        self.options = Options()
        # self.options.add_argument('--headless')  # Uncomment this line to run in headless mode
        # self.options.add_argument('--no-sandbox')  # Uncomment this line if needed
        self.options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
        self.driver.maximize_window()

    def scroll_down(self, scrolls, scroll_percentage=0.75):
        # Calculate the scroll interval based on the percentage of the page height to scroll
        total_scroll_height = self.driver.execute_script(
            "return Math.max( document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight);")
        scroll_height = scroll_percentage * (total_scroll_height / scrolls)
        
        # Perform the scrolling
        for _ in range(scrolls):
            self.driver.execute_script(f"window.scrollBy(0, {scroll_height});")
            time.sleep(0.25)

    def scrape_category_links(self, category_url):
        # Visit the category URL and scroll down to load more categories
        self.driver.get(category_url)
        sleep(3)
        self.scroll_down(4)
        
        # Extract the links of sub-categories
        category_elements = self.driver.find_elements(By.CLASS_NAME, "shopee-category-list__sub-category")
        return [category.get_attribute('href') for category in category_elements]

    def scrape_product_data(self, link, current_time, index, num, count):
        # Visit the product page and scroll down to load more products
        self.driver.get(f'{link}?page={count}')
        sleep(2)
        self.scroll_down(4)
        
        # Check if there are search items
        search_items_elements = self.driver.find_elements(By.CLASS_NAME, "row.shopee-search-item-result__items")
        if search_items_elements == []:
            return 0  # Return 0 if no search items found

        # Extract product details
        name_elements = self.driver.find_elements(By.CSS_SELECTOR, ".efwNRW")
        url_elements = self.driver.find_elements(By.XPATH, '//a[@data-sqe="link"]')
        rating_elements = self.driver.find_elements(By.CLASS_NAME, "shopee-rating-stars__stars")
        price_elements = self.driver.find_elements(By.CSS_SELECTOR, ".cA9TT\\+")
        sold_elements = self.driver.find_elements(By.CLASS_NAME, "OwmBnn.eumuJJ")
        ratings = self.driver.find_elements(By.CSS_SELECTOR, ".\\+gdNDl")
        sold = self.driver.find_elements(By.CLASS_NAME, "DN6Jp1")

        def get_name():
            return [name.text for name in name_elements]

        def get_link():
            return [url.get_attribute('href') for url in url_elements]

        def get_rating():
            # Extract product rating
            product_rating = []
            for i, rating in enumerate(rating_elements, start=1):
                star_wrappers = rating.find_elements(By.CLASS_NAME, "shopee-rating-stars__star-wrapper")
                total_width = 0
                for star_wrapper in star_wrappers:
                    list_star = star_wrapper.find_element(By.CLASS_NAME, "shopee-rating-stars__lit")
                    width_style = list_star.get_attribute("style")
                    width_percent = float(width_style.split(":")[1].strip()[:-1].replace("%", ""))
                    total_width += width_percent
                product_rating.append(total_width)
            return product_rating

        def get_price():
            # Extract product price
            product_price = []
            for price_container in price_elements:
                price_wrappers = price_container.find_elements(By.CLASS_NAME, "bPcAVl")
                class_discounted = "bPcAVl FMvHxS H5ICvW"
                if class_discounted == price_wrappers[0].get_attribute("class"):
                    price_discount = price_container.find_element(By.XPATH, "./div[@class='bPcAVl IWBsMB']//span[@class='k9JZlv']")
                    product_price.append(price_discount.text)
                else:
                    price_element = price_container.find_element(By.CLASS_NAME, "bPcAVl")
                    current_price = price_element.find_elements(By.CLASS_NAME, "k9JZlv")
                    if len(current_price) == 1:
                        price = current_price[0].text
                        product_price.append(price)
                    elif len(current_price) == 2:
                        price_from, price_to = current_price[0].text, current_price[1].text
                        price = f"{price_from} - {price_to}"
                        product_price.append(price)
            return product_price

        def get_sold():
            # Extract historical sold quantity
            return [sold.text.split(" ")[2] for sold in sold_elements]
        
        def process_rating_null():
            rating_items = []
            for item in ratings:
                class_name = item.find_elements(By.CLASS_NAME, "shopee-rating-stars")
                rating_items.append(len(class_name))
            rating_fact = get_rating()
            j = 0
            for i, mark in enumerate(rating_items):
                if mark == 1:
                    rating_items[i] = rating_fact[j]
                    j += 1
                else:
                    rating_items[i] = np.nan
            return rating_items
                        
            
        def process_sold_null():
            sold_items = []
            for item in sold:
                class_eumuJJ = item.find_elements(By.CLASS_NAME, "OwmBnn.eumuJJ")
                if class_eumuJJ:
                    sold_items.append(1)
                else:
                    sold_num = item.find_element(By.CLASS_NAME, "OwmBnn").text
                    if sold_num == '':
                        sold_num = np.nan
                    else:
                        sold_num = sold_num.split(" ")[2]
                    sold_items.append(sold_num)
            sold_fact = get_sold()
            j = 0
            for i, mark in enumerate(sold_items):
                if mark == 1:
                    sold_items[i] = sold_fact[j]
                    j += 1
            return sold_items

        def load_dataframe():
            # Load extracted data into a DataFrame
            try:
                df = pd.DataFrame(columns=["product_name", "product_url", "product_rating", "product_price", "history_sold"])
                df["product_name"] = get_name()
                df["product_url"] = get_link()
                df["product_rating"] = process_rating_null()
                df["product_price"] = get_price()
                df["history_sold"] = process_sold_null()
                df.to_csv(f'{current_time}/0{index}/data_{num}_{count}.csv', index=False)
            except Exception as e:
                print(f"This error when save file csv: {e}")
                with open(f"{current_time}/error.txt", "a") as f:
                    f.write(f"Save file CSV error in index: {index} and {link}?page={count} with error {e}\n")
            return df

        print(load_dataframe())

        len_items_page = len(get_name())
        return len_items_page

    def run_scraper(self):
        # Main function to run the scraper
        current_time = time.strftime("%Y%m%d_%H%M%S")
        os.mkdir(current_time)
        shopee_url = "https://shopee.vn/"
        self.driver.get(shopee_url)
        sleep(1)
        self.scroll_down(2)
        
        # Extract category URLs
        category_url_elements = self.driver.find_elements(By.CLASS_NAME, "home-category-list__category-grid")
        category_url_ls = [category.get_attribute('href') for category in category_url_elements]
        category_url_ls = category_url_ls[6:]
        # Loop through categories and subcategories
        # print('44444', category_url_ls)
        
        for index, category_url in enumerate(category_url_ls):
            os.mkdir(f"{current_time}/0{index}")
            link_category = self.scrape_category_links(category_url)
            # Write mapping URL to a file when reaching the limit
            string_url = category_url.split("/")[-1]
            need_index = string_url.index("-cat")
            category_name = unquote(string_url[:need_index])
            with open(f"{current_time}/mapping_url.txt", "a") as f:
                f.write(f"{index} --> {category_name}\n")
            print('55555', len(link_category))
            len_items = 0
            for num, link in enumerate(link_category):
                count = 0
                while True:
                    len_items_page = self.scrape_product_data(link, current_time, index, num, count)
                    len_items += len_items_page
                    count += 1
                    print('222222', len_items)

                    if len_items_page == 0:
                        break
                if len_items > 4000:
                    break

if __name__ == "__main__":
    # Create an instance of ShopeeScraper and run the scraper
    scraper = ShopeeScraper()
    scraper.run_scraper()


# a = ['https://shopee.vn/%C4%90i%E1%BB%87n-Tho%E1%BA%A1i-Ph%E1%BB%A5-Ki%E1%BB%87n-cat.11036030', 'https://shopee.vn/M%E1%BA%B9-B%C3%A9-cat.11036194', 'https://shopee.vn/Thi%E1%BA%BFt-B%E1%BB%8B-%C4%90i%E1%BB%87n-T%E1%BB%AD-cat.11036132', 'https://shopee.vn/Nh%C3%A0-C%E1%BB%ADa-%C4%90%E1%BB%9Di-S%E1%BB%91ng-cat.11036670', 'https://shopee.vn/M%C3%A1y-T%C3%ADnh-Laptop-cat.11035954', 'https://shopee.vn/S%E1%BA%AFc-%C4%90%E1%BA%B9p-cat.11036279', 'https://shopee.vn/M%C3%A1y-%E1%BA%A2nh-M%C3%A1y-Quay-Phim-cat.11036101', 'https://shopee.vn/S%E1%BB%A9c-Kh%E1%BB%8Fe-cat.11036345', 'https://shopee.vn/%C4%90%E1%BB%93ng-H%E1%BB%93-cat.11035788', 'https://shopee.vn/Gi%C3%A0y-D%C3%A9p-N%E1%BB%AF-cat.11035825', 'https://shopee.vn/Gi%C3%A0y-D%C3%A9p-Nam-cat.11035801', 'https://shopee.vn/T%C3%BAi-V%C3%AD-N%E1%BB%AF-cat.11035761', 'https://shopee.vn/Thi%E1%BA%BFt-B%E1%BB%8B-%C4%90i%E1%BB%87n-Gia-D%E1%BB%A5ng-cat.11036971', 'https://shopee.vn/Ph%E1%BB%A5-Ki%E1%BB%87n-Trang-S%E1%BB%A9c-N%E1%BB%AF-cat.11035853', 'https://shopee.vn/Th%E1%BB%83-Thao-Du-L%E1%BB%8Bch-cat.11035478', 'https://shopee.vn/B%C3%A1ch-H%C3%B3a-Online-cat.11036525', 'https://shopee.vn/%C3%94-T%C3%B4-Xe-M%C3%A1y-Xe-%C4%90%E1%BA%A1p-cat.11036793', 'https://shopee.vn/Nh%C3%A0-S%C3%A1ch-Online-cat.11036863', 'https://shopee.vn/Balo-T%C3%BAi-V%C3%AD-Nam-cat.11035741', 'https://shopee.vn/Th%E1%BB%9Di-Trang-Tr%E1%BA%BB-Em-cat.11036382', 'https://shopee.vn/%C4%90%E1%BB%93-Ch%C6%A1i-cat.11036932', 'https://shopee.vn/Gi%E1%BA%B7t-Gi%C5%A9-Ch%C4%83m-S%C3%B3c-Nh%C3%A0-C%E1%BB%ADa-cat.11036624', 'https://shopee.vn/Ch%C4%83m-S%C3%B3c-Th%C3%BA-C%C6%B0ng-cat.11036478', 'https://shopee.vn/Voucher-D%E1%BB%8Bch-V%E1%BB%A5-cat.11035898', 'https://shopee.vn/D%E1%BB%A5ng-c%E1%BB%A5-v%C3%A0-thi%E1%BA%BFt-b%E1%BB%8B-ti%E1%BB%87n-%C3%ADch-cat.11116484']