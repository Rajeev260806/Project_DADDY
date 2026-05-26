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

1. Create a single folder:
{"action":"create_folder","path":"Desktop","name":"MyFolder"}

2. Delete a single file or folder:
{"action":"delete","path":"Desktop","name":"MyFolder"}

3. Rename a file or folder:
{"action":"rename","path":"Desktop","old_name":"OldName","new_name":"NewName"}

4. Move a file or folder:
{"action":"move","name":"file.txt","from_path":"Desktop","to_path":"Documents"}

5. List contents of a folder:
{"action":"list","path":"Desktop"}

6. Find files by name or extension:
{"action":"find","path":"Downloads","pattern":"*.pdf"}

7. Create a single text file with content:
{"action":"create_file","path":"Desktop","name":"notes.txt","content":"Hello World"}

8. Read a text file:
{"action":"read_file","path":"Desktop","name":"notes.txt"}

9. Get file/folder info (size, date):
{"action":"info","path":"Desktop","name":"report.docx"}

10. Delete multiple files matching a pattern (wildcard):
{"action":"delete_pattern","path":"Downloads/Video","pattern":"Moviesda*"}
Use when: delete all PDFs, delete every file starting with X, delete files containing Y

11. Create MULTIPLE files at once:
{"action":"create_files","path":"Desktop","files":["file_1.txt","file_2.txt","file_3.txt"]}

Use this when:
- User says "create 3 files named file_1.txt, file_2.txt, file_3.txt"
- User says "create files file_n.txt where n is 1 to 5"   → expand to ["file_1.txt","file_2.txt","file_3.txt","file_4.txt","file_5.txt"]
- User says "create two files sample.txt and portfolio.txt" → ["sample.txt","portfolio.txt"]
- User says "create 4 text files named report_1 to report_4" → ["report_1.txt","report_2.txt","report_3.txt","report_4.txt"]
- Any command involving creating more than one file

YOU must expand the pattern into a full list inside the JSON.
Never use placeholders like "file_n" — always expand to real names.

12. Delete MULTIPLE specific files at once (explicit names or expanded pattern):
{"action":"delete_files","path":"Desktop","files":["sample.txt","portfolio.txt"]}

Use this when:
- User says "delete sample.txt and portfolio.txt"
- User says "delete file_1.txt, file_2.txt and file_3.txt"
- User says "delete files file_n.txt where n is 1 to 3" → expand to ["file_1.txt","file_2.txt","file_3.txt"]
- User says "remove two files named sample.txt and portfolio.txt"
- Any command involving deleting more than one explicitly named file

YOU must expand patterns into full list of real filenames inside the JSON.

DECISION GUIDE:
- Single file creation           → create_file
- Multiple files, any pattern    → create_files  (YOU expand the list)
- Single file/folder deletion    → delete
- Multiple explicit files        → delete_files  (YOU expand the list)
- Multiple files by wildcard     → delete_pattern

