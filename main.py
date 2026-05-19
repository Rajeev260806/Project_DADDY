from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from loguru import logger
import sys
import os

from core.llm import LLMCore
from core.memory import ConversationMemory
from config import ASSISTANT_NAME

logger.remove()
logger.add("logs/assistant.log",rotation="1MB",level="DEBUG")
logger.add(sys.stderr,level="WARNING")

console = Console()

def print_banner():
    console.print(Panel(
        f"[bold cyan]{ASSISTANT_NAME} - Personal AI Assistant[/bold cyan]\n"
        f"[dim]Powered by Llama 3.2 | Running 100% locally[/dim]\n"
        f"[dim]Type your message and press Enter. Type 'quit' to exit. Type 'clear' to reset memory.[/dim]",
        border_style="bold cyan"
    ))

def main():
    print_banner()

    console.print("[yellow]Starting up DADDY...[/yellow]")
    llm = LLMCore()
    memory = ConversationMemory()
    console.print(f"[green]✓ {ASSISTANT_NAME} is ready! Start chatting.[/green]\n")

    while True:
        try:
            user_input = console.input("[bold green]You:[/bold green] ").strip()

            if not user_input:
                continue
            if user_input.lower() in ["quit", "exit", "bye"]:
                console.print(f"[cyan]{ASSISTANT_NAME}: Tata Bye Bye See You.[/cyan]")
                break
            if user_input.lower() == "clear":
                memory.clearMemory()
                console.print(f"[yellow]Conversation memory cleared.[/yellow]\n")
                continue
            if user_input.lower() == "history":
                history = memory.getHistory()
                if not history:
                    console.print("[dim]No history yet.[/dim]\n")
                else:
                    for msg in history:
                        role = "You" if msg["role"] == "user" else ASSISTANT_NAME
                        console.print(f"[dim]{role}: {msg['content'][:100]}...[/dim]")
                console.print()
                continue

            history = memory.getHistory()
            memory.add_user_message(user_input)
            console.print(f"[dim]{ASSISTANT_NAME} is thinking...[/dim]")
            response = llm.chat(user_input,history)
            memory.add_agent_message(response)
            console.print(f"\n[bold cyan]{ASSISTANT_NAME}:[/bold cyan] {response}\n")

        except KeyboardInterrupt:
            console.print(f"\n[cyan]{ASSISTANT_NAME}: Goodbye![/cyan]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            logger.error(f"Main loop error: {e}")

if __name__=="__main__":
    main()