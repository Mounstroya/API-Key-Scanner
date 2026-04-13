# 🔍 API Key Scanner — Multi-Provider

Scan GitHub for leaked API keys from **OpenAI**, **Anthropic (Claude)**, and **Google Gemini**.

> ⚠️ **DISCLAIMER**: This project is intended **for security research only**. Use it to check if your own keys have been exposed. Do not use it illegally. The authors are not responsible for any misuse.

---

## ✨ Features

- 🤖 **OpenAI** — detects `sk-proj-` and `sk-svcacct-` key formats
- 🧠 **Anthropic (Claude)** — detects `sk-ant-` key format
- 💎 **Google Gemini** — detects `AIza...` key format
- 🎛️ **Interactive provider selection** — choose which providers to scan at runtime
- 💻 **CLI support** — pass providers directly as arguments
- 🍪 **Cookie persistence** — log in to GitHub once, reuse session automatically
- 🗃️ **SQLite database** — results stored locally in `github.db`

---

## 📋 Prerequisites

- Debian / Ubuntu / macOS / WSL2
- Python 3.10+
- Google Chrome or Chromium

---

## 🚀 Installation

```bash
# 1. Clone the repo
git clone https://github.com/Mounstroya/API-Key-Scanner
cd API-Key-Scanner

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install setuptools
pip install -r requirements.txt
```

---

## 🖥️ Usage

### Interactive mode (recommended)

```bash
python3 src/main.py
```

You will see a menu to choose which providers to scan:

```
╭─────────────────────────────────────────╮
│  API Key Scanner — Multi-Provider       │
│  Scan GitHub for leaked API keys        │
╰─────────────────────────────────────────╯

Which providers do you want to scan for?
  [1] 🤖  OpenAI
  [2] 🧠  Anthropic (Claude)
  [3] 💎  Google Gemini
  [A] 🔍  All providers

Enter your choice:
```

After selecting, a browser will open and ask you to log in to GitHub. Once logged in, the scan starts automatically.

### CLI mode

```bash
# Scan only OpenAI keys
python3 src/main.py -p openai

# Scan Anthropic and Gemini
python3 src/main.py -p anthropic gemini

# Scan all providers
python3 src/main.py -p openai anthropic gemini

# Only re-check keys already in the database
python3 src/main.py --check-existed-keys-only
```

### All arguments

| Argument | Description | Default |
|---|---|---|
| `-p`, `--providers` | Providers to scan: `openai` `anthropic` `gemini` | Interactive |
| `--from-iter` | Resume scan from a specific iteration | `None` |
| `-ceko` | Only re-check keys already in the database | `False` |
| `-ciq` | Re-check keys with insufficient quota | `False` |
| `-k`, `--keywords` | Custom search keywords | Default list |
| `-l`, `--languages` | Custom programming languages to search | Default list |
| `--debug` | Enable debug logging | `False` |

---

## 📊 Results

Results are stored in `github.db` (SQLite). You can browse it with any SQLite viewer such as [DB Browser for SQLite](https://sqlitebrowser.org/).

Each record contains:
- `apiKey` — the key found
- `status` — `yes` (valid), `invalid_api_key`, `rate_limit`, etc.
- `lastChecked` — date of last validation

---

## 🔒 Keeping Your Keys Safe

If you find your own key exposed, revoke it immediately:
- [OpenAI — Revoke API keys](https://platform.openai.com/api-keys)
- [Anthropic — Manage API keys](https://console.anthropic.com/settings/keys)
- [Google — Manage API keys](https://console.cloud.google.com/apis/credentials)

Useful resources:
- [Best Practices for API Key Safety (OpenAI)](https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety)
- [My API Key Leaked — What Should I Do? (GitGuardian)](https://www.gitguardian.com/remediation/openai-key)

---

## 🙏 Credits

Based on [ChatGPT-API-Scanner](https://github.com/Junyi-99/ChatGPT-API-Scanner) by [@Junyi-99](https://github.com/Junyi-99), licensed under [MIT](https://github.com/Junyi-99/ChatGPT-API-Scanner/blob/main/LICENSE).

This fork adds multi-provider support (Anthropic, Gemini) and an interactive provider selection menu.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
