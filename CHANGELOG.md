# Changelog

Versions before the first public release were developed privately; the SHA-256 of every earlier build is kept by the maintainer.

## v2.10

- The page now points to this repository for verification: step 1 of "Procedure for real money" refers to `SHA256SUMS` in the GitHub release and to rebuilding with `python3 build.py`, and the footer names `github.com/jurgen2005/dice-seed-bip39`. The URL is plain text, not a link, so the page still makes no network connections.

## v2.9 (first public release)

- Dutch / English interface (starts in the browser language, nothing stored).
- Per-face deviation table (σ) with detectability.
- Explanation of the test randomizer and the reliability of the browser RNG; test button fails closed without `crypto.getRandomValues`.
- Watch-only account key `m/84'/0'/0'` as descriptor, key origin, zpub or xpub, with QR (own QR encoder for versions 1 to 10, ECC M).
- Address checker (receive and change, up to 1000 each) and automatic hiding after inactivity.
- Last-word calculator (coin flips or full list), existing-seed entry with autocomplete.
- First 10 BIP-84 addresses with QR, verification mode for SeedSigner's 50/99 rolls.
- Compact SeedQR with zoom, SeedSigner grid layout, block-by-block mode and embedded official templates.
- Master fingerprint with BIP39 passphrase.
- Core: dice rolls -> SHA-256 -> BIP39, conservative minimum (log2 5 bits per roll), quality checks, self-test on load, CSP without network.
