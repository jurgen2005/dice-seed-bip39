# Dobbelsteen-seed (BIP39)

Eén losse HTML-pagina die **echte dobbelsteenworpen** omzet in een BIP39-seed (12 of 24 woorden), volledig offline. De uitkomst kun je **controleren** in plaats van alleen vertrouwen.

[English version](README.md)

> **Status: niet geaudit.** De cryptografie in deze pagina (SHA-256, SHA-512, PBKDF2, RIPEMD-160, secp256k1, BIP32, QR-codering) is in gewone JavaScript geschreven. Ze is getest tegen officiële testvectoren en onafhankelijke bibliotheken, maar **niet** beoordeeld door een onafhankelijke security-auditor. Controleer de uitkomst altijd in een tweede, onafhankelijke tool voordat je echte waarde op een seed zet. Geen garantie, zie [LICENSE](LICENSE).

## Waarom

Een seed uit de interne random-generator van een apparaat kun je van buitenaf niet controleren. Het Coldcard-incident van 2026 liet zien dat dit jarenlang mis kan gaan zonder dat iemand het merkt. Met dobbelstenen ben **jij** de bron van de willekeur. De omzetting van worpen naar woorden ligt vast, dus iedereen kan haar narekenen.

Deze pagina:

- gebruikt **geen random-generator voor echte seeds**. De woorden zijn `SHA-256(jouw worpen)`, verder niets;
- volgt dezelfde conventie als [de BIP39-tool van Ian Coleman](https://github.com/iancoleman/bip39) (Entropy type **Base 10**) en de dobbelsteenmodus van SeedSigner. Daardoor kun je de uitkomst in een onafhankelijke tool narekenen;
- weigert te weinig worpen, met een voorzichtig minimum dat ook klopt bij een merkbaar scheve dobbelsteen.

## Functies

- **Seed uit worpen:** 12 of 24 woorden. Minimaal 56 / 111 worpen (harde grens), aanbevolen 100 / 199. Meer worpen tellen altijd mee.
- **Controlemodus:** voor SeedSigners 50 / 99 worpen. Duidelijk gemarkeerd en alleen bedoeld om na te rekenen.
- **Kwaliteitscontrole van de worpen:** chi² over de zes kanten, afwijking per kant in σ met meetbaarheid, lange reeksen en getypte patronen.
- **Fingerprint:** master fingerprint (BIP32), met optionele BIP39-passphrase (NFKD, met een waarschuwing bij niet-ASCII-tekens).
- **Compact SeedQR** (SeedSigner-standaard):
  - vergroting met raster;
  - modus blok voor blok om over te tekenen;
  - de officiële printbare SeedSigner-sjablonen zitten in de pagina.
- **Adressen:**
  - de eerste 10 BIP-84-ontvangstadressen, elk met een QR;
  - een adrescontrole over ontvangst- en wisseladressen, tot 1000 per keten.
- **Watch-only account-sleutel** `m/84'/0'/0'`: als descriptor, `[fingerprint/pad]zpub`, zpub of xpub, als tekst en als QR.
- **Bestaande seed:** invoeren in 12 of 24 vakjes met automatisch aanvullen, en een geldig laatste woord berekenen uit muntworpen.
- **Automatisch verbergen:** woorden en QR worden na een tijd zonder activiteit verborgen.
- **Twee talen:** Nederlands en Engels. De pagina start in de taal van de browser en slaat de keuze niet op.
- **Zelftest bij elke keer laden:**
  - NIST SHA-256;
  - officiële BIP39-, BIP32-, BIP84- en BIP-380-vectoren;
  - QR-matrices.

  Mislukt de zelftest, dan is berekenen geblokkeerd.
- **Geen netwerk, geen opslag:** een Content Security Policy blokkeert alle netwerkverkeer. Er is geen opslag, er zijn geen cookies en er worden geen externe bestanden geladen.

## Controleren voor gebruik

1. Download `dice-seed.html` uit de [nieuwste release](../../releases/latest).
2. Vergelijk de SHA-256 met `SHA256SUMS` in de release en in deze repository:
   - macOS: `shasum -a 256 dice-seed.html`
   - Linux: `sha256sum dice-seed.html`
   - Windows (PowerShell): `Get-FileHash dice-seed.html`
3. Optioneel, en sterker: bouw het bestand zelf opnieuw en vergelijk (zie *Reproduceerbare build*).
4. Open de pagina en controleer dat de zelftest-badge groen is.

## Veilig gebruik (kort)

1. Gebruik een offline computer, bij voorkeur opgestart van een live-USB (bijvoorbeeld Tails), zonder netwerk.
2. Gebruik een goede dobbelsteen (een casinodobbelsteen is ideaal). Gooi echt: schudden en laten rollen, niet neerleggen en geen worp overdoen. Schrijf de worpen eerst op papier.
3. Voer de worpen in, laat de seed berekenen en **reken dezelfde worpen na in een tweede tool** (Ian Coleman, Entropy, Base 10). Dezelfde woorden betekenen dat geen van beide tools je invoer heeft gemanipuleerd.
4. Schrijf de woorden op papier of metaal. Geen foto, geen screenshot, niet kopiëren en plakken.
5. Klik "Alles wissen", sluit de browser en zet de computer uit.

De pagina legt dit uitgebreider uit onder *Controleren en veilig gebruiken*.

## Reproduceerbare build

`dist/dice-seed.html` wordt uit `src/` gemaakt door `build.py`. Daarvoor is alleen Python 3 nodig, zonder extra pakketten.

```sh
python3 build.py
# toont de SHA-256 van dist/dice-seed.html; die moet gelijk zijn aan SHA256SUMS
```

De build controleert ook twee dingen: dat de woordenlijst de officiële BIP39-`english.txt` is, en dat de sjablonen byte voor byte gelijk zijn aan de originelen van SeedSigner.

| Pad | Inhoud |
|---|---|
| `src/template.html` | De bron van de pagina (HTML, CSS, JavaScript) met placeholders |
| `src/wordlist/english.txt` | Officiële Engelse BIP39-woordenlijst |
| `src/templates/*.pdf` | Officiële SeedSigner-sjablonen `grid_wfingerprint` |
| `src/i18n_en.json` | Engelse vertaling van de vaste Nederlandse tekst |
| `build.py` | Vult de placeholders in en schrijft `dist/dice-seed.html` |
| `tests/test_crosscheck.py` | Kruiscontrole tegen embit en zxing-cpp in headless Chromium |

## Tests

```sh
pip install playwright embit zxing-cpp opencv-python-headless numpy
playwright install chromium
python3 tests/test_crosscheck.py
```

Tijdens de ontwikkeling is de pagina ook vergeleken met:

- de tool van Ian Coleman (Base 10);
- de Python-bibliotheken `mnemonic` en `qrcode`;
- hardware: een Blockstream Jade scande de Compact SeedQR en toonde dezelfde adressen.

Getest in Chromium. Firefox en Safari zijn niet systematisch getest.

## Beperkingen

- Geen bescherming tegen een gecompromitteerde computer, schermopname of iemand die meekijkt. Gebruik een offline live-USB.
- De statistische controles vangen tikpatronen en grove scheefheid, geen subtiele. Daarvoor is het voorzichtige minimum.
- De knop "Testworpen (random)" gebruikt de random-generator van de browser. Hij is er alleen om de tool uit te proberen, en de uitkomst krijgt het label TESTSEED. Nooit gebruiken voor echte waarde.
- Niet geaudit, zie boven.

## Hoe dit gemaakt is

De code is geschreven met een AI-assistent (Claude, van Anthropic). De beheerder heeft de richting bepaald, alles gecontroleerd en het op hardware getest. Elke cryptografische functie is gedekt door testvectoren en kruiscontroles. Beoordeel de code toch op haar eigen merites en controleer de uitkomst; daar is deze tool juist voor gemaakt.

## Bronnen en licenties

- **Code:** MIT, zie [LICENSE](LICENSE).
- **Engelse BIP39-woordenlijst:** uit [BIP-39](https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki).
- **Printbare SeedSigner-sjablonen:** © SeedSigner, MIT-licentie, uit de [SeedSigner-repository](https://github.com/SeedSigner/seedsigner#seedqr-printable-templates).
- **Compact SeedQR-formaat:** specificatie van SeedSigner.

Zie [NOTICE.md](NOTICE.md).
