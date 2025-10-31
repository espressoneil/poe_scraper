# This successfully upgraded but was just a simple HTTPConnection with the same headers. I made this using https://curlconverter.com/python-httpclient/.
# To use it as an example, I had to strip out the cookie that contained the posessid and cf_key that you can grab from the network tab.

import http.client

conn = http.client.HTTPConnection('www.pathofexile.com')
headers = {
    'Upgrade': 'websocket',
    'Origin': 'https://www.pathofexile.com',
    'Cache-Control': 'no-cache',
    'Accept-Language': 'en-US,en;q=0.9',
    'Pragma': 'no-cache',
    'Connection': 'Upgrade',
    'Sec-WebSocket-Key': 'WFVqHwrrj360aWjf1AoQ9A==',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
    'Sec-WebSocket-Version': '13',
    'Sec-WebSocket-Extensions': 'permessage-deflate; client_max_window_bits',
    'Cookie': 'REDACTED',
}
conn.request('GET', '/api/trade2/live/poe2/Standard/Yp99gV3DiY', headers=headers)
response = conn.getresponse()
print(f"Status: {response.status} - {response.reason}")

# Print all headers
print("Headers:")
for header, value in response.getheaders():
    print(f"  {header}: {value}")

print("Body:")
try:
    body = response.read().decode('utf-8')
    print(body)
except UnicodeDecodeError:
    # Handle cases where the body might not be UTF-8 decodable
    body = response.read()
    print(f"Binary body (not UTF-8 decodable): {body}")

conn.close()