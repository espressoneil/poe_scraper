import urllib.request
import urllib.parse
import json
import http.cookiejar
import gzip
import io
import glob
import time
import os
from datetime import datetime, timezone


# URL for the API request
items_url = "https://www.pathofexile.com/api/trade2/search/poe2/Standard"
fetch_url="https://www.pathofexile.com/api/trade2/fetch"

# Cookies: POESESSID AND CF_CLEARANCE ARE REDACTED AND NEED TO BE GRABBED FROM POE TRADE WEBSITE.
# todo: use secrets file.
cookie_jar = http.cookiejar.CookieJar()
cookie_jar.set_cookie(http.cookiejar.Cookie(
    version=0,
    name="POESESSID",
    value="...",
    port=None,
    port_specified=False,
    domain=".pathofexile.com",
    domain_specified=True,
    domain_initial_dot=True,
    path="/",
    path_specified=True,
    secure=False,
    expires=None,
    discard=True,
    comment=None,
    comment_url=None,
    rest={},
    rfc2109=False,
))
cookie_jar.set_cookie(http.cookiejar.Cookie(
    version=0,
    name="cf_clearance",
    value="...",
    port=None,
    port_specified=False,
    domain=".pathofexile.com",
    domain_specified=True,
    domain_initial_dot=True,
    path="/",
    path_specified=True,
    secure=False,
    expires=None,
    discard=True,
    comment=None,
    comment_url=None,
    rest={},
    rfc2109=False,
))

# Set up an opener with cookies
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

# Headers
headers = {
    "authority": "www.pathofexile.com",
    "method": "POST",
    "path": "/api/trade2/search/poe2/Standard",
    "scheme": "https",
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "origin": "https://www.pathofexile.com",
    "priority": "u=1, i",
    "referer": "https://www.pathofexile.com/trade2/search/poe2/Standard",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-arch": '"x86"',
    "sec-ch-ua-bitness": '"64"',
    "sec-ch-ua-full-version": '"131.0.6778.265"',
    "sec-ch-ua-full-version-list": '"Google Chrome";v="131.0.6778.265", "Chromium";v="131.0.6778.265", "Not_A Brand";v="24.0.0.0"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": '""',
    "sec-ch-ua-platform": '"Windows"',
    "sec-ch-ua-platform-version": '"15.0.0"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "x-requested-with": "XMLHttpRequest",
    "content-type": "application/json",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
}

def GetItemData(ids, trade_id):
    params = {
        'query': trade_id,
        'realm': 'poe2',
    }
    #request = urllib.request.Request(full_fetch_url, headers=headers, method="POST")
    items = []
    for i in range(0, len(ids), 10):
        batch = ids[i:i+10]
        full_fetch_url = fetch_url + '/' + ','.join(batch)
        #print("fetching", len(batch), "ids")
        response, item_data = MakeRequest(full_fetch_url, None, "GET")

        wait = parse_rate_limit_ip_state(response.headers)
        #print("sleeping", wait)
        time.sleep(wait)
        if item_data is None:
            return None
        items.extend(item_data['result'])

    return items




def ConstructGetIDsQuery(price_range = None, sort_field = None, sort_direction = 'asc', corrupted = None):
    json_data={"query":
               {"status":{"option":"securable"},
                "name":"Against the Darkness",
                "type":"Time-Lost Diamond",
                "stats":[{"type":"and","filters":[],"disabled":False}],
                "filters":{
                    "trade_filters":{"filters":{"price":{"option":"divine","min":5,"max":5}}},
                    "misc_filters": {"filters": {"identified": {"option": "true"}}}}}}
    

    if sort_field:
        json_data['sort'] = {}
        json_data['sort'][sort_field] = sort_direction

    if price_range:
        low = price_range[0]
        high = price_range[1]
        json_data['query']['filters'] = {
            'trade_filters': {
                'filters': {
                    'price': {
                        'min': low,
                        'max': high,
                        'option': 'divine',
                    },
                },
                'disabled': False,
            }
        }
    if corrupted is not None:
        json_data['query']['filters']['misc_filters'] = {
            'filters': {
                'corrupted': {
                   'option': corrupted
                }
            }
        }
        #print(price_range, sort_field, sort_direction)
    #print(json_data)
    return json_data

