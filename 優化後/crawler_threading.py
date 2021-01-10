import csv
import requests
import time
import os
import threading
from bs4 import BeautifulSoup
from multiprocessing import Process, Manager

def get_html(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.75 Safari/537.36'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup
        
def process_review(reviews_link, msg): #  msg = [title, score, price, date, tag]
    global global_csv_data
    soup = get_html(reviews_link)
    reviews = soup.find_all('div', class_='review-content')
    data = [[msg[0], msg[1], msg[2], msg[3], msg[4], review.getText()] for review in reviews]
    global_csv_data += data

def crawler(start_page, processes):
    global tasks
    base_url = 'https://www.urcosme.com/tags/14/products?fbclid=IwAR0xatEdaJJTe8db2SPQPGVkAwa8cb-OfJavlEHxTNl-Ss81NJcX2bQa49U&page='
    soup = get_html(base_url + '1')
    pages = soup.find('div', class_='pagination').find_all('a')
    page_range = int(pages[len(pages) - 2].getText()) + 1
    page = start_page
    while page < page_range:
        soup = get_html(base_url + str(page))
        products_list = soup.find_all('div', class_='uc-product-item')
        for product in products_list:
            title = product.find('div', class_='product-name').select_one('a').getText()
            score = product.find('div', class_='score').getText()
            date_price_span = product.find('div', class_='product-market-date').find_all('span')
            date = ''
            price = ''
            if len(date_price_span) == 3:
                date = date_price_span[0].getText().replace('上市日期：', '')
                price = date_price_span[2].getText().replace('價格：', '')
            elif len(date_price_span) == 1:  # 只有價格
                price = date_price_span[0].getText().replace('價格：', '')

            link = 'https://www.urcosme.com/' + product.find('div', class_='product-image').find('a').get('href')
            soup = get_html(link)
            tags = soup.find_all('div', class_='uc-product-detail')
            tag = ''
            try:
                tags = soup.find_all('div', class_='uc-product-detail')
                tag_titles = tags[len(tags) - 1].find('div', class_='detail-text').find_all('a')
                tag_titles = [tag_title.getText() for tag_title in tag_titles]
                tag = '、'.join(tag_titles)
            except:
                pass
            
            reviews_link = link + '/reviews'
            pagination_soup = get_html(reviews_link)
            reviews_pages = 1
            try:
                check_next_reviews = pagination_soup.find('div', class_='pagination').find('a', rel='next')
                reviews_pages_link = pagination_soup.find('div', class_='pagination').find_all('a') 
                reviews_pages = reviews_pages_link[-2].getText()
            except:
                pass
            reviews_link_template = link + '/reviews?page='
            msg = [title, score, price, date, tag]
            for reviews_page in range(1, int(reviews_pages) + 1):
                tasks.append(threading.Thread(target=process_review, args=(reviews_link_template + str(reviews_page), msg),))
                tasks[len(tasks) - 1].start()

        print('page:', page, 'finish')
        page += processes


start = time.time()
global_csv_data = [['標題', '評分', '價格', '上市日期', '標籤', '評論']]
total_pages = 30
tasks = []

for i in range(1, total_pages + 1):
    tasks.append(threading.Thread(target=crawler, args=(i, total_pages),))
    tasks[i - 1].start()

for i in range(len(tasks)):
    tasks[i].join()

with open('threading_output.csv', 'w', newline='', encoding='utf-8-sig') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerows(global_csv_data)

end = time.time()
print(f'執行時間 {end - start} 秒')