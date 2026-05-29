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
        self._daddy_running = False

    def load_icon(self):
        if ICON_PATH.exists():
            return Image.open(str(ICON_PATH))
        
        img  = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([2, 2, 62, 62], fill=(0, 180, 255, 255))
        return img
    
    