import sys
import requests
from currency_converter import convert, rates
from progress.bar import IncrementalBar
import inquirer

locales = requests.get("http://apis.justwatch.com/content/locales/state").json()
locales = [(locale["full_locale"], locale["country"]) for locale in locales]

exchange_rates = {}

args = sys.argv[1:]

if len(args) == 0:
    raise TypeError("\n\nMissing 1 required argument \"search-term\"\n"
    + "For example, run:\n"
    + "python justwatch.py hunger games --on netflix --curr NOK")

arg_map = dict()

current_key = "first_arg"
current_vals = []
for i, arg in enumerate(args):
    if arg.startswith("-"):
        current_key = arg
        current_vals.clear()
        continue
    
    current_vals.append(arg)
    arg_map[current_key] = current_vals.copy()

query_name = " ".join(arg_map["first_arg"])
prioritised = arg_map["--on"] if "--on" in arg_map else ["netflix"]
preferred_currency = "".join(arg_map["--curr"]) if "--curr" in arg_map else "NOK"
preferred_currency = preferred_currency.upper()

if rates is not None and preferred_currency not in rates:
    raise ValueError(f"\n\nCould not recognize \"{preferred_currency}\" as a currency")

query = query_name.replace(" ", "%20")
search_body = f"%7B\"page_size\":10,\"page\":1,\"query\":\"{query}\",\"content_types\":[\"movie\",\"show\"]%7D"

query_result = requests.get(f"https://apis.justwatch.com/content/titles/pt_BR/popular?language=en&body={search_body}").json()

if len(query_result["items"]) == 0: raise ValueError(f"Could not find any results for \"{query_name}\"")

alternatives = [
  inquirer.List("choice",
                message=f"Results for \"{query_name}\"",
                choices=[item["title"] for item in query_result["items"]],
            ),
]
choice = inquirer.prompt(alternatives)["choice"]

entity = next((item for item in query_result["items"] if item["title"] == choice), None)

id = entity["id"]
content_type = entity["object_type"]
title = entity["title"]

def simplify_url(url):
    split = url.split("/")
    for part in split:
        if '.' in part: return part
    raise ValueError(f"{url} could not be simplified")

def extract_service_url(offer):
    return simplify_url(list(offer["urls"].values())[0])

def extract_offers(offers, list, location):
    if rates is None: return

    for offer in offers:
        if "retail_price" not in offer: continue
        price = offer["retail_price"]
        currency = offer["currency"]

        price_NOK = convert(price, currency, preferred_currency)

        list.append((price_NOK, extract_service_url(offer), location))

streaming_services_data = {}
renting_offers_data = []
buying_offers_data = []

with IncrementalBar(f"Searching for places to watch \"{title}\"", max=len(locales), suffix="%(index)d / %(max)d countries checked") as bar:
    for locale, location in locales:
        offers = requests.get(f"http://apis.justwatch.com/content/titles/{content_type}/{id}/locale/{locale}").json()

        bar.next()

        if "offers" not in offers: continue

        offers = offers["offers"]
        offers = [(offer, offer["monetization_type"]) for offer in offers]

        streaming_services = [extract_service_url(offer) for offer, type in offers if type == "flatrate"]
        renting_offers = [offer for offer, type in offers if type == "rent"]
        buying_offers = [offer for offer, type in offers if type == "buy"]

        for streaming_service in streaming_services:
            if streaming_service not in streaming_services_data:
                streaming_services_data[streaming_service] = [location]
            elif location not in streaming_services_data[streaming_service]:
                streaming_services_data[streaming_service].append(location)

        extract_offers(renting_offers, renting_offers_data, location)
        extract_offers(buying_offers, buying_offers_data, location)

renting_offers_data = list(dict.fromkeys(renting_offers_data))
renting_offers_data.sort(key=lambda offer: offer[0])

buying_offers_data = list(dict.fromkeys(buying_offers_data))
buying_offers_data.sort(key=lambda offer: offer[0])

def is_prioritised(service):
    for prioritised_service in prioritised:
        if prioritised_service in service: return True
    return False

prioritised_services = [
        (service, locations) for service, locations in streaming_services_data.items()
        if is_prioritised(service)]

def print_service(service, locations):
    print(service)
    for location in locations:
        print(" " * 4 + location)

def wait_to_show_more():
    skip = input("Press ENTER to show more (\"s\" to skip) ") in ["s", "skip", "h", "n", "e", "end"]
    print("\033[A", end="\r\033[K")
    return skip

for service in prioritised_services:
    print_service(*service)
    skip = wait_to_show_more()
    if skip: break

print()

for service, locations in streaming_services_data.items():
    if is_prioritised(service): continue
    locations.sort()
    print_service(service, locations)
    skip = wait_to_show_more()
    if skip: break

def pad_string(string, length):
    return string + " " * (length - len(string))

def print_offers_data(headline, data):
    if len(data) == 0: return
    website_lens = [len(site) for _, site, __ in data]
    max_website_len = max(website_lens)

    print(f"\n{headline}\n")
    for i in range(len(data)):
        price, website, location = data[i]
        website_string = pad_string(website, max_website_len)
        print(f"{website_string}    for {price:.2f} {preferred_currency}, in {location}")
        if i % 3 == 0: 
            skip = wait_to_show_more()
            if skip: break

print_offers_data("RENTING OFFERS", renting_offers_data)
print_offers_data("BUYING OFFERS", buying_offers_data)
