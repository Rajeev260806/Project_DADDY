from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from loguru import logger
import sys
import os

from core.llm import LLMCore
from core.memory import ConversationMemory
from core.speech_input import SpeechInput
from core.speech_output import SpeechOutput
from config import ASSISTANT_NAME

logger.remove()
logger.add("logs/assistant.log",rotation="1MB",level="DEBUG")
logger.add(sys.stderr,level="WARNING")

console = Console()

def print_banner():
    console.print(Panel(
        f"[bold cyan]{ASSISTANT_NAME} - Personal AI Assistant[/bold cyan]\n"
        f"[dim]Powered by Llama 3.2 | Running 100% locally[/dim]\n"
        f"[dim]Commands: 'switch' = toggle voice/text | 'clear' = reset memory | 'quit' = exit[/dim]",
        border_style="bold cyan"
    ))

def getInput(mode: str,speechInput: SpeechInput)->str:
    if mode=="voice":
        return speechInput.listen()
    else:
        return console.input("[bold green]You:[/bold green] ").strip()

def main():

    print_banner()

    console.print("\n[bold cyan]Choose input mode:[/bold cyan]")
    console.print("  [green]1[/green] → Text mode  (type your messages)")
    console.print("  [green]2[/green] → Voice mode (speak your messages)\n")

    choice = console.input("Enter 1 or 2: ").strip()
    mode = "voice" if choice == "2" else "text"

    console.print("[yellow]Starting up DADDY...[/yellow]")
    llm = LLMCore()
    memory = ConversationMemory()
    speechOutput = SpeechOutput()

    speechInput = None
    if mode == "voice":
        console.print("[yellow]Loading Whisper speech model...[/yellow]")
        speechInput = SpeechInput()

    console.print(f"[green]✓ {ASSISTANT_NAME} is ready![/green]\n")

    if mode == "voice":
        greeting = f"Hey baby...., Daddy's.. home!!!"
        greeting2 = f"Ready ya Mamee!"
        speechOutput.speak(greeting)
        speechOutput.speak(greeting2)


    while True:
        try:
            if mode == "voice":
                console.print("[dim]Press Enter to start recording...[/dim]")
                input()                        
                user_input = getInput(mode, speechInput)

                if not user_input:
                    console.print("[yellow]Nothing detected. Try again.[/yellow]")
                    continue

                console.print(f"[bold green]You said:[/bold green] {user_input}")
            else:
                user_input = getInput(mode, speechInput)

            if not user_input:
                continue
            if user_input.lower() in ["quit", "exit", "bye"]:
                byemessage = "Tata Bye Bye See You!"
                console.print(f"[cyan]{ASSISTANT_NAME}: {byemessage}[/cyan]")
                if mode=="voice":
                    speechOutput.speak(byemessage)
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
            if user_input.lower() == "switch":
                if mode == "text":
                    mode = "voice"
                    if speechInput is None:
                        speechInput = SpeechInput()
                    console.print("[green]Switched to VOICE mode.[/green]\n")
                else:
                    mode = "text"
                    console.print("[green]Switched to TEXT mode.[/green]\n")
                continue

            if user_input.lower() == "voices":
                speechOutput.list_voices()
                continue

            history = memory.getHistory()
            memory.add_user_message(user_input)
            console.print(f"[dim]{ASSISTANT_NAME} is thinking...[/dim]")
            response = llm.chat(user_input,history)
            memory.add_agent_message(response)
            console.print(f"\n[bold cyan]{ASSISTANT_NAME}:[/bold cyan] {response}\n")
            if mode == "voice":
                speechOutput.speak(response)

        except KeyboardInterrupt:
            console.print(f"\n[cyan]{ASSISTANT_NAME}: Tata Bye Bye See You![/cyan]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            logger.error(f"Main loop error: {e}")

if __name__=="__main__":
    main()