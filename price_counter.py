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

def GetJSONFromFile(filename):
    with open(filename, 'r') as file:
        hash_table = json.load(file)
    return hash_table

def get_all_files(directory):
    files = glob.glob(os.path.join(directory, "output_*.json"))
    return files
    latest_file = max(files, key=os.path.getmtime, default=None)
    return latest_file

def get_file_price_map(file):
    priced_ids = {}
    if file:
        priced_ids = GetJSONFromFile(file)
        return priced_ids
    return {}



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

while True:
    #print("Last file", find_latest_file("json_outputs"))
    #prior_ids = get_last_ids("json_outputs")
    files = get_all_files("json_outputs")
    
    for file in files:
        priced_ids = get_file_price_map(file)
        total = 0
        for key, value in priced_ids.items():
            total += len(value)
        print(file, total)
        print(file, {key: len(value) for key, value in priced_ids.items()})
    break
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




