# ws_example.py
import asyncio
import json
import logging
import io
from re import I
import websockets
import urllib.request
import urllib.parse
import gzip
import http.cookiejar
import time

from concurrent.futures import ThreadPoolExecutor


# enable debug logging for more handshake detail
#logging.basicConfig(level=logging.DEBUG)
#logging.getLogger("websockets").setLevel(logging.DEBUG)
#logging.getLogger("websockets.protocol").setLevel(logging.DEBUG)

ABYSSAL = "Rise%20of%20the%20Abyssal"
STANDARD = "Standard"
LEAGUE = ABYSSAL

REALM = "poe2"
ABOVE_DIVINE = "kK2Lj9wu5"
ABOVE_TEN_DIVINE = "DEeREzwt5"
ABOVE_HUNDRED_DIVINE = "6q6valbIG"
HH_UNDER_TEN = "bZ65EKOSL"
HH_EXALTS = "ZQGknjECQ"
ANY_TABLET = "pL5bOgwu0"
ANY_TABLET_UNDER_10EX = "rEwy8wmcQ"

SEARCH_QUERY = ABOVE_TEN_DIVINE
# SEARCH_ID = "Yp99gV3DiY"   # use the exact id/path you validated with http.client
WSS_URL_TEMPLATE = f"wss://www.pathofexile.com/api/trade2/live/poe2/{LEAGUE}/{{TRADE_ID}}"
REFERER_TEMPLATE = f"https://www.pathofexile.com/trade2/search/poe2/{LEAGUE}/{{TRADE_ID}}/live"
#print(WSS_URL_TEMPLATE.format(SEARCH_QUERY=SEARCH_QUERY))
#WSS_URL1 = f"wss://www.pathofexile.com/api/trade2/live/poe2/{LEAGUE}/{ANY_PRECURSOR_TABLET}"
#WSS_URL2 = f"wss://www.pathofexile.com/api/trade2/live/poe2/{LEAGUE}/{ABOVE_HUNDRED_DIVINE}"

FETCH_URL= "https://www.pathofexile.com/api/trade2/fetch/{ITEM}?query={TRADE_ID}&realm={REALM}"
WHISPER_URL= "https://www.pathofexile.com/api/trade2/whisper"

#TRADE_IDS = [ANY_TABLET, ABOVE_HUNDRED_DIVINE]
TRADE_IDS = [ANY_TABLET_UNDER_10EX]


# Put your real UA and cookies here (or read from env vars)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"

# Open the file in write mode and dump the dictionary to it
with open("secrets.json", "r") as f:
    secrets = json.load(f)

#print(secrets)
MY_POESESSID = secrets["my_poesessid"]
BOT_POESESSID = secrets["bot_poesessid"]
MY_CF_CLEARANCE = secrets["bot_cf_clearance"]
BOT_CF_CLEARANCE = secrets["bot_cf_clearance"]

POESESSID = BOT_POESESSID
CF_CLEARANCE = BOT_CF_CLEARANCE
COOKIES = f"POESESSID={POESESSID}; cf_clearance={CF_CLEARANCE}"

headers = [
    ("Origin", "https://www.pathofexile.com"),
    ("User-Agent", UA),
    ("Accept-Language", "en-US,en;q=0.9"),
    ("Accept-Encoding", "gzip, deflate, br, zstd"),
    ("Cache-Control", "no-cache"),
    ("Pragma", "no-cache"),
    ("Sec-WebSocket-Extensions", "permessage-deflate; client_max_window_bits"),
    ("Cookie", COOKIES),
]

get_headers = {
    #"authority": "www.pathofexile.com",
    "method": "GET",
    #"path": f"/api/trade2/search/poe2/{LEAGUE}",
    #"scheme": "https",
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "origin": "https://www.pathofexile.com",
    "priority": "u=1, i",
    #"referer": f"https://www.pathofexile.com/trade2/search/poe2/{LEAGUE}",
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
    "user-agent": UA,
    "cookie": COOKIES,
}


whisper_headers = get_headers

