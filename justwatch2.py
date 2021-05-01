import requests
from currency_converter import convert

locales = requests.get("http://apis.justwatch.com/content/locales/state").json()
locales = [(locale["full_locale"], locale["country"]) for locale in locales]

exchange_rates = {}

query = "south park"
query = query.replace(" ", "%20")
search_body = f"%7B\"page_size\":5,\"page\":1,\"query\":\"{query}\",\"content_types\":[\"movie\",\"show\"]%7D"

query_result = requests.get(f"https://apis.justwatch.com/content/titles/pt_BR/popular?language=en&body={search_body}").json()

id = query_result["items"][0]["id"]
content_type = query_result["items"][0]["object_type"]

def simplify_url(url):
    split = url.split("/")
    for part in split:
        if '.' in part: return part
    raise ValueError(f"{url} could not be simplified")

def extract_service_url(offer):
    return simplify_url(list(offer["urls"].values())[0])

def extract_offers(offers, list, location):
    for offer in offers:
        if "retail_price" not in offer: continue
        price = offer["retail_price"]
        currency = offer["currency"]

        price_NOK = convert(price, currency, "NOK")

        list.append((price_NOK, extract_service_url(offer), location))

streaming_services_data = {}
renting_offers_data = []
buying_offers_data = []

for locale, location in locales:
    offers = requests.get(f"http://apis.justwatch.com/content/titles/{content_type}/{id}/locale/{locale}").json()
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

prioritised = ("viaplay", "netflix", "tv2")

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
    input("Press ENTER to show more")
    print("\033[A", end="\r\033[K")

for service in prioritised_services:
    print_service(*service)
    wait_to_show_more()

print()

for service, locations in streaming_services_data.items():
    if is_prioritised(service): continue
    locations.sort()
    print_service(service, locations)
    wait_to_show_more()

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
        print(f"{website_string}    for {price:.2f} kr, in {location}")
        if i % 3 == 0: wait_to_show_more()

print_offers_data("RENTING OFFERS", renting_offers_data)
print_offers_data("BUYING OFFERS", buying_offers_data)

# DONE: show renting offers with padding
# DONE: wait to show more for each renting offer
# DONE: do the same for buying offers
# DONE: implement search
# TODO: sys args for search query and streaming service
# TODO: options to skip category when printing
# DONE: automatically update the API key
