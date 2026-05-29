import sys
import winreg
from pathlib import Path
from loguru import logger
from config import ASSISTANT_NAME

REGISTRY_KEY  = r"Software\Microsoft\Windows\CurrentVersion\Run"
REGISTRY_NAME = f"{ASSISTANT_NAME}Assistant"

class StartupManager:
    def __init__(self):
        self.launcher_path = str(Path(__file__).parent / "launcher.py")
        self.python_path   = sys.executable

    def get_startup_command(self) -> str:
        return f'"{self.python_path}" "{self.launcher_path}"'

    def enable(self) -> str:
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                REGISTRY_KEY,
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(
                key,
                REGISTRY_NAME,
                0,
                winreg.REG_SZ,
                self.get_startup_command()
            )
            winreg.CloseKey(key)
            logger.success("Auto-start enabled in Windows Registry.")
            return f"{ASSISTANT_NAME} will now start automatically on Windows boot."
        except Exception as e:
            logger.error(f"Failed to enable startup: {e}")
            return f"Failed to enable auto-start: {e}"

    def disable(self) -> str:
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                REGISTRY_KEY,
                0,
                winreg.KEY_SET_VALUE
            )
            try:
                winreg.DeleteValue(key, REGISTRY_NAME)
                logger.success("Auto-start disabled.")
                result = f"{ASSISTANT_NAME} will no longer start automatically."
            except FileNotFoundError:
                result = "Auto-start was not enabled."
            winreg.CloseKey(key)
            return result
        except Exception as e:
            logger.error(f"Failed to disable startup: {e}")
            return f"Failed to disable auto-start: {e}"

    def is_enabled(self) -> bool:
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                REGISTRY_KEY,
                0,
                winreg.KEY_READ
            )
            try:
                winreg.QueryValueEx(key, REGISTRY_NAME)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception:
            return False

    def status(self) -> str:
        if self.is_enabled():
            cmd = self.get_startup_command()
            return f"Auto-start is ENABLED.\nCommand: {cmd}"
        return "Auto-start is DISABLED."