import sys
import os
from loguru import logger

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def run_with_tray():
    from core.tray import TrayApp
    from startup import StartupManager
    import main as daddy_main

    logger.info("Launching Daddy with system tray...")

    startup_manager = StartupManager()

    def daddy_runner():
        daddy_main.main()

    tray = TrayApp(
        daddy_runner=daddy_runner,
        startup_manager=startup_manager
    )
    tray.run()

def run_without_tray():
    import main as daddy_main
    logger.info("Launching Daddy without system tray...")
    daddy_main.main()

if __name__ == "__main__":
    if "--notray" in sys.argv:
        run_without_tray()
    else:
        run_with_tray()
