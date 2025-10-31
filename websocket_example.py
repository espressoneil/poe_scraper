# ws_example.py
import asyncio
import json
import logging
import io
import websockets
import urllib.request
import urllib.parse
import gzip
import http.cookiejar
import time




# enable debug logging for more handshake detail
#logging.basicConfig(level=logging.DEBUG)
#logging.getLogger("websockets").setLevel(logging.DEBUG)
#logging.getLogger("websockets.protocol").setLevel(logging.DEBUG)

ABYSSAL = "Rise of the Abyssal"
STANDARD = "Standard"
LEAGUE = ABYSSAL

REALM = "poe2"
ABOVE_DIVINE = "kK2Lj9wu5"
ABOVE_TEN_DIVINE = "DEeREzwt5"
HH_UNDER_TEN = "bZ65EKOSL"
HH_EXALTS = "ZQGknjECQ"

SEARCH_QUERY = ABOVE_TEN_DIVINE
# SEARCH_ID = "Yp99gV3DiY"   # use the exact id/path you validated with http.client
WSS_URL = f"wss://www.pathofexile.com/api/trade2/live/poe2/{LEAGUE}/{SEARCH_QUERY}"

FETCH_URL= "https://www.pathofexile.com/api/trade2/fetch/{ITEM}?query={ABOVE_DIVINE}&realm={REALM}"
WHISPER_URL= "https://www.pathofexile.com/api/trade2/whisper"



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
    "user-agent": UA
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

def MakeRequest(url, data, headers, method):
    request = urllib.request.Request(url, data=data, headers=get_headers, method=method)
    decoded = None
    response = None
    # Allow three retries
    for i in range(0,5):
        error = False
        try:
            response = opener.open(request)
            contents = response.read()
            #print(contents)
    
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
            #print(response, json.loads(decoded))
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

async def main():
    try:
        #print(WSS_URL, headers)
        async with websockets.connect(
            WSS_URL,
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

              if last_fetch + 5 > time.time():
                print("Skipping fetch, too soon.")
                continue

              last_fetch = time.time()
              fetch = FETCH_URL.format(ITEM=loaded['result'], ABOVE_DIVINE=ABOVE_DIVINE, REALM=REALM)
              #print("fetch url: ", fetch)
              _, item_data = MakeRequest(fetch, None, get_headers, "GET")
              
              if 'result' not in item_data or len(item_data['result']) == 0 or 'listing' not in item_data['result'][0]:
                print("Result not found in item data.")
                continue
              listing = item_data['result'][0]['listing']
              print("item listing: ", listing)
              x, y = listing['stash']['x'], listing['stash']['y']
              #print("x, y: ", x, y)
              #print("listing:", listing)

              hideout_token = listing['hideout_token']
              #print("hideout token: ", hideout_token)

              whisper_data = {"continue": True, "token": hideout_token}
              whisper_url = WHISPER_URL
              #print(whisper_url)

              response, item_data = MakeRequest(whisper_url, Encode(whisper_data), get_headers, "POST")
              #print(response, item_data)
              if not 'success' in item_data or item_data['success'] == 'false':
                print("UNEXPECTED FATAL ERROR: Unsuccessful or unknown success for item_data: ", item_data)
                print("IF THIS ACTUALLY HAPPENS THE DEV SHOULD IMPLEMENT A RETRY AFTERWARD.")
                exit(1)
                continue


    except websockets.exceptions.InvalidStatus as e:
        # InvalidStatus includes status code and headers from server
        print("InvalidStatus:", e)
    except Exception as e:
        print("Other error:", type(e), e)




if __name__ == "__main__":
    asyncio.run(main())




