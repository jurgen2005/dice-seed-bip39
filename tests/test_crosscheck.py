#!/usr/bin/env python3
"""Independent cross-check of dist/dice-seed.html in headless Chromium.

For random dice rolls and randomly shuffled card decks (12 and 24 words, with and without passphrase) it compares
what the page shows with independent Python libraries:
  words        = BIP39 from SHA-256(rolls or "AS TH 9D ...")   (hashlib + embit)
  fingerprint  = BIP32 master fingerprint          (embit)
  addresses    = first 10 BIP-84 receive addresses (embit)
  zpub / xpub  = account key m/84'/0'/0'           (embit)
  Compact SeedQR decoded from a screenshot == entropy (zxing-cpp)
Cards are entered by clicking the grid, by keyboard shortcuts and as pasted text; the card input checks
(duplicate, incomplete round, sorted deck) are exercised as well.
It also checks the in-page self-test badge and that the page makes no network requests.
Finally it serves the page over http:// (as on GitHub Pages) and checks the online trial mode: banner, TESTSEED marking
on every result, the warning at "enter existing seed", unchanged calculations, and that none of this shows as a local file.

pip install playwright embit zxing-cpp opencv-python-headless numpy && playwright install chromium
python3 tests/test_crosscheck.py
"""
import functools
import hashlib
import http.server
import pathlib
import secrets
import threading

import cv2
import numpy as np
import zxingcpp
from embit import bip32, bip39, script
from embit.networks import NETWORKS
from playwright.sync_api import sync_playwright

DECK = [r + s for s in "SHCD" for r in "A23456789TJQK"]
shuffle = secrets.SystemRandom().shuffle
DIST = pathlib.Path(__file__).resolve().parent.parent / "dist"
PAGE = (DIST / "dice-seed.html").as_uri()


def expected(rolls: str, words_n: int, pp: str):
    ent = hashlib.sha256(rolls.encode()).digest()[: 16 if words_n == 12 else 32]
    return expected_mnemonic(ent, pp)


