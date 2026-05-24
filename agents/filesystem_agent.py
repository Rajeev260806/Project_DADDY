import os
import shutil
import fnmatch
from pathlib import Path
from datetime import datetime
from loguru import logger
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from agents.base_agent import BaseAgent
from config import OLLAMA_MODEL, OLLAMA_BASE_URL

SHORTCUTS = {
    "desktop":   str(Path.home() / "Desktop"),
    "documents": str(Path.home() / "Documents"),
    "downloads": str(Path.home() / "Downloads"),
    "pictures":  str(Path.home() / "Pictures"),
    "music":     str(Path.home() / "Music"),
    "videos":    str(Path.home() / "Videos"),
    "home":      str(Path.home()),
}

FILE_AGENT_PROMPT = """You are a file system command parser for a Windows 11 computer.
The user will give you a plain English command about files or folders.
You must respond with ONLY a JSON object — no explanation, no extra text.

Supported actions and their JSON format:

1. Create folder:
{"action":"create_folder","path":"Desktop","name":"MyFolder"}

2. Delete file or folder:
{"action":"delete","path":"Desktop","name":"MyFolder"}

3. Rename file or folder:
{"action":"rename","path":"Desktop","old_name":"OldName","new_name":"NewName"}

4. Move file or folder:
{"action":"move","name":"file.txt","from_path":"Desktop","to_path":"Documents"}

5. List contents of a folder:
{"action":"list","path":"Desktop"}

6. Find files by name or extension:
{"action":"find","path":"Downloads","pattern":"*.pdf"}

7. Create a text file with content:
{"action":"create_file","path":"Desktop","name":"notes.txt","content":"Hello World"}

8. Read a text file:
{"action":"read_file","path":"Desktop","name":"notes.txt"}

9. Get file/folder info (size, date):
{"action":"info","path":"Desktop","name":"report.docx"}

Rules:
- Use short folder names like Desktop, Documents, Downloads, Pictures, Music, Videos
- For patterns use wildcard like *.pdf *.txt *.py
- name field is always just the file/folder name, never a full path
- Respond ONLY with the JSON. Nothing else.
"""