cookie_jar = http.cookiejar.CookieJar()
cookie_jar.set_cookie(http.cookiejar.Cookie(
    version=0,
    name="POESESSID",
    value=POESESSID,
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
    value=CF_CLEARANCE,
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

def Encode(json_data):
    return json.dumps(json_data).encode("utf-8")

def MakeRequest(url, data, headers, method, retries=1):
    request = urllib.request.Request(url, data=data, headers=get_headers, method=method)
    decoded = None
    response = None
    error = False
    for i in range(0,retries):
        if error:
          time.sleep(15)
        try:
            response = opener.open(request)
            contents = response.read()
    
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
            return [response, json.loads(decoded)]
        
        except urllib.error.HTTPError as e:
            error = True
            print(f"bad request, url: {url}, data: {data}, headers: {headers}, method: {method}")
            print("HTTPError", e)
            #print(e.headers)
            if 'Retry-After' in e.headers:
                error = False
                retry = int(e.headers['Retry-After'])
                print("Rate limited, sleeping: ", retry)
                time.sleep(retry)
        except urllib.error.URLError as e:
            error = True
            print("URLError", e)
            #print(e.headers)
        except Exception as e:
            error = True
            print(f"An error occurred: {e}")
        
    return [None, None]

async def session_once(trade_id, work_q: asyncio.Queue):
    wss_url = WSS_URL_TEMPLATE.format(TRADE_ID=trade_id)
    print("Creating websockets for trade_id: ", trade_id)
    try:
        async with websockets.connect(
            wss_url,
            additional_headers=headers,   # websockets >=12/15 uses this name
            ping_interval=None,
            ping_timeout=None,
            max_size=10_000_000,
            # open_timeout=10,  # optional
        ) as ws:
            last_fetch = time.time() - 5
            async for msg in ws:
              loaded = json.loads(msg)
              if 'result' not in loaded:
                print(f"Ignoring message: {loaded}")
                continue

              if last_fetch + 6 > time.time():
                continue

              
              enqueue_time = time.time()
              await work_q.put({'trade_id': trade_id, 'loaded': loaded, 'enqueue_time': enqueue_time})



    finally:
      try:
        print(f"[{wss_url}] closed (code={ws.close_code}, reason={ws.close_reason})")
      except Exception:
        print(f"[{wss_url}] closed")


_single_worker_pool = ThreadPoolExecutor(max_workers=1)


async def worker(work_q: asyncio.Queue):
    loop = asyncio.get_running_loop()
    last_fetch = time.time() - 30
    while True:
        if last_fetch + 2 > time.time():
            last_fetch - time.time() + 2
            sleep_for = (last_fetch + 2) - time.time()
            #print(f"Sleeping for {sleep_for}s until fetching again.")
            await asyncio.sleep(sleep_for)
        job = await work_q.get()
        trade_id     = job["trade_id"]
        loaded       = job["loaded"]
        enqueue_time = job["enqueue_time"]
        delay = time.time() - enqueue_time
        #print (trade_id,  " delay: ", time.time() - enqueue_time)
        try:
          # POE item encodings are only valid for up to 3 seconds, so we have to toss them if we're too slow.
          if enqueue_time + 3 < time.time():
            print("work item from >3s ago, skipping.")
            continue          

          fetch = FETCH_URL.format(ITEM=loaded['result'], TRADE_ID=trade_id, REALM=REALM)
          resp, item_data = await loop.run_in_executor(_single_worker_pool, MakeRequest, fetch, None, get_headers, "GET")
          last_fetch = time.time()

          if resp is None or item_data is None:
            print(f"Fetch failed, delay was {delay}")
            continue
          if 'result' not in item_data:
            print("Result not found in item data:", item_data)
            continue
          result = item_data['result']
          
          #print("result: ", result)
          length = len(result)
          print("item_data keys: ", item_data.keys())
          print("Looping over result: ", result)
          for ind in range(0, length):
            if ind > 0:
              time.sleep(3)
            if 'listing' not in result[ind]:
              print("listing not found in item data: ", item_data)
              continue
            listing = result[ind]['listing']
            item = result[ind]['item']
              
            print(f"trade_id: {trade_id}, delay: {delay:.2f}, ind: {ind}, item: {item['baseType']}, from account: ", listing['account']['name'])
            x, y = listing['stash']['x'], listing['stash']['y']

            hideout_token = listing['hideout_token']

            whisper_data = {"continue": True, "token": hideout_token}
            whisper_url = WHISPER_URL
            

            response, item_data = await loop.run_in_executor(_single_worker_pool, MakeRequest, whisper_url, Encode(whisper_data), get_headers, "POST")
            if response is None or item_data is None:
              print("Request failed... skipping.")
              continue
            print(response, item_data)
            if not 'success' in item_data or item_data['success'] == 'false':
              print("UNEXPECTED FATAL ERROR: Unsuccessful or unknown success for item_data: ", item_data)
              print("IF THIS ACTUALLY HAPPENS THE DEV SHOULD IMPLEMENT A RETRY AFTERWARD.")
              exit(1)
              continue

          last_fetch = time.time()

        finally:
          #print("Done with work q item")
          work_q.task_done()


async def session_forever(trade_id, work_q):
    #attempt = 0
    while True:
        try:
            await session_once(trade_id, work_q)
            print(f"[{trade_id}] Session cleanly ended, restarting connection.")
            # Reached only when the server closed (cleanly). Backoff and reconnect.
        except websockets.ConnectionClosed as e:
            print(f"[{trade_id}] ConnectionClosed: {e.code} {e.reason}")
        except websockets.exceptions.InvalidStatus as e:
            print(f"[{trade_id}] InvalidStatus: {e}")
        except (OSError, asyncio.TimeoutError) as e:
            print(f"[{trade_id}] network/connect error: {type(e).__name__}: {e}")

        # exponential backoff with cap
        #delay = min(RETRY_CAP, RETRY_BASE * (2 ** attempt))
        #attempt = min(attempt + 1, 10)
        await asyncio.sleep(5)




async def main():
    work_q = asyncio.LifoQueue(maxsize=100)  # backpressure; tweak as needed

    # launch all sessions concurrently
    tasks = [asyncio.create_task(session_forever(trade_id, work_q)) for trade_id in TRADE_IDS]

    worker_task = asyncio.create_task(worker(work_q))

    # wait for both to finish (or error)
    await asyncio.gather(*tasks, worker_task)

if __name__ == "__main__":
  print("running")
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    print("Interrupted.", flush=True)




