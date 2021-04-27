from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait as wait
from time import sleep
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from currency_converter import CurrencyConverter
import pycountry

currency = CurrencyConverter()

url = "https://www.justwatch.com/no/movie/the-silence-of-the-lambs"

driver = webdriver.Chrome("E:\development\chrome-driver\chromedriver")

driver.get(url)

dropdown_css_selector = ".jw-chip-button.active a"
countries_css_selector = ".country-list-item .country-list-item__container a"
watch_now_css_selector = ".detail-infos__subheading"

def click_dropdown():
    element = driver.find_elements_by_css_selector(dropdown_css_selector)[-1]
    element.click()

def get_countries():
    return driver.find_elements_by_css_selector(countries_css_selector)

def wait_for(css_selector):
    wait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
            )

streaming_platform_data = {}
renting_platform_data = []

def extract_streaming():
    soup = BeautifulSoup(driver.page_source, "html.parser")
    app = soup.find(id='app')
    streaming_platform_row = app.find(class_="price-comparison__grid__row price-comparison__grid__row--stream")
    if streaming_platform_row is None: return []
    streaming_platforms = streaming_platform_row.find_all(class_="price-comparison__grid__row__element")
    streaming_platforms = [streaming_platform.find("img")["alt"] for streaming_platform in streaming_platforms]
    return streaming_platforms

def extract_price(text, country_name):
    country = pycountry.countries.get(name=country_name)
    currency = pycountry.currencies.get(numeric=country.numeric)
    print(country)
    print(currency)
    currency_code = currency.alpha_3
    print(currency_code)
    return text

def extract_renting(country):
    # (20, 'Norway', 'Google Play')
    soup = BeautifulSoup(driver.page_source, "html.parser")
    renting_platform_row = soup.find(class_="price-comparison__grid__row price-comparison__grid__row--rent")
    if renting_platform_row is None: return []
    renting_platforms = renting_platform_row.find_all(class_="price-comparison__grid__row__element")
    extracted_data = [
            (renting_platform.find("img")["alt"],
            extract_price(renting_platform.find(class_="price-comparison__grid__row__price").text, country),
            country)
            for renting_platform in renting_platforms]
    return extracted_data

def extract_data(country):
    streaming_platforms = extract_streaming()
    for streaming_platform in streaming_platforms:
        if streaming_platform in streaming_platform_data:
            streaming_platform_data[streaming_platform].append(country)
        else:
            streaming_platform_data[streaming_platform] = [country]

    renting_platform_data.extend(extract_renting(country))

click_dropdown()
sleep(1)

num_countries = len(get_countries())
start_country = get_countries()[0].text
extract_data(start_country)

for i in range(1, num_countries):
    country = get_countries()[i]
    actions = ActionChains(driver)
    actions.move_to_element(country).perform()
    if country.text == start_country: continue
    country_name = country.text
    country.click()
    wait_for(watch_now_css_selector)
    extract_data(country_name)
    driver.back()
    driver.refresh()
    wait_for(dropdown_css_selector)
    click_dropdown()
    wait_for(countries_css_selector)

driver.quit()

print(streaming_platform_data)