class FileSystemAgent(BaseAgent):
    def __init__(self):
        super().__init__("FileSystemAgent")
        self.llm = ChatOllama(
            model = OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature = 0
        )

    def resolve_path(self,folder:str)->Path:
        folder = folder.strip().lower()
        if folder in SHORTCUTS:
            return Path(SHORTCUTS[folder])
        p = Path(folder)
        if p.is_absolute():
            return p
        return Path.home()/folder
    
    def parse_command(self,command:str)->dict:
        message = [
            SystemMessage(FILE_AGENT_PROMPT),
            HumanMessage(command)
        ]

        response = self.llm.invoke(message)
        raw = response.content.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1])

        import json
        return json.loads(raw)
    
    def create_folder(self,data:dict)->str:
        base_url = self.resolve_path(data.get("path","home"))
        folder = base_url / data["name"]

        if folder.exists():
            return f"Folder '{data['name']}' already exists in {base_url.name}."
        folder.mkdir(parents=True,exist_ok=True)
        logger.success(f"Created folder: {folder}")
        return f"Done! Folder '{data['name']}' created in {base_url.name}."
    
    def delete(self,data:dict)->str:
        base_url = self.resolve_path(data.get("path","home"))
        folder = base_url / data["name"]

        if not folder.exists():
            return f"'{data['name']}' not found in {base_url.name}."
        if folder.is_dir():
            shutil.rmtree(folder)
            logger.success(f"Deleted folder: {folder}")
            return f"Done! Folder '{data['name']}' deleted from {base_url.name}."
        else:
            folder.unlink()
            logger.success(f"Deleted file: {folder}")
            return f"Done! File '{data['name']}' deleted from {base_url.name}."
        
    def rename(self,data:dict)->str:
        base_url = self.resolve_path(data.get("path","name"))
        old_name = base_url / data["old_name"]
        new_name = base_url / data["new_name"]

        if not old_name.exists():
            return f"'{data['old_name']}' not found in {base_url.name}."
        
        if new_name.exists():
            return f"'{data['new_name']}' already exists. Choose a different name."
        
        old_name.rename(new_name)
        logger.success(f"Renamed: {old_name} → {new_name}")
        return f"Done! '{data['old_name']}' renamed to '{data['new_name']}'."
    
    def move(self,data:dict)->str:
        from_path = self.resolve_path(data.get("from_path", "home"))
        to_path = self.resolve_path(data.get("to_path", "home"))
        source = from_path / data["name"]
        dest = to_path / data["name"]

        if not source.exists():
            return f"'{data['name']}' not found in {from_path.name}."
        
        to_path.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(dest))
        logger.success(f"Moved: {source} → {dest}")
        return f"Done! '{data['name']}' moved from {from_path.name} to {to_path.name}."
    
    def list(self,data:dict)->str:
        folder = self.resolve_path(data.get("path", "home"))
        if not folder.exists():
            return f"Folder '{folder.name}' not found."
        items = list(folder.iterdir())
        if not items:
            return f"'{folder.name}' is empty."
        folders = sorted([i.name for i in items if i.is_dir()])
        files   = sorted([i.name for i in items if i.is_file()])
        result  = f"Contents of {folder.name}:\n"
        if folders:
            result += f"  Folders ({len(folders)}): {', '.join(folders)}\n"
        if files:
            result += f"  Files ({len(files)}): {', '.join(files)}"
        return result.strip()

    def find(self,data:dict)->str:
        folder = self.resolve_path(data.get("path","home"))
        pattern = data.get("pattern","*")
        if not folder.exists():
            return f"Folder '{folder.name}' not found."
        matches = [
            str(p.relative_to(folder))
            for p in folder.rglob("*")
            if fnmatch.fnmatch(p.name, pattern)
        ]
        if not matches:
            return f"No files matching '{pattern}' found in {folder.name}."
        result = f"Found {len(matches)} file(s) matching '{pattern}' in {folder.name}:\n"
        result += "\n".join(f"  {m}" for m in matches[:20])  
        if len(matches) > 20:
            result += f"\n  ... and {len(matches) - 20} more."
        return result

    def create_file(self,data:dict)->str:
        base_url = self.resolve_path(data.get("path", "home"))
        target = base_url / data["name"]
        content = data.get("content", "")
        target.write_text(content, encoding="utf-8")
        logger.success(f"Created file: {target}")
        return f"Done! File '{data['name']}' created in {base_url.name}."
    
    def read_file(self, data: dict) -> str:
        base_url = self.resolve_path(data.get("path", "home"))
        target = base_url / data["name"]
        if not target.exists():
            return f"File '{data['name']}' not found in {base_url.name}."
        if target.stat().st_size > 50000:
            return f"File '{data['name']}' is too large to read aloud."
        content = target.read_text(encoding="utf-8", errors="ignore")
        return f"Contents of '{data['name']}':\n{content[:1000]}"
    
    def info(self, data: dict) -> str:
        base_url = self._resolve_path(data.get("path", "home"))
        target = base_url / data["name"]
        if not target.exists():
            return f"'{data['name']}' not found in {base_url.name}."
        stat = target.stat()
        size = stat.st_size
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        kind = "Folder" if target.is_dir() else "File"
        size_str = (
            f"{size} bytes" if size < 1024
            else f"{size/1024:.1f} KB" if size < 1024**2
            else f"{size/1024**2:.1f} MB"
        )
        return (
            f"{kind}: '{data['name']}'\n"
            f"  Location : {base_url}\n"
            f"  Size     : {size_str}\n"
            f"  Modified : {modified}"
        )
    
    def handle(self,command:str)->str:
        logger.info(f"FileSystemAgent handling: {command}")

        data = self.parse_command(command)
        logger.debug(f"Parsed action: {data}")

        action = data.get("action", "")

        actions = {
            "create_folder": self.create_folder,
            "delete":        self.delete,
            "rename":        self.rename,
            "move":          self.move,
            "list":          self.list,
            "find":          self.find,
            "create_file":   self.create_file,
            "read_file":     self.read_file,
            "info":          self.info,
        }

        if action not in actions:
            return f"Sorry, I don't know how to do '{action}' yet."

        return actions[action](data)