def parse_rate_limit_ip_state(headers):
    # Split the rate limit states by commas

    rate_limits = headers['X-Rate-Limit-Account'] + ',' + headers['X-Rate-Limit-Ip']
    rate_limits_state = headers['X-Rate-Limit-Account-State'] + ',' + headers['X-Rate-Limit-Ip-State']
    #print(rate_limits, rate_limits_state)
    rate_limits_windows = rate_limits_state.split(',')
    
    #default_wait = 0.5
    
    # Initialize the max wait time
    max_wait_time = 0
    #limits = {5:3, 10:8, 60:15, 300:60}
    #wait_times = {5:2, 10:2, 60:4, 300:5}

    limits = {}
    reset_periods = {}

    for window in rate_limits.split(','):
        #print(window)
        limit, window_period, _naughty_time = map(int, window.split(':'))
        limits[window_period] = limit
        reset_periods[window_period] = window_period
    


    # Iterate over each window
    for window in rate_limits_state.split(','):
        # Split each window into its components (remaining requests, total requests, reset time)
        used, window_period, _ = map(int, window.split(':'))
        limit = limits[window_period]
        reset_period = reset_periods[window_period]

        # assume that all requests slept afterward for the average wait.
        average_wait = float(window_period) / limit
        remaining = float(limit - used)
        estimated_reset = reset_period - (average_wait * used)

        # Still spread remaining requests over the remaining time.
        estimated_wait = estimated_reset / remaining
        
        # Track the longest wait time across all windows
        max_wait_time = max(max_wait_time, estimated_wait)
        #print(window, "limit:", limit, "reset:", reset_period, "limit:", average_wait, remaining, "estimate:", estimated_wait, "max wait:", max_wait_time)
    
    return max_wait_time



def MakeRequest(url, data, method):
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    decoded = None
    response = None
    # Allow three retries
    for i in range(0,5):
        error = False
        try:
            response = opener.open(request)
            contents = response.read()
            print(contents)
    
            # Check if the response is compressed
            encoding = response.headers.get("Content-Encoding", "")
        
            if "gzip" in encoding:
                # Decompress gzip
                buf = io.BytesIO(contents)
                decompressed = gzip.GzipFile(fileobj=buf).read()
                decoded = decompressed.decode("utf-8")
            else:
                # If not compressed
                decoded = contents.decode("utf-8")
            print(response, json.loads(decoded))
            return [response, json.loads(decoded)]
        
        except urllib.error.HTTPError as e:
            error = True
            print("HTTPError", e)
            print(e.headers)
            if 'Retry-After' in e.headers:
                error = False
                retry = int(e.headers['Retry-After'])
                print("Rate limited, sleeping: ", retry)
                time.sleep(retry)
        except urllib.error.URLError as e:
            error = True
            print("URLError", e)
            print(e.headers)
        except Exception as e:
            error = True
            print(f"An error occurred: {e}")
        if error:
            time.sleep(15)
    return [None, None]
    

def GetIDs(**kwargs):
    # Create a request
    data = ConstructGetIDsQuery(**kwargs)
    # Sometimes this will just return "False" and I don't know why.
    while True:
        response, decoded = MakeRequest(items_url, Encode(data), "POST")
        if not decoded:
            return [None, None, None]
    
        wait = parse_rate_limit_ip_state(response.headers)
        time.sleep(wait)
        if decoded['total'] is False:
            print(decoded)
        elif not decoded['total'] is False:
            break

    return [decoded['result'], decoded['total'], decoded['id']]

def Encode(json_data):
    return json.dumps(json_data).encode("utf-8")

def InsertItems(priced_ids, item_data):
    for item in item_data:
        if not item:
            continue
        try:
            price = item['listing']['price']['amount']
            itemid = item['id']
            if not price in priced_ids:
                priced_ids[price] = {}
            priced_ids[price][itemid] = {}
            priced_ids[price][itemid]['item'] = item
            priced_ids[price][itemid]['time'] = datetime.now(timezone.utc).isoformat()
        except:
            print(item)
            return


def WriteJSONOutput(timestamp, output_dir, hash_table):
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Construct the output file path
    output_file = os.path.join(output_dir, f"output_{timestamp}.json")

    # Write the hash table to the JSON file
    with open(output_file, "w") as json_file:
        json.dump(hash_table, json_file, indent=4)

def GetJSONFromFile(filename):
    with open(filename, 'r') as file:
        hash_table = json.load(file)
    return hash_table

def find_latest_file(directory):
    files = glob.glob(os.path.join(directory, "output_*.json"))
    latest_file = max(files, key=os.path.getmtime, default=None)
    return latest_file

def create_key_set(priced_ids):
    all_ids = set()
    for value in priced_ids:
        value_ids = priced_ids[value].keys()
        all_ids.update(value_ids)
    return all_ids

