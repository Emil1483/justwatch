import requests
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import json
import os

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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

def get_auth_from_event(event):
    return get_nested_value(event, "params", "request", "headers", "authorization")

def get_auth_from_event_reserve(event):
    auth = str(event)
    index = auth.find('authorization')

    if index == -1: return

    auth = auth[index + 17:]

    return auth.split("'")[0]

def get_auth():
    print(f"{bcolors.OKCYAN}Retrieving currency auth token{bcolors.ENDC}")

    capabilities = DesiredCapabilities.CHROME
    capabilities["goog:loggingPrefs"] = {"performance": "ALL"}  # chromedriver 75+

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(
        ChromeDriverManager().install(),
        desired_capabilities=capabilities,
        chrome_options=options
    )

    driver.get("http://www.xe.com")
    logs = driver.get_log("performance")
    driver.quit()
    events = [*process_browser_logs_for_network_events(logs)]
    with open("auth.txt", "wt") as f:
        for event in events:
            if (auth := get_auth_from_event(event)) is not None:
                f.write(auth)
                return auth

        print(f"{bcolors.WARNING}Warning: Using backup method to get currency auth token{bcolors.ENDC}")

        for event in events:
            if (auth := get_auth_from_event_reserve(event)) is not None:
                f.write(auth)
                return auth

url = "https://www.xe.com/api/protected/midmarket-converter/"

path = os.path.dirname(os.path.realpath(__file__))
auth_token = open(f"{path}/auth.txt", "r").read()

auth_header = {"authorization": auth_token}

response = requests.get(url, headers=auth_header)
if response.status_code != 200:
    auth = get_auth()

    if auth is None:
        response = None
        print(f"{bcolors.FAIL}Alert: Could not get currency auth token. " +
                f"We will only display subscription offers{bcolors.ENDC}")
    else:
        response = requests.get(url, headers={"authorization": auth})

rates = response.json()["rates"] if response is not None else None

def convert(value, old, new):
    return value * rates[new] / rates[old]

if __name__ == '__main__':
    print(convert(10, "USD", "NOK"))
