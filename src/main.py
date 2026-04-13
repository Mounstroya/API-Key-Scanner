"""
API Key Scanner - Multi-Provider
Scan GitHub for leaked API keys from OpenAI, Anthropic (Claude), and Google Gemini.

Based on: https://github.com/Junyi-99/ChatGPT-API-Scanner (MIT License)
"""

import argparse
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor

import rich
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

from configs import KEYWORDS, LANGUAGES, PATHS, PROVIDERS
from manager import CookieManager, DatabaseManager, ProgressManager
from utils import check_key

FORMAT = "%(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt="[%X]")
log = logging.getLogger("API-Key-Scanner")
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)

console = Console()


# ─────────────────────────────────────────────
#  Interactive provider selection
# ─────────────────────────────────────────────
def select_providers() -> list[str]:
    """
    Show an interactive menu and return the list of selected provider keys.
    """
    console.print(Panel.fit(
        "[bold cyan]API Key Scanner[/bold cyan] — Multi-Provider\n"
        "[dim]Scan GitHub for leaked API keys[/dim]",
        border_style="cyan",
    ))

    provider_list = list(PROVIDERS.items())

    console.print("\n[bold]Which providers do you want to scan for?[/bold]\n")
    for i, (key, info) in enumerate(provider_list, start=1):
        console.print(f"  [bold cyan][{i}][/bold cyan] {info['emoji']}  {info['name']}")
    console.print(f"  [bold cyan][A][/bold cyan] 🔍  All providers\n")

    while True:
        raw = Prompt.ask("Enter your choice", default="A").strip().upper()

        if raw == "A":
            selected = list(PROVIDERS.keys())
            break

        choices = raw.replace(",", " ").split()
        selected = []
        valid = True
        for ch in choices:
            if ch.isdigit() and 1 <= int(ch) <= len(provider_list):
                selected.append(provider_list[int(ch) - 1][0])
            else:
                console.print(f"[red]Invalid choice: '{ch}'. Try again.[/red]")
                valid = False
                break
        if valid and selected:
            break

    console.print("\n[bold green]Selected providers:[/bold green]")
    for p in selected:
        info = PROVIDERS[p]
        console.print(f"  {info['emoji']} {info['name']}")
    console.print()

    return selected


