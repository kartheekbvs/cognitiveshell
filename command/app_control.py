# cognitiveshell/commands/app_control.py

import subprocess
import platform
import logging
import psutil
import time

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AppControl:
    """
    Manages application processes on the operating system.
    Handles opening, closing, and attempting to bring applications to the front.
    """

    def __init__(self):
        """
        Initializes the AppControl module.
        Determines the operating system to use appropriate commands.
        """
        self.os_name = platform.system()
        logger.info(f"AppControl initialized for OS: {self.os_name}")

    def _get_app_executable_name(self, app_name: str) -> str:
        """
        Helper method to get the common executable name for an app based on OS.
        This is a simplified mapping and might need expansion for more apps
        or a configuration file in a real-world scenario.

        Args:
            app_name (str): The common name of the application (e.g., "vscode", "chrome").

        Returns:
            str: The executable name or command to launch the app.
        """
        app_name_lower = app_name.lower()

        if self.os_name == "Windows":
            if "vscode" in app_name_lower:
                return "Code.exe"
            elif "chrome" in app_name_lower:
                return "chrome.exe"
            elif "firefox" in app_name_lower:
                return "firefox.exe"
            elif "notepad" in app_name_lower:
                return "notepad.exe"
            elif "calculator" in app_name_lower:
                return "calc.exe"
            elif "word" in app_name_lower:
                return "WINWORD.EXE"
            elif "excel" in app_name_lower:
                return "EXCEL.EXE"
            elif "powerpoint" in app_name_lower:
                return "POWERPNT.EXE"
            elif "cmd" in app_name_lower or "command prompt" in app_name_lower:
                return "cmd.exe"
            elif "powershell" in app_name_lower:
                return "powershell.exe"
            # Default to the app_name itself, Windows might find it
            return app_name
        elif self.os_name == "Darwin":  # macOS
            if "vscode" in app_name_lower:
                return "Visual Studio Code" # App bundle name
            elif "chrome" in app_name_lower:
                return "Google Chrome"
            elif "firefox" in app_name_lower:
                return "Firefox"
            elif "safari" in app_name_lower:
                return "Safari"
            elif "terminal" in app_name_lower:
                return "Terminal"
            elif "pages" in app_name_lower:
                return "Pages"
            elif "numbers" in app_name_lower:
                return "Numbers"
            elif "keynote" in app_name_lower:
                return "Keynote"
            # Default to the app_name itself, 'open -a' might find it
            return app_name
        else:  # Linux and other Unix-like systems
            if "vscode" in app_name_lower:
                return "code" # Command line executable
            elif "chrome" in app_name_lower:
                return "google-chrome" # Or 'chromium-browser'
            elif "firefox" in app_name_lower:
                return "firefox"
            elif "terminal" in app_name_lower:
                return "gnome-terminal" # Or 'konsole', 'xterm', etc.
            # Default to the app_name itself, assuming it's a command in PATH
            return app_name_lower


    def open_app(self, app_name: str) -> bool:
        """
        Opens a specified application.

        Args:
            app_name (str): The name of the application to open.

        Returns:
            bool: True if the app was successfully launched or already open, False otherwise.
        """
        executable_name = self._get_app_executable_name(app_name)
        logger.info(f"Attempting to open '{app_name}' (executable: '{executable_name}')")

        try:
            if self.os_name == "Windows":
                # Use 'start' command on Windows to open applications
                subprocess.Popen(['start', '', executable_name], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            elif self.os_name == "Darwin":  # macOS
                # Use 'open -a' to open applications by their bundle name
                subprocess.Popen(['open', '-a', executable_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:  # Linux/Unix
                # Directly execute the command, assuming it's in PATH
                subprocess.Popen([executable_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"Successfully sent command to open '{app_name}'.")
            return True
        except FileNotFoundError:
            logger.error(f"Application '{app_name}' (executable: '{executable_name}') not found.")
            return False
        except Exception as e:
            logger.error(f"Error opening '{app_name}': {e}")
            return False

    def close_app(self, app_name: str) -> bool:
        """
        Closes a specified application by terminating its processes.

        Args:
            app_name (str): The name of the application to close.

        Returns:
            bool: True if the app processes were found and terminated, False otherwise.
        """
        executable_name = self._get_app_executable_name(app_name)
        logger.info(f"Attempting to close '{app_name}' (targeting processes like '{executable_name}')")
        
        found_and_terminated = False
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                # Check if process name or executable path contains the app name/executable
                process_name_lower = proc.info['name'].lower()
                process_exe_lower = proc.info['exe'].lower() if proc.info['exe'] else ''

                if executable_name.lower() in process_name_lower or \
                   executable_name.lower() in process_exe_lower:
                    logger.info(f"Found process '{proc.info['name']}' (PID: {proc.info['pid']}). Terminating...")
                    proc.terminate() # Request termination
                    found_and_terminated = True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Process no longer exists, access denied, or zombie process
                continue
            except Exception as e:
                logger.warning(f"Could not check or terminate process {proc.info.get('name', 'N/A')} (PID: {proc.info.get('pid', 'N/A')}): {e}")
        
        if found_and_terminated:
            # Give some time for processes to terminate
            time.sleep(1)
            # Verify if processes are actually gone
            still_running = False
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    process_name_lower = proc.info['name'].lower()
                    process_exe_lower = proc.info['exe'].lower() if proc.info['exe'] else ''
                    if executable_name.lower() in process_name_lower or \
                       executable_name.lower() in process_exe_lower:
                        still_running = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            if still_running:
                logger.warning(f"Some processes for '{app_name}' might still be running after termination attempt.")
                return False
            else:
                logger.info(f"Successfully closed processes for '{app_name}'.")
                return True
        else:
            logger.info(f"No active processes found for '{app_name}'.")
            return False

    def bring_to_front(self, app_name: str) -> bool:
        """
        Attempts to bring a specified application's window to the foreground.
        This is highly OS-specific and can be unreliable or require external tools.

        Args:
            app_name (str): The name of the application to bring to the front.

        Returns:
            bool: True if the operation was attempted (success not guaranteed), False otherwise.
        """
        executable_name = self._get_app_executable_name(app_name)
        logger.info(f"Attempting to bring '{app_name}' to front (targeting: '{executable_name}')")

        try:
            if self.os_name == "Windows":
                # On Windows, bringing an app to front reliably requires pywinauto or win32gui.
                # A simple 'start' command will just open a new instance or bring it to front
                # if it's already running and not minimized. This is not ideal.
                # For a robust solution, consider: pip install pywinauto
                # from pywinauto.application import Application
                # app = Application().connect(title_re=f".*{app_name}.*")
                # app.top_window().set_focus()
                logger.warning("Bringing applications to front on Windows is complex and requires specific libraries (e.g., pywinauto). Re-opening might be the only simple option.")
                # As a fallback, try to re-open, which might bring it to front if already open
                # or open a new instance. This is NOT a true "bring to front".
                self.open_app(app_name)
                return True
            elif self.os_name == "Darwin":  # macOS
                # Use AppleScript to activate the application
                script = f'tell application "{executable_name}" to activate'
                subprocess.run(['osascript', '-e', script], check=True, capture_output=True)
                logger.info(f"Successfully sent command to bring '{app_name}' to front on macOS.")
                return True
            else:  # Linux/Unix
                # On Linux, this often requires 'wmctrl' or 'xdotool' to be installed.
                # Example with wmctrl (needs to be installed: sudo apt install wmctrl)
                # find_window_cmd = f"wmctrl -l | grep -i '{executable_name}' | awk '{{print $1}}'"
                # window_id = subprocess.check_output(find_window_cmd, shell=True, text=True).strip().split('\n')[0]
                # if window_id:
                #     subprocess.run(['wmctrl', '-ia', window_id], check=True)
                #     logger.info(f"Successfully attempted to bring '{app_name}' to front on Linux.")
                #     return True
                logger.warning("Bringing applications to front on Linux often requires 'wmctrl' or 'xdotool' to be installed. This functionality is not fully implemented in this basic version.")
                # Fallback: try to open, which might bring it to front if already open
                self.open_app(app_name)
                return True
        except FileNotFoundError:
            logger.error(f"Required command for '{self.os_name}' (e.g., 'osascript', 'wmctrl') not found.")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Error bringing '{app_name}' to front: {e.stderr.decode().strip()}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred while bringing '{app_name}' to front: {e}")
            return False

# Example Usage (for testing purposes)
if __name__ == "__main__":
    app_controller = AppControl()

    print("--- Testing AppControl ---")

    # Test opening an app
    print("\n--- Opening Notepad (Windows) or TextEdit (macOS) or gedit (Linux) ---")
    if app_controller.os_name == "Windows":
        app_controller.open_app("notepad")
    elif app_controller.os_name == "Darwin":
        app_controller.open_app("TextEdit") # Or "Terminal"
    else:
        app_controller.open_app("gedit") # Or "gnome-terminal"
    time.sleep(3)

    # Test closing an app
    print("\n--- Closing the opened app ---")
    if app_controller.os_name == "Windows":
        app_controller.close_app("notepad")
    elif app_controller.os_name == "Darwin":
        app_controller.close_app("TextEdit") # Or "Terminal"
    else:
        app_controller.close_app("gedit") # Or "gnome-terminal"
    time.sleep(2)

    # Test opening Chrome/Google Chrome/google-chrome
    print("\n--- Opening Chrome/Google Chrome ---")
    app_controller.open_app("chrome")
    time.sleep(5) # Give time for Chrome to open

    # Test bringing Chrome to front (will vary by OS)
    print("\n--- Bringing Chrome to front (may not work reliably on all OS) ---")
    app_controller.bring_to_front("chrome")
    time.sleep(3)

    # Test closing Chrome
    print("\n--- Closing Chrome ---")
    app_controller.close_app("chrome")
    time.sleep(2)

    print("\n--- Testing complete ---")

