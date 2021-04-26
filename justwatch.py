from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait as wait
from time import sleep
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

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

platform_data = {}

def extract_data(country):
    soup = BeautifulSoup(driver.page_source, "html.parser")
    app = soup.find(id='app')
    platform_row = app.find(class_="price-comparison__grid__row price-comparison__grid__row--stream")
    if platform_row is None: return
    platforms = platform_row.find_all(class_="price-comparison__grid__row__element")
    platforms = [platform.find("img")["alt"] for platform in platforms]
    for platform in platforms:
        if platform in platform_data:
            platform_data[platform].append(country)
        else:
            platform_data[platform] = [country]

click_dropdown()
sleep(1)

num_countries = len(get_countries())
start_country = get_countries()[0].text

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

print(platform_data)