# ─────────────────────────────────────────────
#  Main scanner class
# ─────────────────────────────────────────────
class APIKeyScanner:
    """
    Scan GitHub for leaked API keys across multiple providers.
    """

    def __init__(self, db_file: str, keywords: list, languages: list, providers: list[str]):
        self.db_file = db_file
        self.driver: webdriver.Chrome | None = None
        self.cookies: CookieManager | None = None
        self.providers = providers

        rich.print(f"📂 Opening database file {self.db_file}")
        self.dbmgr = DatabaseManager(self.db_file)

        self.keywords = keywords
        self.languages = languages
        self.candidate_urls = self._build_candidate_urls()

    def _build_candidate_urls(self) -> list[str]:
        """Build search URLs for all selected providers."""
        urls = []
        for provider_key in self.providers:
            provider = PROVIDERS[provider_key]
            for regex, too_many_results, _ in provider["regex_list"]:
                for path in PATHS:
                    urls.append(
                        f"https://github.com/search?q=(/{regex.pattern}/)+AND+({path})&type=code&ref=advsearch"
                    )
                for language in self.languages:
                    if too_many_results:
                        urls.append(
                            f"https://github.com/search?q=(/{regex.pattern}/)+language:{language}&type=code&ref=advsearch"
                        )
                    else:
                        urls.append(
                            f"https://github.com/search?q=(/{regex.pattern}/)&type=code&ref=advsearch"
                        )
        return urls

    def _all_regex(self):
        """Return all compiled regex objects for selected providers."""
        result = []
        for provider_key in self.providers:
            result.extend(PROVIDERS[provider_key]["regex_list"])
        return result

    def login_to_github(self):
        """Open Chrome and log in to GitHub."""
        rich.print("🌍 Opening Chrome ...")

        options = webdriver.ChromeOptions()
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")

        self.driver = uc.Chrome(options=options)
        self.driver.implicitly_wait(3)

        self.cookies = CookieManager(self.driver)
        cookie_exists = os.path.exists("cookies.pkl")
        self.driver.get("https://github.com/login")

        if not cookie_exists:
            rich.print("🤗 No cookies found, please login to GitHub first")
            input("Press Enter after you logged in: ")
            self.cookies.save()
        else:
            rich.print("🍪 Cookies found, loading cookies")
            self.cookies.load()

        self.cookies.verify_user_login()

    def _expand_all_code(self):
        elements = self.driver.find_elements(by=By.XPATH, value="//*[contains(text(), 'more match')]")
        for element in elements:
            element.click()

    def _find_urls_and_apis(self) -> tuple[list[str], list[str]]:
        apis_found = []
        urls_need_expand = []
        all_regex = self._all_regex()

        codes = self.driver.find_elements(by=By.CLASS_NAME, value="code-list")
        for element in codes:
            apis = []
            for regex, _, too_long in all_regex[2:]:
                if not too_long:
                    apis.extend(regex.findall(element.text))

            if len(apis) == 0:
                a_tag = element.find_element(by=By.XPATH, value=".//a")
                urls_need_expand.append(a_tag.get_attribute("href"))
            apis_found.extend(apis)

        return apis_found, urls_need_expand

    def _process_url(self, url: str):
        if self.driver is None:
            raise ValueError("Driver is not initialized")

        self.driver.get(url)

        while True:
            if self.driver.find_elements(by=By.XPATH, value="//*[contains(text(), 'You have exceeded a secondary rate limit')]"):
                for _ in tqdm(range(30), desc="⏳ Rate limit reached, waiting ..."):
                    time.sleep(1)
                self.driver.refresh()
                continue

            self._expand_all_code()
            apis_found, urls_need_expand = self._find_urls_and_apis()
            rich.print(f"    🌕 There are {len(urls_need_expand)} urls waiting to be expanded")

            try:
                WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//a[@aria-label='Next Page']")))
                next_buttons = self.driver.find_elements(by=By.XPATH, value="//a[@aria-label='Next Page']")
                next_buttons[0].click()
            except Exception:
                rich.print("⚪️ No more pages")
                break

        all_regex = self._all_regex()
        for u in tqdm(urls_need_expand, desc="🔍 Expanding URLs ..."):
            if self.driver is None:
                raise ValueError("Driver is not initialized")

            with self.dbmgr as mgr:
                if mgr.get_url(u):
                    rich.print(f"    🔑 skipping url '{u[:10]}...{u[-10:]}'")
                    continue

            self.driver.get(u)
            time.sleep(3)

            retry = 0
            while retry <= 3:
                matches = []
                for regex, _, _ in all_regex:
                    matches.extend(regex.findall(self.driver.page_source))
                matches = list(set(matches))

                if len(matches) == 0:
                    rich.print(f"    ⚪️ No matches found, retrying [{retry}/3]...")
                    retry += 1
                    time.sleep(3)
                    continue

                with self.dbmgr as mgr:
                    new_apis = [api for api in matches if not mgr.key_exists(api)]
                    new_apis = list(set(new_apis))
                apis_found.extend(new_apis)
                rich.print(f"    🔬 Found {len(matches)} matches in the expanded page")
                for match in matches:
                    rich.print(f"        '{match[:10]}...{match[-10:]}'")

                with self.dbmgr as mgr:
                    mgr.insert_url(url)
                break

        self.check_api_keys_and_save(apis_found)

    def check_api_keys_and_save(self, keys: list[str]):
        with self.dbmgr as mgr:
            unique_keys = list(set(keys))
            unique_keys = [api for api in unique_keys if not mgr.key_exists(api)]

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(check_key, unique_keys))
            with self.dbmgr as mgr:
                for idx, result in enumerate(results):
                    mgr.insert(unique_keys[idx], result)

    def search(self, from_iter: int | None = None):
        progress = ProgressManager()
        total = len(self.candidate_urls)
        pbar = tqdm(enumerate(self.candidate_urls), total=total, desc="🔍 Searching ...")

        if from_iter is None:
            from_iter = progress.load(total=total)

        for idx, url in enumerate(self.candidate_urls):
            if idx < from_iter:
                pbar.update()
                time.sleep(0.05)
                log.debug("⚪️ Skip %s", url)
                continue
            self._process_url(url)
            progress.save(idx, total)
            pbar.update()
        pbar.close()

    def deduplication(self):
        with self.dbmgr as mgr:
            mgr.deduplicate()

    def update_existed_keys(self):
        with self.dbmgr as mgr:
            rich.print("🔄 Updating existed keys")
            keys = mgr.all_keys()
            for key in tqdm(keys, desc="🔄 Updating existed keys ..."):
                result = check_key(key[0])
                mgr.delete(key[0])
                mgr.insert(key[0], result)

    def update_iq_keys(self):
        with self.dbmgr as mgr:
            rich.print("🔄 Updating insufficient quota keys")
            keys = mgr.all_iq_keys()
            for key in tqdm(keys, desc="🔄 Updating ..."):
                result = check_key(key[0])
                mgr.delete(key[0])
                mgr.insert(key[0], result)

    def all_available_keys(self) -> list:
        with self.dbmgr as mgr:
            return mgr.all_keys()

    def __del__(self):
        if hasattr(self, "driver") and self.driver is not None:
            self.driver.quit()


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────
def main(
    from_iter: int | None = None,
    check_existed_keys_only: bool = False,
    keywords: list | None = None,
    languages: list | None = None,
    check_insufficient_quota: bool = False,
    providers: list[str] | None = None,
):
    keywords = KEYWORDS.copy() if keywords is None else keywords
    languages = LANGUAGES.copy() if languages is None else languages

    # If providers not passed via CLI, ask interactively
    if providers is None:
        providers = select_providers()

    scanner = APIKeyScanner("github.db", keywords, languages, providers)

    if not check_existed_keys_only:
        scanner.login_to_github()
        scanner.search(from_iter=from_iter)

    if check_insufficient_quota:
        scanner.update_iq_keys()

    scanner.update_existed_keys()
    scanner.deduplication()
    keys = scanner.all_available_keys()

    rich.print(f"\n🔑 [bold green]Available keys ({len(keys)}):[/bold green]")
    for key in keys:
        rich.print(f"[bold green]{key[0]}[/bold green]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scan GitHub for leaked API keys (multi-provider)")
    parser.add_argument("--from-iter", type=int, default=None, help="Start from the specific iteration")
    parser.add_argument("--debug", action="store_true", default=False)
    parser.add_argument("-ceko", "--check-existed-keys-only", action="store_true", default=False)
    parser.add_argument("-ciq", "--check-insufficient-quota", action="store_true", default=False)
    parser.add_argument("-k", "--keywords", nargs="+", default=None)
    parser.add_argument("-l", "--languages", nargs="+", default=None)
    parser.add_argument(
        "-p", "--providers",
        nargs="+",
        choices=list(PROVIDERS.keys()),
        default=None,
        help="Providers to scan: openai anthropic gemini (default: interactive selection)",
    )
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    main(
        from_iter=args.from_iter,
        check_existed_keys_only=args.check_existed_keys_only,
        keywords=args.keywords,
        languages=args.languages,
        check_insufficient_quota=args.check_insufficient_quota,
        providers=args.providers,
    )
