import threading
import sys
import os
from pathlib import Path
from loguru import logger
import pystray
from PIL import Image
from pystray import MenuItem as item
from config import ASSISTANT_NAME

ICON_PATH = Path("assets/daddy_icon.png")

class TrayApp:

    def __init__(self, daddy_runner, startup_manager):
        self.daddy_runner = daddy_runner
        self.startup_manager = startup_manager
        self.daddy_thread = None
        self.icon = None
        self.daddy_running = False

    def load_icon(self):
        if ICON_PATH.exists():
            return Image.open(str(ICON_PATH))
        
        img  = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([2, 2, 62, 62], fill=(0, 180, 255, 255))
        return img
    
    def start_daddy(self):
        if self._daddy_running:
            logger.warning("Daddy is already running.")
            return
        self._daddy_running = True
        self.daddy_thread   = threading.Thread(
            target=self.run_daddy_safe,
            daemon=True,
            name="daddyThread"
        )
        self.daddy_thread.start()
        logger.info("daddy thread started.")

    def run_daddy_safe(self):
        try:
            self.daddy_runner()
        except SystemExit:
            pass
        except Exception as e:
            logger.error(f"daddy crashed: {e}")
        finally:
            self._daddy_running = False
            logger.info("daddy thread ended.")

    def on_open(self, icon, item):
        try:
            import subprocess
            subprocess.Popen(
                ["python", "main.py"],
                creationflags=0x00000010   
            )
        except Exception as e:
            logger.error(f"Failed to open daddy window: {e}")
    
    def on_restart(self, icon, item):
        logger.info("Restarting daddy...")
        self._daddy_running = False
        self.start_daddy()

    def on_enable_startup(self, icon, item):
        result = self.startup_manager.enable()
        logger.info(result)

    def on_disable_startup(self, icon, item):
        result = self.startup_manager.disable()
        logger.info(result)

    def on_status(self, icon, item):
        status = self.startup_manager.status()
        logger.info(f"Startup status: {status}")

    def on_quit(self, icon, item):
        logger.info("Quitting daddy from tray...")
        self._daddy_running = False
        icon.stop()
        sys.exit(0)

    def build_menu(self) -> pystray.Menu:
        startup_enabled = self.startup_manager.is_enabled()

        return pystray.Menu(
            item(f"{ASSISTANT_NAME} — Personal Assistant", None, enabled=False),
            pystray.Menu.SEPARATOR,
            item("Open Daddy",self.on_open),
            item("Restart Daddy",self.on_restart),
            pystray.Menu.SEPARATOR,
            item(
                "Enable Auto-Start",
                self.on_enable_startup,
                enabled=not startup_enabled
            ),
            item(
                "Disable Auto-Start",
                self.on_disable_startup,
                enabled=startup_enabled
            ),
            item("Startup Status",self.on_status),
            pystray.Menu.SEPARATOR,
            item("Quit",self.on_quit),
        )
    
    def run(self):
        logger.info("Starting system tray...")

        self.start_daddy()

        icon_image = self.load_icon()
        self.icon  = pystray.Icon(
            name=ASSISTANT_NAME,
            icon=icon_image,
            title=f"{ASSISTANT_NAME} — Running",
            menu=self.build_menu()
        )

        logger.success("System tray icon active.")
        self.icon.run()