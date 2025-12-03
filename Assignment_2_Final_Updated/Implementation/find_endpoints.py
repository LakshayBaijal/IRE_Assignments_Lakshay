import requests

base = "http://localhost:3000"
paths = [
    "", "api", "api/pages", "api/page", "pages", "page",
    "crawl", "crawler", "raw", "json", "data"
]

seed = "page_s1ns46p4"

for p in paths:
    url = f"{base}/{p}/{seed}".replace("//","/")
    try:
        r = requests.get(url, headers={"Accept":"application/json"}, timeout=3)
        print("\nURL:", url)
        print("Status:", r.status_code)
        text = r.text[:200].strip().replace("\n"," ")
        print("Body:", text[:150], ("..." if len(text)>150 else ""))
    except Exception as e:
        print("\nURL:", url, " -> ERROR:", e)