def expected_mnemonic(ent: bytes, pp: str):
    words = bip39.mnemonic_from_bytes(ent)
    root = bip32.HDKey.from_seed(bip39.mnemonic_to_seed(words, pp))
    acc = root.derive("m/84h/0h/0h")
    addrs = [script.p2wpkh(acc.derive([0, i]).key).address(NETWORKS["main"]) for i in range(10)]
    pub = acc.to_public()
    return ent, words.split(), root.my_fingerprint.hex(), addrs, pub.to_base58(NETWORKS["main"]["zpub"]), pub.to_base58(NETWORKS["main"]["xpub"])


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


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

        # Playing cards: full shuffled deck(s), entered by clicking the grid, typing on the keyboard and pasting text
        page.click("#btnSource")
        for words_n, how, pp in [(12, "click", ""), (12, "keys", "TREZOR"), (24, "text", ""), (24, "click", "correct horse")]:
            page.check(f'input[name=len][value="{words_n}"]')
            page.click("#btnCardClear")
            rounds = 1 if words_n == 12 else 2
            cards = []
            for _ in range(rounds):
                deck = DECK[:]
                shuffle(deck)
                cards += deck
            if how == "text":
                page.fill("#cards", "\n".join(" ".join(c.replace("T", "10") for c in cards[i:i + 13]) for i in range(0, len(cards), 13)).lower())
            else:
                page.click("#cardRoundInfo")  # focus away from any input, so keystrokes go to the card shortcuts
                for c in cards:
                    if how == "click":
                        page.click(f'#cardGrid .cc[data-c="{c}"]')
                    else:
                        page.keyboard.press(c[0].lower())
                        page.keyboard.press(c[1].lower())
            if page.is_visible("#cardConfirmWrap"):
                page.check("#cardConfirmStrong")
            canon = " ".join(cards)
            checks = {"input text": page.eval_on_selector("#cards", "e => e.value.replace(/\\s+/g, ' ').trim().toUpperCase()").replace("10", "T") == canon}
            page.click("#btnGenerate")
            page.wait_for_selector("#result:not(.hidden)")
            page.fill("#pp", pp)
            page.wait_for_function("() => /^[0-9a-f]{8}$/.test(document.getElementById('fpVal').textContent)")
            page.wait_for_timeout(300)
            ent, words, fp, addrs, zpub, xpub = expected(canon, words_n, pp)
            got_words = [w.split(".")[-1].strip() for w in page.eval_on_selector_all("#words .word", "e => e.map(x => x.textContent)")]
            qr = zxingcpp.read_barcodes(cv2.imdecode(np.frombuffer(page.locator("#qrbox").screenshot(), np.uint8), cv2.IMREAD_GRAYSCALE))
            checks.update({
                "hashed input": page.text_content("#dRolls") == canon,
                "words": got_words == words,
                "fingerprint": page.inner_text("#fpVal") == fp,
                "addresses": page.eval_on_selector_all(".addrrow span", "e => e.map(x => x.textContent)") == addrs,
                "zpub": page.inner_text("#xpZpub") == zpub,
                "xpub": page.inner_text("#xpXpub") == xpub,
                "SeedQR": bool(qr) and qr[0].bytes == ent,
            })
            bad = [k for k, v in checks.items() if not v]
            fails += len(bad)
            print(f"cards: {words_n} words, {len(cards)} cards via {how}, passphrase={'yes' if pp else 'no'}: {'OK' if not bad else 'FAIL ' + ', '.join(bad)}")

        # Card input checks: duplicate blocks, incomplete round blocks, sorted deck warns, change after generating clears
        page.check('input[name=len][value="12"]')
        page.fill("#cards", " ".join(DECK[:51] + ["AS"]))
        dup_ok = page.is_disabled("#btnGenerate") and page.is_visible("#cardInvalidMsg")
        page.fill("#cards", " ".join(DECK[:51]))
        short_ok = page.is_disabled("#btnGenerate") and page.eval_on_selector_all("#cardGrid .cc:not([disabled])", "e => e.map(x => x.dataset.c)") == [DECK[51]]
        page.fill("#cards", " ".join(DECK))
        sorted_ok = page.is_visible("#cardConfirmWrap") and page.is_disabled("#btnGenerate")
        page.check("#cardConfirmStrong")
        page.click("#btnGenerate")
        page.wait_for_selector("#result:not(.hidden)")
        page.click("#btnSource")
        cleared_ok = page.is_hidden("#result")
        extra = {"duplicate blocks": dup_ok, "51 cards blocks, 1 left in grid": short_ok, "sorted deck needs confirmation": sorted_ok, "switching source clears result": cleared_ok}
        bad = [k for k, v in extra.items() if not v]
        fails += len(bad)
        print("card input checks:", "OK" if not bad else "FAIL " + ", ".join(bad))

        # Opened as a local file: no trial-mode banner, warning, marking or title
        local = {
            "no trial banner": page.is_hidden("#bannerHosted"),
            "no seed-entry warning": page.is_hidden("#hostedSeedInWarn"),
            "no trial marking on result": page.is_hidden("#hostedBannerOut") and "TESTSEED" not in page.inner_text("#fpNote"),
            "title": "trial" not in page.title(),
        }
        bad = [k for k, v in local.items() if not v]
        fails += len(bad)
        print("local file, no trial mode:", "OK" if not bad else "FAIL " + ", ".join(bad))

        # Served over http:// (as on GitHub Pages): online trial mode
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(DIST)))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{srv.server_port}/dice-seed.html"
        hp = browser.new_page(locale="en-US", viewport={"width": 1100, "height": 900})
        hreq = []
        hp.on("pageerror", lambda e: errors.append("hosted: " + str(e)))
        hp.on("request", lambda r: hreq.append(r.url) if r.url != url and not r.url.startswith("data:") else None)
        hp.goto(url)
        hosted = {
            "self-test": "OK" in hp.inner_text("#badgeTest"),
            "trial banner": hp.is_visible("#bannerHosted") and hp.inner_text("#bannerHosted").startswith("ONLINE TRIAL VERSION"),
            "online banner replaced": hp.is_hidden("#bannerOnline"),
            "seed-entry warning": hp.is_visible("#hostedSeedInWarn"),
            "title": hp.title().endswith("online trial version"),
        }
        rolls = "".join(secrets.choice("123456") for _ in range(100))
        hp.check('input[name=len][value="12"]')
        hp.fill("#rolls", rolls)
        if hp.is_visible("#confirmWrap"):
            hp.check("#confirmStrong")
        hp.click("#btnGenerate")
        hp.wait_for_selector("#result:not(.hidden)")
        hp.wait_for_function("() => /^[0-9a-f]{8}$/.test(document.getElementById('fpVal').textContent)")
        ent, words, fp, addrs, zpub, xpub = expected(rolls, 12, "")
        hosted.update({
            "dice result marked": hp.is_visible("#hostedBannerOut") and hp.is_hidden("#testBannerOut") and "TESTSEED" in hp.inner_text("#fpNote"),
            "dice words unchanged": [w.split(".")[-1].strip() for w in hp.eval_on_selector_all("#words .word", "e => e.map(x => x.textContent)")] == words,
            "dice fingerprint unchanged": hp.inner_text("#fpVal") == fp,
        })
        hp.click("#btnSeedInToggle")
        hp.evaluate("""() => {
            const dt = new DataTransfer();
            dt.setData('text', 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about');
            document.querySelector('#seedBoxes input').dispatchEvent(new ClipboardEvent('paste', { clipboardData: dt, bubbles: true, cancelable: true }));
        }""")
        hp.click("#btnLoadSeed")
        hp.wait_for_function("() => document.getElementById('fpVal').textContent === '73c5da0a'")
        ent, words, fp, addrs, zpub, xpub = expected_mnemonic(bytes(16), "")
        hosted.update({
            "entered seed marked": hp.is_visible("#hostedBannerOut") and hp.is_visible("#inputBannerOut") and "TESTSEED" in hp.inner_text("#fpNote"),
            "entered seed addresses": hp.eval_on_selector_all(".addrrow span", "e => e.map(x => x.textContent)") == addrs and fp == "73c5da0a",
        })
        hp.click("#langNl")
        hosted.update({
            "Dutch banner and title": hp.inner_text("#bannerHosted").startswith("ONLINE PROBEERVERSIE") and hp.title().endswith("online probeerversie"),
            "Dutch result marking": hp.inner_text("#hostedBannerOut").startswith("TESTSEED (online probeerversie)"),
        })
        bad = [k for k, v in hosted.items() if not v]
        fails += len(bad)
        print("http://, online trial mode:", "OK" if not bad else "FAIL " + ", ".join(bad))
        requests += hreq
        srv.shutdown()
        browser.close()
    print("page errors:", errors or "none", "| network requests:", requests or "none")
    fails += len(errors) + len(requests)
    print("RESULT:", "PASS" if not fails else f"FAIL ({fails})")
    raise SystemExit(1 if fails else 0)


if __name__ == "__main__":
    main()
