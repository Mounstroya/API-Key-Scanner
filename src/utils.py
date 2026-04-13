"""
This module provides functions to check the validity of API keys
from multiple providers: OpenAI, Anthropic (Claude), and Google Gemini.

The check_key() function auto-detects the provider based on the key prefix.
"""

import rich
from openai import APIStatusError, AuthenticationError, OpenAI, RateLimitError


# ─────────────────────────────────────────────
#  OpenAI
# ─────────────────────────────────────────────
def check_key_openai(key: str) -> str:
    """Check if an OpenAI API key is valid."""
    try:
        client = OpenAI(api_key=key)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a yeser, you only output lowercase yes."},
                {"role": "user", "content": "yes or no? say yes"},
            ],
        )
        result = completion.choices[0].message.content
        rich.print(f"🔑 [bold green]OpenAI key available[/bold green]: [orange_red1]'{key}'[/orange_red1] ({result})\n")
        return "yes"
    except AuthenticationError as e:
        rich.print(f"[deep_sky_blue1]{e.body['code']} ({e.status_code})[/deep_sky_blue1]: '{key[:10]}...{key[-10:]}'")
        return e.body["code"]
    except RateLimitError as e:
        rich.print(f"[deep_sky_blue1]{e.body['code']} ({e.status_code})[/deep_sky_blue1]: '{key[:10]}...{key[-10:]}'")
        return e.body["code"]
    except APIStatusError as e:
        rich.print(f"[bold red]{e.body['code']} ({e.status_code})[/bold red]: '{key[:10]}...{key[-10:]}'")
        return e.body["code"]
    except Exception as e:
        rich.print(f"[bold red]{e}[/bold red]: '{key[:10]}...{key[-10:]}'")
        return "Unknown Error"


# ─────────────────────────────────────────────
#  Anthropic
# ─────────────────────────────────────────────
def check_key_anthropic(key: str) -> str:
    """Check if an Anthropic API key is valid."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=10,
            messages=[{"role": "user", "content": "say yes"}],
        )
        result = message.content[0].text
        rich.print(f"🧠 [bold green]Anthropic key available[/bold green]: [orange_red1]'{key}'[/orange_red1] ({result})\n")
        return "yes"
    except Exception as e:
        err = str(e)
        if "authentication_error" in err or "invalid x-api-key" in err.lower():
            rich.print(f"[deep_sky_blue1]invalid_api_key[/deep_sky_blue1]: '{key[:10]}...{key[-10:]}'")
            return "invalid_api_key"
        if "rate_limit" in err.lower():
            rich.print(f"[deep_sky_blue1]rate_limit[/deep_sky_blue1]: '{key[:10]}...{key[-10:]}'")
            return "rate_limit"
        rich.print(f"[bold red]{e}[/bold red]: '{key[:10]}...{key[-10:]}'")
        return "Unknown Error"


# ─────────────────────────────────────────────
#  Google Gemini
# ─────────────────────────────────────────────
def check_key_gemini(key: str) -> str:
    """Check if a Google Gemini API key is valid."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("say yes")
        result = response.text.strip()
        rich.print(f"💎 [bold green]Gemini key available[/bold green]: [orange_red1]'{key}'[/orange_red1] ({result})\n")
        return "yes"
    except Exception as e:
        err = str(e).lower()
        if "api_key_invalid" in err or "api key not valid" in err:
            rich.print(f"[deep_sky_blue1]invalid_api_key[/deep_sky_blue1]: '{key[:10]}...{key[-10:]}'")
            return "invalid_api_key"
        if "quota" in err or "rate" in err:
            rich.print(f"[deep_sky_blue1]rate_limit[/deep_sky_blue1]: '{key[:10]}...{key[-10:]}'")
            return "rate_limit"
        rich.print(f"[bold red]{e}[/bold red]: '{key[:10]}...{key[-10:]}'")
        return "Unknown Error"


# ─────────────────────────────────────────────
#  Auto-detect provider and check key
# ─────────────────────────────────────────────
def check_key(key: str) -> str:
    """
    Auto-detect the provider from the key prefix and validate it.
    """
    if key.startswith("sk-ant-"):
        return check_key_anthropic(key)
    elif key.startswith("AIza"):
        return check_key_gemini(key)
    else:
        return check_key_openai(key)


if __name__ == "__main__":
    check_key("sk-proj-12345")
