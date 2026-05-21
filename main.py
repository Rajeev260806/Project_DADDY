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
from core.wakeword import WakeWordDetector
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

def handleSpecialCommands(userInput:str,mode:str,memory:ConversationMemory,speech_input:SpeechInput,wake_detector:WakeWordDetector,speech_output:SpeechOutput)->tuple[bool,str,SpeechInput]:
    cmd = userInput.lower().strip()
    if cmd in ["quit","exit","bye"]:
        byeText = "Tata Tata Bye Bye!"
        console.print(f"[cyan]{ASSISTANT_NAME}: {byeText}[/cyan]")
        speech_output.speak(byeText)
        sys.exit(0)
    
    if cmd=="clear":
        memory.clearMemory()
        console.print("[yellow]Memory cleared.[/yellow]\n")
        return True, mode, speech_input
    
    if cmd=="switch" or cmd=="switch.":
        if mode == "text":
            mode = "wake"
            if speech_input is None:
                console.print("[yellow]Loading Whisper model...[/yellow]")
                speech_input = SpeechInput()
            console.print("[green]Switched to WAKE WORD mode. Say 'Hey Daddy' to activate.[/green]\n")
        elif mode == "voice":
            mode = "wake"
            console.print("[green]Switched to WAKE WORD mode. Say 'Hey Daddy' to activate.[/green]\n")
        else:
            mode = "text"
            console.print("[green]Switched to TEXT mode.[/green]\n")
        return True,mode,speech_input
    
    if cmd.startswith("threshold "):
        parts = cmd.split()
        if len(parts) == 2 and parts[1].isdigit():
            new_val = int(parts[1])
            wake_detector.adjust_threshold(new_val)
            console.print(f"[yellow]Mic threshold set to {new_val}.[/yellow]\n")
        else:
            console.print("[red]Convey as threshold <number>  e.g. threshold 400[/red]\n")
        return True, mode, speech_input
    
    if cmd == "voices":
        speech_output.list_voices()
        return True, mode, speech_input

    return False, mode, speech_input

def runWakeWordMode(llm:LLMCore,speech_input:SpeechInput,speech_output:SpeechOutput,memory:ConversationMemory,wakeword:WakeWordDetector):
    console.print(f"[dim] Listening for wake word: 'Hey Daddy'...[/dim]")
    while True:
        detected = wakeword.listen()
        if not detected:
            continue

        console.print(f"\n[bold green] Wake word detected![/bold green]")
        speech_output.speak("Yes?")

        console.print("[dim]Waiting for your command![/dim]")
        user_input = speech_input.listen(record_sec=6)

        if not user_input:
            console.print("[yellow]Didn't catch that. Try again.[/yellow]")
            speech_output.speak("Sorry, I didn't catch that.")
            console.print(f"[dim]Listening for wake word: 'Hey Daddy'...[/dim]")
            continue

        console.print(f"[bold green]You said:[/bold green] {user_input}")

        is_special, _, _ = handleSpecialCommands(user_input, "wake", memory,speech_input, wakeword, speech_output)

        if is_special:
            console.print(f"[dim]Listening for wake word: 'Hey Daddy'...[/dim]")
            continue

        history = memory.getHistory()
        memory.add_user_message(user_input)

        console.print(f"[dim]{ASSISTANT_NAME} is thinking...[/dim]")
        response = llm.chat(user_input, history)
        memory.add_agent_message(response)

        console.print(f"\n[bold cyan]{ASSISTANT_NAME}:[/bold cyan] {response}\n")
        speech_output.speak(response)

        console.print(f"[dim]Listening for wake word: 'Hey Daddy'...[/dim]")

def runTextMode(llm:LLMCore,speech_input:SpeechInput,speech_output:SpeechOutput,memory:ConversationMemory,wakeword:WakeWordDetector):
    while True:
        user_input = console.input("[bold green]You said:[/bold green] ").strip()

        if not user_input:
            continue

        is_special, _, _ = handleSpecialCommands(
            user_input, "text", memory,
            speech_input, wakeword, speech_output
        )
        if is_special:
            continue

        history = memory.getHistory()
        memory.add_user_message(user_input)

        console.print(f"[dim]{ASSISTANT_NAME} is thinking...[/dim]")
        response = llm.chat(user_input, history)
        memory.add_agent_message(response)

        console.print(f"\n[bold cyan]{ASSISTANT_NAME}:[/bold cyan] {response}\n")
        speech_output.speak(response)

def runVoiceMode(llm:LLMCore,speech_input:SpeechInput,speech_output:SpeechOutput,memory:ConversationMemory,wakeword:WakeWordDetector):
    while True:
        console.print("[dim]Press Enter to start recording...[/dim]")
        input()
        user_input = speech_input.listen()

        if not user_input:
            console.print("[yellow]Nothing detected. Try again.[/yellow]")
            continue

        console.print(f"[bold green]You said:[/bold green] {user_input}")

        is_special, _, _ = handleSpecialCommands(
            user_input, "voice", memory,
            speech_input, wakeword, speech_output
        )
        if is_special:
            continue

        history = memory.getHistory()
        memory.add_user_message(user_input)

        console.print(f"[dim]{ASSISTANT_NAME} is thinking...[/dim]")
        response = llm.chat(user_input, history)
        memory.add_agent_message(response)

        console.print(f"\n[bold cyan]{ASSISTANT_NAME}:[/bold cyan] {response}\n")
        speech_output.speak(response)



