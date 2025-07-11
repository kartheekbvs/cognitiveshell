# cognitiveshell/utils/database.py

import sqlite3
import os
import json
import datetime
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages all interactions with the SQLite database for CognitiveShell.
    Handles database initialization, logging commands, and tracking usage statistics.
    """

    def __init__(self, db_name: str = 'cognitiveshell.db'):
        """
        Initializes the DatabaseManager.

        Args:
            db_name (str): The name of the SQLite database file.
        """
        # Determine the base directory of the project
        # In a Colab notebook, __file__ is not defined.
        # Assuming the notebook is in the 'cognitiveshell' directory,
        # the 'data' directory would be one level up.
        current_dir = os.getcwd() # Get the current working directory (where the notebook is)
        project_root = os.path.abspath(os.path.join(current_dir, '..')) # Go up one level from the notebook location
        self.db_path = os.path.join(project_root, 'data', db_name)

        # Ensure the 'data' directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        self._initialize_db()
        logger.info(f"DatabaseManager initialized. DB Path: {self.db_path}")

    def _get_connection(self):
        """
        Establishes and returns a connection to the SQLite database.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row # Allows accessing columns by name
            return conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise

    def _initialize_db(self):
        """
        Initializes the database by creating necessary tables if they don't exist.
        Tables:
        - commands_log: Stores a log of all executed commands.
        - frequent_queries: Tracks the frequency of search queries.
        - app_usage: Tracks the frequency of app openings.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Table for logging all commands
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS commands_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    command_text TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    entities TEXT, -- Stored as JSON string
                    timestamp TEXT NOT NULL,
                    status TEXT -- 'success' or 'failure'
                )
            """)

            # Table for tracking frequent search queries
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS frequent_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_text TEXT NOT NULL UNIQUE,
                    count INTEGER DEFAULT 1,
                    last_used TEXT NOT NULL
                )
            """)

            # Table for tracking app usage
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_name TEXT NOT NULL UNIQUE,
                    open_count INTEGER DEFAULT 1,
                    last_opened TEXT NOT NULL
                )
            """)
            conn.commit()
            logger.info("Database tables checked/created successfully.")

    def log_command(self, command_text: str, intent: str, entities: dict, status: str = 'success'):
        """
        Logs a command execution to the commands_log table.

        Args:
            command_text (str): The raw command string from the user.
            intent (str): The parsed intent of the command.
            entities (dict): Dictionary of extracted entities.
            status (str): 'success' or 'failure' of the command execution.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
                entities_json = json.dumps(entities) # Convert dict to JSON string for storage

                cursor.execute("""
                    INSERT INTO commands_log (command_text, intent, entities, timestamp, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (command_text, intent, entities_json, timestamp, status))
                conn.commit()
                logger.debug(f"Logged command: '{command_text}' with intent '{intent}' and status '{status}'")
        except sqlite3.Error as e:
            logger.error(f"Error logging command '{command_text}': {e}")

    def update_frequent_query(self, query_text: str):
        """
        Updates the count and last_used timestamp for a frequent query.
        Inserts a new record if the query doesn't exist.

        Args:
            query_text (str): The search query to update/add.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

                cursor.execute("""
                    INSERT INTO frequent_queries (query_text, count, last_used)
                    VALUES (?, 1, ?)
                    ON CONFLICT(query_text) DO UPDATE SET
                        count = count + 1,
                        last_used = ?
                """, (query_text, timestamp, timestamp))
                conn.commit()
                logger.debug(f"Updated frequent query: '{query_text}'")
        except sqlite3.Error as e:
            logger.error(f"Error updating frequent query '{query_text}': {e}")

    def update_app_usage(self, app_name: str):
        """
        Updates the open_count and last_opened timestamp for an application.
        Inserts a new record if the app doesn't exist.

        Args:
            app_name (str): The name of the application to update/add.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

                cursor.execute("""
                    INSERT INTO app_usage (app_name, open_count, last_opened)
                    VALUES (?, 1, ?)
                    ON CONFLICT(app_name) DO UPDATE SET
                        open_count = open_count + 1,
                        last_opened = ?
                """, (app_name, timestamp, timestamp))
                conn.commit()
                logger.debug(f"Updated app usage for: '{app_name}'")
        except sqlite3.Error as e:
            logger.error(f"Error updating app usage for '{app_name}': {e}")

    def get_most_frequent_queries(self, limit: int = 5) -> list[dict]:
        """
        Retrieves the most frequently used search queries.

        Args:
            limit (int): The maximum number of queries to retrieve.

        Returns:
            list[dict]: A list of dictionaries, each representing a frequent query.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT query_text, count, last_used
                    FROM frequent_queries
                    ORDER BY count DESC, last_used DESC
                    LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving frequent queries: {e}")
            return []

    def get_most_used_apps(self, limit: int = 5) -> list[dict]:
        """
        Retrieves the most frequently used applications.

        Args:
            limit (int): The maximum number of apps to retrieve.

        Returns:
            list[dict]: A list of dictionaries, each representing an app.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT app_name, open_count, last_opened
                    FROM app_usage
                    ORDER BY open_count DESC, last_opened DESC
                    LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving most used apps: {e}")
            return []

    def get_recent_commands(self, limit: int = 10) -> list[dict]:
        """
        Retrieves the most recent commands from the log.

        Args:
            limit (int): The maximum number of commands to retrieve.

        Returns:
            list[dict]: A list of dictionaries, each representing a logged command.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT command_text, intent, entities, timestamp, status
                    FROM commands_log
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
                # Convert entities JSON string back to dict
                rows = []
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    if row_dict['entities']:
                        row_dict['entities'] = json.loads(row_dict['entities'])
                    rows.append(row_dict)
                return rows
        except sqlite3.Error as e:
            logger.error(f"Error retrieving recent commands: {e}")
            return []


# Example Usage (for testing purposes)
if __name__ == "__main__":
    # Ensure this runs from the project root or adjust db_name for testing
    # For testing, let's use a temporary DB name so it doesn't interfere
    # with the actual app DB if it were already running.
    temp_db_name = 'test_cognitiveshell.db'
    db_manager = DatabaseManager(db_name=temp_db_name)

    print(f"--- Testing DatabaseManager with '{temp_db_name}' ---")

    # 1. Log some commands
    print("\n--- Logging commands ---")
    db_manager.log_command("open vscode", "open_app", {"app_name": "vscode"}, "success")
    db_manager.log_command("search python tutorial", "search_default", {"query": "python tutorial"}, "success")
    db_manager.log_command("go to github.com", "go_to_url", {"url": "https://github.com"}, "success")
    db_manager.log_command("close chrome", "close_app", {"app_name": "chrome"}, "failure")
    db_manager.log_command("open vscode", "open_app", {"app_name": "vscode"}, "success") # Log again for frequency
    time.sleep(0.1) # Small delay for timestamp difference
    db_manager.log_command("search python tutorial", "search_default", {"query": "python tutorial"}, "success")
    time.sleep(0.1)
    db_manager.log_command("search machine learning", "search_default", {"query": "machine learning"}, "success")


    # 2. Update frequent queries
    print("\n--- Updating frequent queries ---")
    db_manager.update_frequent_query("python tutorial")
    db_manager.update_frequent_query("AI papers")
    db_manager.update_frequent_query("python tutorial") # Update again
    db_manager.update_frequent_query("machine learning")

    # 3. Update app usage
    print("\n--- Updating app usage ---")
    db_manager.update_app_usage("vscode")
    db_manager.update_app_usage("chrome")
    db_manager.update_app_usage("vscode") # Update again
    db_manager.update_app_usage("firefox")

    # 4. Retrieve data
    print("\n--- Retrieving most frequent queries ---")
    queries = db_manager.get_most_frequent_queries(limit=3)
    for q in queries:
        print(f"- Query: '{q['query_text']}', Count: {q['count']}, Last Used: {q['last_used']}")

    print("\n--- Retrieving most used apps ---")
    apps = db_manager.get_most_used_apps(limit=3)
    for a in apps:
        print(f"- App: '{a['app_name']}', Open Count: {a['open_count']}, Last Opened: {a['last_opened']}")

    print("\n--- Retrieving recent commands ---")
    recent_cmds = db_manager.get_recent_commands(limit=5)
    for cmd in recent_cmds:
        print(f"- Command: '{cmd['command_text']}', Intent: '{cmd['intent']}', Status: '{cmd['status']}', Entities: {cmd['entities']}")

    # Clean up the test database file
    if os.path.exists(db_manager.db_path):
        os.remove(db_manager.db_path)
        print(f"\nCleaned up test database: {db_manager.db_path}")

    print("--- Database testing complete ---")
