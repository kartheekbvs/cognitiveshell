# cognitiveshell/commands/browser_control.py
!pip install playwright
!playwright install
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
import time
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BrowserControl:
    """
    Manages browser automation using Playwright.
    Handles opening URLs, performing searches, and basic tab management.
    """

    def __init__(self, browser_type: str = "chromium"):
        """
        Initializes the BrowserControl.

        Args:
            browser_type (str): The type of browser to launch ('chromium', 'firefox', 'webkit').
                                Defaults to 'chromium'.
        """
        self.playwright = None
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page: Page = None
        self.browser_type = browser_type
        self._initialize_browser()

    def _initialize_browser(self):
        """
        Launches the browser and creates a new context and page.
        This method is called automatically during initialization.
        """
        try:
            self.playwright = sync_playwright().start()
            if self.browser_type == "chromium":
                self.browser = self.playwright.chromium.launch(headless=False) # headless=False to see the browser
            elif self.browser_type == "firefox":
                self.browser = self.playwright.firefox.launch(headless=False)
            elif self.browser_type == "webkit":
                self.browser = self.playwright.webkit.launch(headless=False)
            else:
                raise ValueError(f"Unsupported browser type: {self.browser_type}")

            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            logger.info(f"Browser ({self.browser_type}) launched successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            self._cleanup() # Attempt to clean up on failure
            raise

    def open_url(self, url: str):
        """
        Opens a given URL in the current browser page.
        If no page exists, a new one is created.

        Args:
            url (str): The URL to navigate to.
        """
        if not self.page:
            logger.warning("No active page found. Creating a new one.")
            self.page = self.context.new_page()
        try:
            # Ensure URL has a scheme (http/https) for Playwright
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            self.page.goto(url)
            logger.info(f"Navigated to URL: {url}")
        except Exception as e:
            logger.error(f"Failed to open URL '{url}': {e}")

    def search(self, query: str, search_engine: str = "google"):
        """
        Performs a search on a specified search engine.

        Args:
            query (str): The search query.
            search_engine (str): The search engine to use (e.g., 'google', 'duckduckgo').
                                 Defaults to 'google'.
        """
        if not self.page:
            logger.warning("No active page found. Creating a new one.")
            self.page = self.context.new_page()

        try:
            if search_engine.lower() == "google":
                search_url = f"https://www.google.com/search?q={query}"
            elif search_engine.lower() == "duckduckgo":
                search_url = f"https://duckduckgo.com/?q={query}"
            elif search_engine.lower() == "bing":
                search_url = f"https://www.bing.com/search?q={query}"
            else:
                logger.warning(f"Unsupported search engine: {search_engine}. Defaulting to Google.")
                search_url = f"https://www.google.com/search?q={query}"

            self.page.goto(search_url)
            logger.info(f"Performed search for '{query}' on {search_engine}.")
        except Exception as e:
            logger.error(f"Failed to perform search for '{query}': {e}")

    def new_tab(self, url: str = "about:blank"):
        """
        Opens a new tab and navigates to the specified URL.

        Args:
            url (str): The URL to open in the new tab. Defaults to a blank page.
        """
        try:
            self.page = self.context.new_page()
            self.open_url(url) # Reuse open_url to handle URL formatting
            logger.info(f"Opened new tab with URL: {url}")
        except Exception as e:
            logger.error(f"Failed to open new tab: {e}")

    def close_current_tab(self):
        """
        Closes the currently active tab.
        If it's the last tab, the browser will remain open but without an active page.
        """
        if self.page:
            try:
                self.page.close()
                self.page = None # Clear the reference to the closed page
                logger.info("Closed current tab.")
                # If there are other pages, switch to the first one available
                if self.context.pages:
                    self.page = self.context.pages[0]
                    logger.info("Switched to the first available tab.")
                else:
                    logger.info("No more tabs open in the current context.")
            except Exception as e:
                logger.error(f"Failed to close current tab: {e}")
        else:
            logger.warning("No active tab to close.")

    def _cleanup(self):
        """
        Closes the browser and stops the Playwright instance.
        """
        if self.browser:
            try:
                self.browser.close()
                logger.info("Browser closed.")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
            finally:
                self.browser = None
                self.context = None
                self.page = None

        if self.playwright:
            try:
                self.playwright.stop()
                logger.info("Playwright stopped.")
            except Exception as e:
                logger.error(f"Error stopping Playwright: {e}")
            finally:
                self.playwright = None

    def __del__(self):
        """
        Ensures the browser is closed when the object is garbage collected.
        """
        self._cleanup()

# Example Usage (for testing purposes)
if __name__ == "__main__":
    browser_controller = None
    try:
        print("--- Initializing BrowserControl (Chromium) ---")
        browser_controller = BrowserControl(browser_type="chromium")
        time.sleep(2) # Give some time for the browser to open

        print("\n--- Opening Google ---")
        browser_controller.open_url("google.com")
        time.sleep(3)

        print("\n--- Performing a search for 'Playwright Python' ---")
        browser_controller.search("Playwright Python tutorial")
        time.sleep(5)

        print("\n--- Opening a new tab for Wikipedia ---")
        browser_controller.new_tab("wikipedia.org")
        time.sleep(4)

        print("\n--- Closing current tab (Wikipedia) ---")
        browser_controller.close_current_tab()
        time.sleep(2)

        print("\n--- Performing another search for 'CognitiveShell project' ---")
        browser_controller.search("CognitiveShell project")
        time.sleep(5)

    except Exception as e:
        print(f"\nAn error occurred during testing: {e}")
    finally:
        if browser_controller:
            print("\n--- Cleaning up browser ---")
            browser_controller._cleanup()
        print("--- Testing complete ---")

