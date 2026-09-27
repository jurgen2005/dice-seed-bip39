#!/usr/bin/env python3
"""Independent cross-check of dist/dice-seed.html in headless Chromium.

For random dice rolls (12 and 24 words, with and without passphrase) it compares what the page shows with
independent Python libraries:
  words        = BIP39 from SHA-256(rolls)        (hashlib + embit)
  fingerprint  = BIP32 master fingerprint          (embit)
  addresses    = first 10 BIP-84 receive addresses (embit)
  zpub / xpub  = account key m/84'/0'/0'           (embit)
  Compact SeedQR decoded from a screenshot == entropy (zxing-cpp)
It also checks the in-page self-test badge and that the page makes no network requests.

pip install playwright embit zxing-cpp opencv-python-headless numpy && playwright install chromium
python3 tests/test_crosscheck.py
"""
import hashlib
import pathlib
import secrets

import cv2
import numpy as np
import zxingcpp
from embit import bip32, bip39, script
from embit.networks import NETWORKS
from playwright.sync_api import sync_playwright

PAGE = (pathlib.Path(__file__).resolve().parent.parent / "dist" / "dice-seed.html").as_uri()


def expected(rolls: str, words_n: int, pp: str):
    ent = hashlib.sha256(rolls.encode()).digest()[: 16 if words_n == 12 else 32]
    words = bip39.mnemonic_from_bytes(ent)
    root = bip32.HDKey.from_seed(bip39.mnemonic_to_seed(words, pp))
    acc = root.derive("m/84h/0h/0h")
    addrs = [script.p2wpkh(acc.derive([0, i]).key).address(NETWORKS["main"]) for i in range(10)]
    pub = acc.to_public()
    return ent, words.split(), root.my_fingerprint.hex(), addrs, pub.to_base58(NETWORKS["main"]["zpub"]), pub.to_base58(NETWORKS["main"]["xpub"])


def main() -> None:
    fails = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(locale="en-US", viewport={"width": 1100, "height": 900})
        errors, requests = [], []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("request", lambda r: requests.append(r.url) if not r.url.startswith(("file:", "data:")) else None)
        page.goto(PAGE)
        badge = page.inner_text("#badgeTest")
        print("badge:", badge)
        fails += "OK" not in badge
        for words_n, n_rolls, pp in [(12, 100, ""), (12, 150, "TREZOR"), (24, 199, ""), (24, 300, "correct horse")]:
            rolls = "".join(secrets.choice("123456") for _ in range(n_rolls))
            page.check(f'input[name=len][value="{words_n}"]')
            page.fill("#rolls", rolls)
            if page.is_visible("#confirmWrap"):
                page.check("#confirmStrong")
            page.click("#btnGenerate")
            page.wait_for_selector("#result:not(.hidden)")
            page.fill("#pp", pp)
            page.wait_for_function("() => /^[0-9a-f]{8}$/.test(document.getElementById('fpVal').textContent)")
            page.wait_for_timeout(300)
            ent, words, fp, addrs, zpub, xpub = expected(rolls, words_n, pp)
            got_words = [w.split(".")[-1].strip() for w in page.eval_on_selector_all("#words .word", "e => e.map(x => x.textContent)")]
            got_addrs = page.eval_on_selector_all(".addrrow span", "e => e.map(x => x.textContent)")
            qr = zxingcpp.read_barcodes(cv2.imdecode(np.frombuffer(page.locator("#qrbox").screenshot(), np.uint8), cv2.IMREAD_GRAYSCALE))
            checks = {
                "words": got_words == words,
                "fingerprint": page.inner_text("#fpVal") == fp,
                "addresses": got_addrs == addrs,
                "zpub": page.inner_text("#xpZpub") == zpub,
                "xpub": page.inner_text("#xpXpub") == xpub,
                "SeedQR": bool(qr) and qr[0].bytes == ent,
            }
            bad = [k for k, v in checks.items() if not v]
            fails += len(bad)
            print(f"{words_n} words, {n_rolls} rolls, passphrase={'yes' if pp else 'no'}: {'OK' if not bad else 'FAIL ' + ', '.join(bad)}")
        browser.close()
    print("page errors:", errors or "none", "| network requests:", requests or "none")
    fails += len(errors) + len(requests)
    print("RESULT:", "PASS" if not fails else f"FAIL ({fails})")
    raise SystemExit(1 if fails else 0)


if __name__ == "__main__":
    main()