Rules:
- path uses short names: Desktop, Documents, Downloads, Pictures, Music, Videos
- Subpaths are allowed: Downloads/Video, Desktop/Projects
- name field is always a single file/folder name — never a full path
- files field is always a fully expanded JSON array of filenames — never placeholders
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
        for alias, full_path in SHORTCUTS.items():
            if folder.lower().startswith(alias):
                remainder = folder[len(alias):].lstrip("/\\")
                if remainder:
                    return Path(full_path) / remainder
                return Path(full_path)
        p = Path(folder)
        if p.is_absolute():
            return p
        return Path.home()/folder
    
    def find_actual_name(self,base:Path,spoken_name:str)->str:
        if not base.exists():
            return spoken_name
        spoken_clean = spoken_name.lower().replace(" ", "").replace("_", "").replace("-", "")
        for item in base.iterdir():
            item_clean = item.name.lower().replace("_", "").replace("-", "")
            if item_clean == spoken_clean:
                return item.name
        return spoken_name

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
    
    def create_folder(self, data: dict) -> str:
        base_url = self.resolve_path(data.get("path", "home"))
        folder   = base_url / data["name"]
        if folder.exists():
            return f"Folder '{data['name']}' already exists in {base_url.name}."
        folder.mkdir(parents=True, exist_ok=True)
        logger.success(f"Created folder: {folder}")
        return f"Done! Folder '{data['name']}' created in {base_url.name}."

    def delete(self, data: dict) -> str:
        base_url = self.resolve_path(data.get("path", "home"))
        target   = base_url / self.find_actual_name(base_url, data["name"])
        if not target.exists():
            return f"'{data['name']}' not found in {base_url.name}."
        if target.is_dir():
            shutil.rmtree(target)
            logger.success(f"Deleted folder: {target}")
            return f"Done! Folder '{target.name}' deleted from {base_url.name}."
        else:
            target.unlink()
            logger.success(f"Deleted file: {target}")
            return f"Done! File '{target.name}' deleted from {base_url.name}."

    def rename(self, data: dict) -> str:
        base_url = self.resolve_path(data.get("path", "home"))
        old_name = self.find_actual_name(base_url, data["old_name"])
        old      = base_url / old_name
        new      = base_url / data["new_name"]
        if not old.exists():
            return f"'{old_name}' not found in {base_url.name}."
        if new.exists():
            return f"'{data['new_name']}' already exists. Choose a different name."
        old.rename(new)
        logger.success(f"Renamed: {old} → {new}")
        return f"Done! '{old_name}' renamed to '{data['new_name']}'."

    def move(self, data: dict) -> str:
        from_path = self.resolve_path(data.get("from_path", "home"))
        to_path   = self.resolve_path(data.get("to_path", "home"))
        name      = self.find_actual_name(from_path, data["name"])
        source    = from_path / name
        dest      = to_path / name
        if not source.exists():
            return f"'{name}' not found in {from_path.name}."
        to_path.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(dest))
        logger.success(f"Moved: {source} → {dest}")
        return f"Done! '{name}' moved from {from_path.name} to {to_path.name}."

    def list(self, data: dict) -> str:
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

    def find(self, data: dict) -> str:
        folder  = self.resolve_path(data.get("path", "home"))
        pattern = data.get("pattern", "*")
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

    def create_file(self, data: dict) -> str:
        base_url = self.resolve_path(data.get("path", "home"))
        target   = base_url / data["name"]
        content  = data.get("content", "")
        base_url.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        logger.success(f"Created file: {target}")
        return f"Done! File '{data['name']}' created in {base_url.name}."

    def read_file(self, data: dict) -> str:
        base_url = self.resolve_path(data.get("path", "home"))
        target   = base_url / self.find_actual_name(base_url, data["name"])
        if not target.exists():
            return f"File '{data['name']}' not found in {base_url.name}."
        if target.stat().st_size > 50000:
            return f"File '{data['name']}' is too large to read aloud."
        content = target.read_text(encoding="utf-8", errors="ignore")
        return f"Contents of '{target.name}':\n{content[:1000]}"

    def info(self, data: dict) -> str:
        base_url = self.resolve_path(data.get("path", "home"))
        name     = self.find_actual_name(base_url, data["name"])
        target   = base_url / name
        if not target.exists():
            return f"'{name}' not found in {base_url.name}."
        stat     = target.stat()
        size     = stat.st_size
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        kind     = "Folder" if target.is_dir() else "File"
        size_str = (
            f"{size} bytes"        if size < 1024     else
            f"{size/1024:.1f} KB"  if size < 1024**2  else
            f"{size/1024**2:.1f} MB"
        )
        return (
            f"{kind}: '{name}'\n"
            f"  Location : {base_url}\n"
            f"  Size     : {size_str}\n"
            f"  Modified : {modified}"
        )

    def delete_pattern(self, data: dict) -> str:
        folder  = self.resolve_path(data.get("path", "home"))
        pattern = data.get("pattern", "")
        if not pattern:
            return "No pattern provided. Please specify what files to delete."
        if not folder.exists():
            return f"Folder '{folder.name}' not found."
        matched = [
            item for item in folder.iterdir()
            if item.is_file() and fnmatch.fnmatch(item.name, pattern)
        ]
        if not matched:
            return f"No files matching '{pattern}' found in '{folder.name}'."
        deleted = []
        failed  = []
        for item in matched:
            try:
                item.unlink()
                deleted.append(item.name)
                logger.success(f"Deleted: {item}")
            except Exception as e:
                failed.append(item.name)
                logger.error(f"Failed to delete {item}: {e}")
        result = f"Deleted {len(deleted)} file(s) matching '{pattern}' from '{folder.name}'."
        if deleted:
            preview = ', '.join(deleted[:5])
            result += f"\n  Deleted: {preview}"
            if len(deleted) > 5:
                result += f" ... and {len(deleted) - 5} more."
        if failed:
            result += f"\n  Failed: {', '.join(failed)}"
        return result


    def create_files(self, data: dict) -> str:
        base_url   = self.resolve_path(data.get("path", "home"))
        files      = data.get("files", [])
        content    = data.get("content", "")   

        if not files:
            return "No file names provided. Please specify the files to create."

        base_url.mkdir(parents=True, exist_ok=True)

        created  = []
        skipped  = []
        failed   = []

        for filename in files:
            target = base_url / filename
            if target.exists():
                skipped.append(filename)
                continue
            try:
                target.write_text(content, encoding="utf-8")
                created.append(filename)
                logger.success(f"Created file: {target}")
            except Exception as e:
                failed.append(filename)
                logger.error(f"Failed to create {filename}: {e}")

        result = f"Created {len(created)} file(s) in '{base_url.name}'."

        if created:
            preview = ', '.join(created[:5])
            result += f"\n  Created : {preview}"
            if len(created) > 5:
                result += f" ... and {len(created) - 5} more."

        if skipped:
            result += f"\n  Skipped : {', '.join(skipped)} — already exist."

        if failed:
            result += f"\n  Failed  : {', '.join(failed)}"

        return result

    def delete_files(self, data: dict) -> str:        
        base_url = self.resolve_path(data.get("path", "home"))
        files    = data.get("files", [])

        if not files:
            return "No file names provided. Please specify the files to delete."

        if not base_url.exists():
            return f"Folder '{base_url.name}' not found."

        deleted  = []
        not_found = []
        failed   = []

        for filename in files:
            real_name = self.find_actual_name(base_url, filename)
            target    = base_url / real_name

            if not target.exists():
                not_found.append(filename)
                continue

            if target.is_dir():
                failed.append(f"{filename} (is a folder — use delete action instead)")
                continue

            try:
                target.unlink()
                deleted.append(real_name)
                logger.success(f"Deleted: {target}")
            except Exception as e:
                failed.append(filename)
                logger.error(f"Failed to delete {filename}: {e}")

        result = f"Deleted {len(deleted)} file(s) from '{base_url.name}'."

        if deleted:
            preview = ', '.join(deleted[:5])
            result += f"\n  Deleted   : {preview}"
            if len(deleted) > 5:
                result += f" ... and {len(deleted) - 5} more."

        if not_found:
            result += f"\n  Not found : {', '.join(not_found)}"

        if failed:
            result += f"\n  Failed    : {', '.join(failed)}"

        return result


    def handle(self, command: str) -> str:
        logger.info(f"FileSystemAgent handling: {command}")
        data   = self.parse_command(command)
        action = data.get("action", "")
        logger.debug(f"Parsed action: {data}")

        actions = {
            "create_folder":  self.create_folder,
            "delete":         self.delete,
            "delete_pattern": self.delete_pattern,
            "delete_files":   self.delete_files,    
            "rename":         self.rename,
            "move":           self.move,
            "list":           self.list,
            "find":           self.find,
            "create_file":    self.create_file,
            "create_files":   self.create_files,    
            "read_file":      self.read_file,
            "info":           self.info,
        }

        if action not in actions:
            return f"Sorry, I don't know how to do '{action}' yet."

        return actions[action](data)