def get_last_ids(directory):
    file = find_latest_file(directory)
    priced_ids = {}
    if file:
        priced_ids = GetJSONFromFile(file)
    all_ids = create_key_set(priced_ids)

    print(len(all_ids), "ids in last file.")
    return all_ids



def FindAllDiamonds(corrupted):
    
    priced_ids = {}
    all_ids = set()
    current_price = 1
    max_price = 1000
    while current_price < max_price:
        total_at_price = len(priced_ids[current_price]) if current_price in priced_ids else 0
        price_max = current_price if total_at_price >= 100 else max_price
        sort_field = None if total_at_price >= 100 else 'price'
        ids, total, trade_id = GetIDs(price_range=[current_price, price_max], sort_field=sort_field, corrupted=corrupted)
        exhausted = len(ids) > 0 and len(ids) < 100
        new_ids = [candidate_id for candidate_id in ids if candidate_id not in all_ids]
        #print("Found", len(ids), "new ids")
        all_ids.update(ids)
        print("current", current_price, "total", total, "trade_id", trade_id)
        if len(new_ids) > 0:
            last_id = new_ids[-1]
        
            item_data = GetItemData(new_ids, trade_id)
            InsertItems(priced_ids, item_data)
            #print(response)
            #print(len(item_data), 'results')
            #response, last_item_data = GetItemData([last_id], trade_id)
            new_price = item_data[-1]['listing']['price']['amount']

        elif len(ids) == 0:
            print("Reached the end, no results found:", current_price)
            break
    
        #print(response)
            #print(new_price)
        #print(last_item_data['result'])
        new_price = current_price
        #bug: sometimes an item is repriced between when it is fully fetched and not.
        last_price = 0
        #print({key: len(value) for key, value in priced_ids.items()})
        last_price = sorted(priced_ids)[0]
        # Pick the new price where 10 values are >= new_price. This avoids the issue of racing reprices causing accidental skips. Erase top results that are above current price.
        total_above_price = 0
        for price in sorted(priced_ids, reverse=True):
            total_above_price += len(priced_ids.get(price, {}))
            new_price = price
            if total_above_price >= 5 or exhausted:
                break
            if new_price == current_price + 1 and len(priced_ids.get(current_price, {})) < 100:
                print("Special case. A few results returned at current_price+1, but not enough to proceed normally.")
                break
        total_at_price = len(priced_ids.get(current_price, {}))
        print(str(total_at_price) + "/" + str(total), {key: len(value) for key, value in priced_ids.items()})
        if new_price > current_price:
            print("continuing from", current_price, "to", new_price)
            current_price = new_price
            continue
        elif new_price < current_price:
            print("Somehow new price is lower!!")
    
        #print(total_at_price + "/" + total, {key: len(value) for key, value in priced_ids.items()})
        if total_at_price + total/20 >= total:
            print("reached:", total_at_price, "out of", total, "for", current_price, "so moving on to", current_price+1)
            current_price = current_price + 1

    return priced_ids

import random

def GetAllDiamonds():
  while True:
      #print("Last file", find_latest_file("json_outputs"))
      prior_ids = get_last_ids("json_outputs")
      start_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
      print("Finding all corrupted jewels")
      corrupted_priced_ids = FindAllDiamonds(corrupted=True)
      #WriteJSONOutput(start_timestamp, "json_outputs", corrupted_priced_ids)
      print("Finding all uncorrupted jewels")
      priced_ids = FindAllDiamonds(corrupted=False)
      for price in corrupted_priced_ids:
          for itemid in corrupted_priced_ids[price]:
              if not price in priced_ids:
                  priced_ids[price] = {}
              priced_ids[price][itemid] = corrupted_priced_ids[price][itemid]
      new_ids = create_key_set(priced_ids)
      missing_ids = prior_ids - new_ids
      print(len(new_ids), len(prior_ids), "new/old item counts.", len(missing_ids), "items are in the old set but not the new set.")

      ids, total, trade_id = GetIDs(price_range=[1, 1000])
      missing_items = GetItemData(list(missing_ids), trade_id)
      print(len(missing_items), "out of", len(missing_ids), "were found after looking them up.")
      if len(missing_items) > 0:
          print(random.sample(missing_items, 10))
          InsertItems(priced_ids, missing_items)
      WriteJSONOutput(start_timestamp, "json_outputs", priced_ids)





GetIDs(price_range=[1, 200], sort_field='price', corrupted=False)
