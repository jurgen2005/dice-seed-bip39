# Changelog

Versions before the first public release were developed privately; the SHA-256 of every earlier build is kept by the maintainer.

## v2.12

- Online trial version. The page now detects whether it was opened as a local file (`file://`) or from a web address, such as GitHub Pages at `https://jurgen2005.github.io/dice-seed-bip39/dist/dice-seed.html`. From a web address it switches to trial mode: a red "ONLINE TRIAL VERSION" banner at the top (it replaces the "This computer is online" banner, because going offline does not make a hosted copy trustworthy), "online trial version" in the tab title, every result marked TESTSEED (dice, cards and an entered existing seed), and a fixed warning at "Enter existing seed" never to type a real seed there. It fails closed: anything that is not `file://` counts as online. The calculations are unchanged.
- `tests/test_crosscheck.py` now also serves the page over `http://` and checks the trial mode (banner, marking, warning, unchanged words, fingerprint and addresses, Dutch and English), and checks that none of it appears when the page is opened as a local file.
- README: section on the online trial version and its consequences. The release links are now absolute, so they also work on the GitHub Pages site.

## v2.11

- Playing cards as an alternative entropy source, behind the button "Use playing cards" in step 2. Method: full shuffled deck(s), no replacement. 12 words need one full round of 52 cards (log2(52!) = 225.6 bit), 24 words two rounds with a thorough reshuffle in between (451 bit).
- Visual input: a 4 x 13 grid (suits in rows, ranks in columns; transposed on narrow screens). Entered cards grey out with their position in the round, the last card is outlined, the grid locks when enough rounds are complete. Keyboard: rank (`A 2-9 T J Q K`) then suit (`S H C D`), Backspace removes the last card. Text input accepts `10` and the suit symbols.
- Calculation: SHA-256 over the canonical ASCII notation, cards separated by one space (`AS TH 9D ...`), then the same BIP39 path as the dice. Recomputable with `shasum` plus Ian Coleman (Hex, Use Raw Entropy); Ian Coleman's own card mode uses a different notation and gives different words.
- Checks: every card exactly once per round, only complete rounds; warnings for remnants of a sorted deck (same-suit neighbouring ranks) and for pairs kept from the previous round, thresholds from 400,000 simulated shuffles. A strong warning must be confirmed.
- "Test cards (random)": Fisher-Yates on `crypto.getRandomValues` with rejection sampling, marked TESTSEED.
- Self-test extended with card vectors (independently computed with Python `mnemonic` and embit). `tests/test_crosscheck.py` now also covers cards (grid clicks, keyboard, pasted text, 12 and 24 words, input checks).
- Fix: the TESTSEED marking now belongs to the calculated result. Before, loading an existing seed cleared the test flag of test rolls that were still in the dice field.

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
