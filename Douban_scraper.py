# parser
import pandas as pd
import json
import re
import time
import random
import os
import undetected_chromedriver as uc 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.action_chains import ActionChains

def driver_starter():
    options = uc.ChromeOptions()
    options.add_argument('--disable-popup-blocking')
    driver = uc.Chrome(options=options)
    return driver

def get_film_urls(driver):
    WebDriverWait(driver, 60).until(ec.presence_of_element_located((By.CLASS_NAME, 'subject-card')))
    time.sleep(random.uniform(1, 5))
    films_for_scrap = driver.find_element(By.XPATH, '//div[@data-swiper-slide-index = 0]').find_elements(By.CLASS_NAME, 'subject-card')
    time.sleep(random.uniform(1, 5))
    films_for_scrap.extend(driver.find_element(By.XPATH, '//div[@data-swiper-slide-index = 1]').find_elements(By.CLASS_NAME, 'subject-card'))
    time.sleep(random.uniform(1, 5))
    films_for_scrap.extend(driver.find_element(By.XPATH, '//div[@data-swiper-slide-index = 2]').find_elements(By.CLASS_NAME, 'subject-card'))
    time.sleep(random.uniform(1, 5))
    films_for_scrap.extend(driver.find_element(By.XPATH, '//div[@data-swiper-slide-index = 3]').find_elements(By.CLASS_NAME, 'subject-card'))
    time.sleep(random.uniform(1, 5))
    url_list = []

    for film in films_for_scrap:
        film_url = film.find_element(By.XPATH, './/a[@href]').get_attribute('href')
        url_list.append(film_url)
    return url_list

def save_results(final_data, scrapped_films):
    df = pd.DataFrame(final_data)
    file_exists = os.path.isfile('Douban.csv')
    df.to_csv('Douban.csv', mode='a', header=not file_exists, index=False, encoding='utf-8-sig')
    with open('scrapped_films', 'w', encoding='utf-8') as f:
        json.dump(scrapped_films, f)

def film_reviews_parser(url_list,driver,scrapped_films):
    final_data = []
    for id,url in enumerate(url_list):
        if not url in scrapped_films: 
            driver.get(url_list[id])
            WebDriverWait(driver, 60).until(ec.presence_of_element_located((By.XPATH, "//p[@class = 'pl']//a[@href = 'reviews']")))
            time.sleep(3)
            reviews_bttn = driver.find_element(By.ID, "reviews-wrapper").find_element(By.XPATH, ".//a[@href = 'reviews']")
            time.sleep(3)
            ActionChains(driver).move_to_element(reviews_bttn).perform()
            driver.execute_script("arguments[0].click();", reviews_bttn)
            for i in range(0,20):
                WebDriverWait(driver, 60).until(ec.presence_of_element_located((By.XPATH, '//div[@data-cid]')))
                final_data.extend(review_parser(driver))
                try:
                    next_page = driver.find_element(By.CLASS_NAME, 'paginator').find_element(By.CLASS_NAME, 'next').find_element(By.XPATH, './/a[@href]')
                    driver.execute_script("arguments[0].click();", next_page)
                except:
                    break
            scrapped_films.append(url)
        else:
            continue
    return final_data, scrapped_films

def getting_cookies(driver):
    cookies = None
    try:
        with open('douban_cookies.json', 'r', encoding='utf-8') as f:
            cookies = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        input("Enter the account and push Enter")
        cookies = driver.get_cookies()
        with open('douban_cookies.json', 'w', encoding='utf-8') as f:
            json.dump(cookies, f)
    return cookies

def review_parser(driver):
    tempor_data = []
    reviews = driver.find_elements(By.XPATH, "//div[@data-cid]")
    for review in reviews:
        full_review={}
        try:
            stars = review.find_element(By.XPATH, './/span[@title]')
        except:
            continue           
        mark = stars.get_attribute('class')
        if mark == "allstar30 main-title-rating":
            full_review['mark'] = 1
        elif mark == "allstar50 main-title-rating" or mark == "allstar40 main-title-rating":
            full_review['mark'] = 2
        elif mark == "allstar20 main-title-rating" or mark == "allstar10 main-title-rating":
            full_review['mark'] = 0
        try:
            open_bttn = review.find_element(By.XPATH, ".//a[@class ='unfold']")
            ActionChains(driver).move_to_element(open_bttn).perform()
            driver.execute_script("arguments[0].click();", open_bttn)
            WebDriverWait(driver, 30).until(ec.presence_of_element_located((By.XPATH, './/p[@data-align]|.//p[@data-page]')))
            time.sleep(random.uniform(1,2))
        except:
            pass
        final_review = [n.text for n in review.find_elements(By.XPATH, './/p[@data-align]|.//p[@data-page]')]
        full_review['review'] = final_review
        tempor_data.append(full_review)
        time.sleep(random.uniform(1,2))
    return(tempor_data)

driver = driver_starter()
driver.get('https://www.douban.com/?p=1')
cookies = getting_cookies(driver)
for cookie in cookies:
    driver.add_cookie(cookie)
driver.refresh()
WebDriverWait(driver,60).until(ec.element_to_be_clickable((By.CLASS_NAME, 'global-nav-items')))
time.sleep(random.uniform(3, 7))
driver.get('https://movie.douban.com')
try:
    consent_bttn = WebDriverWait(driver, 60).until(ec.element_to_be_clickable((By.CSS_SELECTOR, 'button.fc-cta-consent')))
    consent_bttn.click()
except:
    pass

url_list = get_film_urls(driver)

with open('scrapped_films', 'r', encoding='utf-8') as f:
    scrapped_films = json.load(f)
final_data, scrapped_films = film_reviews_parser(url_list,driver, scrapped_films)

for id, review in enumerate(final_data):
    interim_review = [re.sub(r'\s+', ' ', re.sub(r'[a-zA-Z\n]+', '', n)).strip() for n in review['review']]
    interim_review = " ".join(interim_review)
    final_data[id]['review'] = interim_review
final_data = [i for i in final_data if len(i['review']) > 10]

save_results(final_data, scrapped_films)

driver.quit()