import requests
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
import json

def process_browser_logs_for_network_events(logs):
    for entry in logs:
        log = json.loads(entry["message"])["message"]
        if (
            "Network.response" in log["method"]
            or "Network.request" in log["method"]
            or "Network.webSocket" in log["method"]
        ):
            yield log


def get_nested_value(json, *keys):
    if keys[0] not in json: return None
    if len(keys) == 1: return json[keys[0]]
    return get_nested_value(json[keys[0]], *keys[1:])

def get_auth():
    capabilities = DesiredCapabilities.CHROME
    capabilities["goog:loggingPrefs"] = {"performance": "ALL"}  # chromedriver 75+

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(
        "E:\development\chrome-driver\chromedriver.exe",
        desired_capabilities=capabilities,
        chrome_options=options
    )

    driver.get("http://www.xe.com")
    logs = driver.get_log("performance")
    driver.quit()
    events = process_browser_logs_for_network_events(logs)
    with open("auth.txt", "wt") as f:
        for event in events:
            auth = get_nested_value(event, "params", "response", "requestHeaders", "authorization")
            if auth is not None:
                f.write(auth)
                return auth

url = "https://www.xe.com/api/protected/midmarket-converter/"
auth_token = open("auth.txt", "r").read()
auth_header = {"authorization": auth_token}

response = requests.get(url, headers=auth_header)
if response.status_code != 200:
    response = requests.get(url, headers={"authorization": get_auth()})

rates = response.json()["rates"]

def convert(value, old, new):
    return value * rates[new] / rates[old]

if __name__ == '__main__':
    print(convert(10, "USD", "NOK"))