def main():

    print_banner()

    console.print("\n[bold cyan]Choose input mode:[/bold cyan]")
    console.print("  [green]1[/green] → Text mode")
    console.print("  [green]2[/green] → Voice mode")
    console.print("  [green]3[/green] → Wake word mode \n")

    choice = console.input("Enter 1, 2 or 3: ").strip()
    mode = {"1": "text", "2": "voice", "3": "wake"}.get(choice, "text")

    llm = LLMCore()
    memory = ConversationMemory()
    speech_output = SpeechOutput()
    wakeword = WakeWordDetector()
    speech_input = SpeechInput()

    if mode in ["voice", "wake"]:
        console.print("[yellow]Loading Whisper speech model...[/yellow]")
        speech_input = SpeechInput()

    console.print(f"[green]✓ {ASSISTANT_NAME} is ready![/green]\n")

    greetings = {
        "text":  f"Hello! I'm {ASSISTANT_NAME}. Type your message below.",
        "voice": f"Hello! I'm {ASSISTANT_NAME}. Press Enter when you want to speak.",
        "wake":  f"Hello! I'm {ASSISTANT_NAME}. Say Hey Daddy to wake me up."
    }
    console.print(f"[cyan]{greetings[mode]}[/cyan]\n")
    speech_output.speak(greetings[mode])

    try:
        if mode == "text":
            runTextMode(llm,speech_input, speech_output, memory, wakeword)
        elif mode == "voice":
            runVoiceMode(llm, speech_input, speech_output, memory, wakeword)
        elif mode == "wake":
            runWakeWordMode(llm, speech_input, speech_output, memory, wakeword)
    except KeyboardInterrupt:
        console.print(f"\n[cyan]{ASSISTANT_NAME}: Goodbye![/cyan]")



    # console.print("\n[bold cyan]Choose input mode:[/bold cyan]")
    # console.print("  [green]1[/green] → Text mode  (type your messages)")
    # console.print("  [green]2[/green] → Voice mode (speak your messages)\n")

    # choice = console.input("Enter 1 or 2: ").strip()
    # mode = "voice" if choice == "2" else "text"

    # console.print("[yellow]Starting up DADDY...[/yellow]")
    # llm = LLMCore()
    # memory = ConversationMemory()
    # speechOutput = SpeechOutput()

    # speechInput = None
    # if mode == "voice":
    #     console.print("[yellow]Loading Whisper speech model...[/yellow]")
    #     speechInput = SpeechInput()

    # console.print(f"[green]✓ {ASSISTANT_NAME} is ready![/green]\n")

    # if mode == "voice":
    #     greeting = f"Hey baby...., Daddy's.. home!!!"
    #     greeting2 = f"Ready ya Mamee!"
    #     speechOutput.speak(greeting)
    #     speechOutput.speak(greeting2)


    # while True:
    #     try:
    #         if mode == "voice":
    #             console.print("[dim]Press Enter to start recording...[/dim]")
    #             input()                        
    #             user_input = getInput(mode, speechInput)

    #             if not user_input:
    #                 console.print("[yellow]Nothing detected. Try again.[/yellow]")
    #                 continue

    #             console.print(f"[bold green]You said:[/bold green] {user_input}")
    #         else:
    #             user_input = getInput(mode, speechInput)

    #         if not user_input:
    #             continue
    #         if user_input.lower() in ["quit", "exit", "bye"]:
    #             byemessage = "Tata Bye Bye See You!"
    #             console.print(f"[cyan]{ASSISTANT_NAME}: {byemessage}[/cyan]")
    #             if mode=="voice":
    #                 speechOutput.speak(byemessage)
    #             break
    #         if user_input.lower() == "clear":
    #             memory.clearMemory()
    #             console.print(f"[yellow]Conversation memory cleared.[/yellow]\n")
    #             continue
    #         if user_input.lower() == "history":
    #             history = memory.getHistory()
    #             if not history:
    #                 console.print("[dim]No history yet.[/dim]\n")
    #             else:
    #                 for msg in history:
    #                     role = "You" if msg["role"] == "user" else ASSISTANT_NAME
    #                     console.print(f"[dim]{role}: {msg['content'][:100]}...[/dim]")
    #             console.print()
    #             continue
    #         if user_input.lower() == "switch":
    #             if mode == "text":
    #                 mode = "voice"
    #                 if speechInput is None:
    #                     speechInput = SpeechInput()
    #                 console.print("[green]Switched to VOICE mode.[/green]\n")
    #             else:
    #                 mode = "text"
    #                 console.print("[green]Switched to TEXT mode.[/green]\n")
    #             continue

    #         if user_input.lower() == "voices":
    #             speechOutput.list_voices()
    #             continue

    #         history = memory.getHistory()
    #         memory.add_user_message(user_input)
    #         console.print(f"[dim]{ASSISTANT_NAME} is thinking...[/dim]")
    #         response = llm.chat(user_input,history)
    #         memory.add_agent_message(response)
    #         console.print(f"\n[bold cyan]{ASSISTANT_NAME}:[/bold cyan] {response}\n")
    #         if mode == "voice":
    #             speechOutput.speak(response)

    #     except KeyboardInterrupt:
    #         console.print(f"\n[cyan]{ASSISTANT_NAME}: Tata Bye Bye See You![/cyan]")
    #         break
    #     except Exception as e:
    #         console.print(f"[red]Error: {e}[/red]")
    #         logger.error(f"Main loop error: {e}")

if __name__=="__main__":
    main()