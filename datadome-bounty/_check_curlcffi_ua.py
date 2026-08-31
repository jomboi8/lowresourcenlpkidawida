from curl_cffi.requests import Session

s = Session(impersonate="chrome124")
r = s.get("https://httpbin.org/headers")
print(r.status_code)
print(r.text)
