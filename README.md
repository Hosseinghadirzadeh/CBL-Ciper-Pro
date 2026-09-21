# CBL Ciper Pro

CBL Ciper Pro is a Windows desktop application for the experimental **LBC-GEO v1** reversible literary transformation. It combines multiple Project Gutenberg books, author metadata, and geographic metadata, then protects the resulting token stream with established authenticated encryption.

The application presents **LBC-GEO v1** as a custom encryption option and includes a dedicated visual page documenting its Multi-Book, Nationality, and Geographic transformation pipeline.

> LBC-GEO is not, by itself, modern cryptography. Confidentiality and authenticity come from AES-256-GCM. Password keys use Argon2id and purpose-specific subkeys use HKDF-SHA256.

## Architecture and exact pipeline

For each representable normalized character, Layer 1 deterministically selects 2–8 distinct eligible books using HMAC-SHA256 keyed by the literary subkey and the per-message nonce. It stores a valid character position from every selected book. All references must resolve to the same character during decryption.

Layer 2 hashes canonical descriptors containing Gutenberg ID, author, nationality, birth country, and birth city. The combined author material salts a per-symbol HKDF key; an HKDF-expanded mask is XORed with the complete serialized Layer-1 token.

Layer 3 independently hashes fixed-precision geographic descriptors containing country code, birth city, latitude, and longitude. Its per-symbol HKDF mask is XORed with Layer 2. The final token envelope retains the selected book IDs so the decoder can reconstruct both masks. That envelope is itself inside AES-GCM ciphertext.

```text
input -> multi-book references -> nationality mask -> geographic mask
      -> token HMAC -> AES-256-GCM -> .lbcx
```

Decryption verifies AES-GCM before returning any data, verifies the exact local corpus hashes, reverses geography, reverses nationality, verifies the token HMAC, and resolves all book references.

### Escape mode and binary data

Characters not present in enough books—including uppercase, punctuation, whitespace, Persian, Arabic, CJK, and emoji—are encoded as `ESCAPE_UTF8` byte tokens. Escape tokens still select the configured number of corpus books so both metadata layers apply. Text is reconstructed as exact UTF-8. Arbitrary files use the same byte-oriented form and are recovered exactly. Folder helpers first create a path-checked ZIP representation.

## Project Gutenberg and metadata

The default **Online Gutenberg Corpus** mode automatically downloads and indexes enough UTF-8 books when encryption first runs. Only public-domain corpus books travel over the internet: plaintext, files, passwords, and keys remain on the computer. Downloads are cached so later encryption/decryption can work offline. A Local Library Only option is also available. Gutenberg generally does not provide nationality, birthplace, or coordinates, so the automatic starter set uses explicitly curated supplemental metadata; other books remain `UNKNOWN` until supplied by the user.

Book originals remain unchanged. A deterministic NFC/case-folded alphanumeric corpus is indexed in SQLite using compact 64-bit position arrays. Every container carries an encrypted corpus manifest with Gutenberg IDs, SHA-256 hashes, and normalization version.

## LBCX v1 container

The binary format begins with `LBCX`, format version, header length, ciphertext length, canonical JSON header, and AES-GCM ciphertext/tag. The authenticated header records the cipher, Argon2id parameters, random salt, fresh AES nonce, fresh message nonce, and LBC-GEO version. The corpus manifest and original filename are encrypted. Unsupported versions and malformed lengths are rejected.

## Security and threat model

CBL Ciper Pro protects against theft or modification of `.lbcx` files, provides offline-password-guessing resistance through Argon2id, detects corpus mismatch, and detects accidental corruption. Independent HKDF labels prevent direct key reuse.

It does **not** protect against a compromised OS, malware, keyloggers, screen capture, weak passwords, plaintext copies elsewhere, password loss, or signing-key loss. There is no password-recovery backdoor. Lost passwords may make data permanently unrecoverable. The application does not claim guaranteed secure deletion; SSD wear-leveling prevents software from reliably guaranteeing physical erasure.

Private Ed25519 keys are exported only in password-encrypted AES-GCM envelopes. Passwords, plaintext, root keys, derived keys, and private-key bytes are never logged.

## Installation and development

Use 64-bit Python 3.12 or newer on Windows 10/11:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pip install -r requirements-build.txt
python -m pytest
python main.py
build\build_exe.bat
```

The default app data directory is `%LOCALAPPDATA%\CBL Ciper Pro\`. Launch with `CBL_Ciper_Pro.exe --portable` to store data in `portable_data` beside the executable. Writable data is never placed in Program Files.

The reliable PyInstaller output is:

```text
dist\CBL_Ciper_Pro\CBL_Ciper_Pro.exe
```

Install Inno Setup 6 and run `build\build_installer.bat` to create `installer\output\CBL_Ciper_Pro_Setup.exe`.

## Offline use and backup

After download and indexing, no network connection is needed. Back up the entire app-data directory with the corpus and SQLite database: decryption requires the exact book editions and metadata used for encryption. Also back up encrypted private-key files and public keys separately.

## Limitations

- LBC token expansion is intentionally large; large files are slower and use substantial memory in v1.
- Word indexes are available to developers, while the shipped encryption path uses character mode plus automatic byte escape.
- Gutenberg search requires internet access; author nationality and birthplace need curated or user-supplied metadata.
- AES-256-GCM is the production container cipher. ChaCha20-Poly1305 is implemented as an optional engine but not exposed as the default container format.
