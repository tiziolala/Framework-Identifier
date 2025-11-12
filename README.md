# Web Framework Passive Detector

A non-intrusive Python tool that analyzes websites to detect which web framework or CMS they may be using — such as WordPress, Django, Laravel, or others — by inspecting public clues and HTTP behavior.

# Features

- Passive detection only — no brute force, no active intrusion.

- Framework-agnostic design — extensible to multiple technologies (WordPress, Django, Laravel, etc.).

- Path and header analysis:

- Tests common framework-specific URLs (e.g., /wp-content/, /admin/, /vendor/).

- HTML content inspection:

- Scoring system estimating how likely a website uses a given framework.



# Requirements

``` python
pip install -r requirements.txt
```

# How to use 
For now you have to run the specific python script for the framework you want to identify.
```bash
python3 wordpress_identifier.py
```