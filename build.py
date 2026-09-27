#!/usr/bin/env python3
"""Reproducible build: src/ -> dist/dice-seed.html. Python 3 standard library only.

Anyone can run this and compare the printed SHA-256 with SHA256SUMS and the GitHub release.
"""
import base64
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"
WORDLIST_SHA256 = "2f5eed53a4727b4bf8880d8f3f199efc90e58503646d9ff8eff3a2ed3b24dbda"  # official BIP39 english.txt
TEMPLATE_SHA256 = {  # official SeedSigner grid_wfingerprint templates (docs/seed_qr/printable_templates)
    "21x21": "b1f4a2595cb899daeb406a2c5a76dc6b7654396c0064beda181733538252f0bb",
    "25x25": "8497036f8f454bc7cb212cf148069283a2a0b681d3a69277559b253cfbd4efe1",
}


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> None:
    wl = (SRC / "wordlist" / "english.txt").read_bytes()
    assert sha256(wl) == WORDLIST_SHA256, "wordlist differs from the official BIP39 english.txt"
    words = wl.decode("utf-8").split("\n")[:-1]
    assert len(words) == 2048

    pdf = {}
    for size, want in TEMPLATE_SHA256.items():
        data = (SRC / "templates" / f"grid_wfingerprint_{size}.pdf").read_bytes()
        assert sha256(data) == want, f"template {size} differs from the SeedSigner original"
        pdf[size] = base64.b64encode(data).decode("ascii")

    i18n = json.loads((SRC / "i18n_en.json").read_bytes().decode("utf-8"))
    t = (SRC / "template.html").read_bytes().decode("utf-8")
    t = (t.replace("__WORDLIST__", json.dumps(words, separators=(",", ":")))
          .replace("__PDF21__", pdf["21x21"])
          .replace("__PDF25__", pdf["25x25"])
          .replace("__I18N_EN__", json.dumps(i18n, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")))
    assert "__" not in t.replace("__proto__", ""), "unreplaced placeholder"

    out = ROOT / "dist" / "dice-seed.html"
    out.parent.mkdir(exist_ok=True)
    out.write_bytes(t.encode("utf-8"))
    print(sha256(out.read_bytes()), " dist/dice-seed.html")


if __name__ == "__main__":
    main()
