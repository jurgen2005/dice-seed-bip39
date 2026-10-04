# Security

## Reporting a problem

If you find a bug that could produce a wrong or weak seed, a wrong address or key, or that leaks data, please report it privately through **GitHub > Security > Report a vulnerability** on this repository instead of opening a public issue.

## Threat model in short

The page protects against: a silently weak random generator (there is none for real seeds), accidental network access (CSP), typos in rolls (invalid characters block), obvious typed patterns and gross die bias (statistical checks, conservative minimum), and a corrupted file (self-test, published SHA-256, reproducible build).

It does **not** protect against: a compromised computer or browser, screen recording, someone watching, a modified copy of the page that you did not verify, or mistakes when writing the words down.

The online trial version on GitHub Pages is outside this model for real seeds: you cannot verify the file you were served, and it runs in your everyday browser, where extensions with access to all websites can read the page. The page marks every result there as TESTSEED and warns against typing a real seed, but a modified copy would not. Use it only to try the tool. If the online version ever shows no "ONLINE TRIAL VERSION" banner, please report that as above.

The cryptographic code is unaudited. Cross-check every seed in an independent tool.
