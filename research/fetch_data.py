"""Download Bitget USDT-FUTURES 1H candles and funding history (public endpoints) to research/data/."""
import csv, json, sys, time, urllib.request, urllib.parse

BASE = "https://api.bitget.com"
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
HOUR = 3600_000


def get(path, **params):
    url = BASE + path + "?" + urllib.parse.urlencode(params)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                body = json.loads(r.read())
            if body.get("code") == "00000":
                return body["data"]
            err = body
        except Exception as e:  # noqa: BLE001
            err = e
        time.sleep(1 + attempt)
    raise RuntimeError(f"{path} {params}: {err}")


def fetch_candles(symbol, start_ms, end_ms):
    rows = {}
    cur_end = end_ms
    while cur_end > start_ms:
        cur_start = max(start_ms, cur_end - 190 * HOUR)
        data = get("/api/v2/mix/market/history-candles", symbol=symbol, productType="usdt-futures",
                   granularity="1H", startTime=cur_start, endTime=cur_end, limit=200)
        for r in data:
            rows[int(r[0])] = r
        cur_end = cur_start
        time.sleep(0.06)
    return [rows[k] for k in sorted(rows)]


def fetch_funding(symbol):
    rows = {}
    page = 1
    while True:
        data = get("/api/v2/mix/market/history-fund-rate", symbol=symbol, productType="usdt-futures",
                   pageSize=100, pageNo=page)
        if not data:
            break
        for r in data:
            rows[int(r["fundingTime"])] = r
        page += 1
        if page > 40:
            break
        time.sleep(0.06)
    return [rows[k] for k in sorted(rows)]


def main():
    now = int(time.time() * 1000) // HOUR * HOUR
    start = now - int(2.6 * 365 * 24) * HOUR
    for s in SYMBOLS:
        c = fetch_candles(s, start, now)
        with open(f"data/{s}_1H.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ts", "open", "high", "low", "close", "base_vol", "quote_vol"])
            w.writerows(c)
        fr = fetch_funding(s)
        with open(f"data/{s}_funding.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ts", "rate"])
            for r in fr:
                w.writerow([r["fundingTime"], r["fundingRate"]])
        print(s, "candles", len(c), c[0][0], c[-1][0], "funding", len(fr), fr[0]["fundingTime"] if fr else None, fr[-1]["fundingTime"] if fr else None)


if __name__ == "__main__":
    main()
