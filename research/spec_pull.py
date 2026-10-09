"""Pull live Bitget USDT-FUTURES contract spec for sleeve A symbols (public endpoints only)."""
import json, sys, time, urllib.request, urllib.parse

BASE = "https://api.bitget.com"
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]


def get(path, **params):
    url = BASE + path + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=20) as r:
        body = json.loads(r.read())
    if body.get("code") != "00000":
        raise RuntimeError(f"{path} {params} -> {body}")
    return body["data"]


def main():
    out = {"pulled_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "symbols": {}}
    for s in SYMBOLS:
        c = get("/api/v2/mix/market/contracts", productType="USDT-FUTURES", symbol=s)[0]
        t = get("/api/v2/mix/market/ticker", productType="USDT-FUTURES", symbol=s)[0]
        f = get("/api/v2/mix/market/current-fund-rate", productType="USDT-FUTURES", symbol=s)[0]
        d = get("/api/v2/mix/market/merge-depth", productType="USDT-FUTURES", symbol=s, limit="5")
        bid, ask = float(t["bidPr"]), float(t["askPr"])
        mid = (bid + ask) / 2
        out["symbols"][s] = {
            "contract": c, "ticker": t, "fund": f,
            "depth_top": {"bids": d.get("bids", [])[:3], "asks": d.get("asks", [])[:3]},
            "spread_bps": (ask - bid) / mid * 1e4,
            "spread_in_ticks": (ask - bid) / (float(c["priceEndStep"]) * 10 ** -int(c["pricePlace"])),
        }
    json.dump(out, open("out/live_spec.json", "w"), indent=1)
    print(json.dumps(out, indent=1)[:6000])


if __name__ == "__main__":
    main()
