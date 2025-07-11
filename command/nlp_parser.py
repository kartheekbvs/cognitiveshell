# cognitiveshell/commands/nlp_parser.py

import re

class NLPParser:
    """
    A basic NLP parser for CognitiveShell commands.
    In this initial phase, it uses simple keyword matching to identify
    intents (e.g., 'open', 'search') and extract relevant entities.

    In later phases, this class will be enhanced with more sophisticated
    NLP libraries like spaCy or transformers for better understanding
    of natural language.
    """

    def __init__(self):
        """
        Initializes the NLPParser.
        No complex models are loaded here yet.
        """
        # Define simple patterns for common commands
        self.patterns = {
            "open_app": r"open\s+(.+)",  # e.g., "open vscode", "open chrome"
            "search_web": r"search\s+(.+)\s+on\s+(.+)", # e.g., "search AI papers on arXiv"
            "search_default": r"search\s+(.+)", # e.g., "search AI papers" (uses default search engine)
            "go_to_url": r"(go to|visit|open url)\s+(.+)", # e.g., "go to google.com", "visit youtube.com"
            "close_app": r"close\s+(.+)", # e.g., "close vscode"
            "bring_to_front": r"(bring|focus)\s+(.+)\s+to\s+front", # e.g., "bring chrome to front"
            # Add more patterns as needed for other commands
        }

        # A simple mapping for common app names to their likely executable names
        # This will be expanded and potentially made configurable later.
        self.app_aliases = {
            "vscode": "Code", # On macOS/Linux, it might be 'code', on Windows 'Code.exe'
            "chrome": "Google Chrome", # Or 'chrome.exe'
            "firefox": "Firefox",
            "terminal": "Terminal", # Or 'cmd.exe', 'powershell.exe', 'gnome-terminal'
            "notepad": "notepad.exe", # Windows
            "calculator": "calc.exe", # Windows
            "safari": "Safari", # macOS
            "pages": "Pages", # macOS
            "excel": "EXCEL.EXE", # Windows
            "word": "WINWORD.EXE", # Windows
        }

        # Default search engine for 'search_default' intent
        self.default_search_engine = "google" # Can be configured later

    def parse_command(self, command_text: str) -> dict:
        """
        Parses a natural language command and extracts intent and entities.

        Args:
            command_text (str): The raw command string from the user.

        Returns:
            dict: A dictionary containing 'intent' and 'entities'.
                  Returns {'intent': 'unknown'} if no match is found.
                  Examples:
                  {'intent': 'open_app', 'entities': {'app_name': 'vscode'}}
                  {'intent': 'search_web', 'entities': {'query': 'AI papers', 'site': 'arXiv'}}
                  {'intent': 'go_to_url', 'entities': {'url': 'google.com'}}
        """
        command_text = command_text.lower().strip()

        # Try to match against defined patterns
        for intent, pattern in self.patterns.items():
            match = re.match(pattern, command_text)
            if match:
                entities = {}
                if intent == "open_app" or intent == "close_app" or intent == "bring_to_front":
                    app_name = match.group(1).strip()
                    # Apply simple alias lookup (can be improved with fuzzy matching)
                    entities['app_name'] = self.app_aliases.get(app_name, app_name)
                elif intent == "search_web":
                    entities['query'] = match.group(1).strip()
                    entities['site'] = match.group(2).strip()
                elif intent == "search_default":
                    entities['query'] = match.group(1).strip()
                    entities['site'] = self.default_search_engine # Use default search engine
                elif intent == "go_to_url":
                    entities['url'] = match.group(2).strip()
                    # Ensure URL has a scheme if missing for browser automation
                    if not re.match(r'^[a-zA-Z]+://', entities['url']):
                        entities['url'] = f"https://{entities['url']}"

                return {"intent": intent, "entities": entities}

        # If no specific pattern matches, check for simple "help" or "exit"
        if "help" in command_text:
            return {"intent": "help", "entities": {}}
        if "exit" in command_text or "quit" in command_text:
            return {"intent": "exit", "entities": {}}

        return {"intent": "unknown", "entities": {}}

# Example Usage (for testing purposes, remove in final integration if not needed)
if __name__ == "__main__":
    parser = NLPParser()

    test_commands = [
        "Open VSCode",
        "search AI papers on arXiv",
        "search latest news",
        "Go to google.com",
        "Visit youtube.com",
        "open url wikipedia.org",
        "close Chrome",
        "bring Firefox to front",
        "focus terminal to front",
        "What is the weather?", # Unknown command
        "help",
        "exit",
    ]

    print("--- Testing NLP Parser ---")
    for cmd in test_commands:
        parsed = parser.parse_command(cmd)
        print(f"Command: '{cmd}'")
        print(f"Parsed: {parsed}\n")


