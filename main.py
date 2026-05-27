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
from core.rag import RAGEngine
from agents.rag_agent import RAGAgent
from agents.filesystem_agent import FileSystemAgent
from agents.word_agent import WordAgent
from core.router import Router
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

def processCommand(user_input: str,llm: LLMCore,memory: ConversationMemory,router: Router,fs_agent: FileSystemAgent,word_agent:WordAgent,rag_agent:RAGAgent,speech_output: SpeechOutput):
    agent = router.route(user_input)
    console.print(f"[dim]→ Routing to: {agent}[/dim]")

    if agent=="filesystem":
        console.print(f"[dim]{ASSISTANT_NAME} is working on it...[/dim]")
        result = fs_agent.safe_run(user_input)
        console.print(f"\n[bold cyan]{ASSISTANT_NAME}:[/bold cyan] {result}\n")
        speech_output.speak(result)
    elif agent == "word":
        console.print(f"[dim]{ASSISTANT_NAME} is working on your document...[/dim]")
        result = word_agent.safe_run(user_input)
        console.print(f"\n[bold cyan]{ASSISTANT_NAME}:[/bold cyan] {result}\n")
        speech_output.speak(result)
    elif agent == "rag":
        console.print(f"[dim]{ASSISTANT_NAME} is searching your knowledge base...[/dim]")
        result = rag_agent.safe_run(user_input)
        console.print(f"\n[bold cyan]{ASSISTANT_NAME}:[/bold cyan] {result}\n")
        speech_output.speak(result)
    else:
        history = memory.getHistory()
        memory.add_user_message(user_input)
        console.print(f"[dim]{ASSISTANT_NAME} is thinking...[/dim]")
        response = llm.chat(user_input, history)
        memory.add_agent_message(response)
        console.print(f"\n[bold cyan]{ASSISTANT_NAME}:[/bold cyan] {response}\n")
        speech_output.speak(response)

def handleSpecialCommands(userInput:str,mode:str,memory:ConversationMemory,speech_input:SpeechInput,wake_detector:WakeWordDetector,speech_output:SpeechOutput)->tuple[bool,str,SpeechInput]:
    cmd = userInput.lower().strip()
    if cmd in ["quit","exit","bye"]:
        byeText = "Tata Bye Bye See You!"
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

def goForWakeWord(wakeword:WakeWordDetector,speech_output: SpeechOutput):
    console.print(f"[dim] Listening for wake word: 'Hey Daddy'...[/dim]")
    while True:
        detected = wakeword.listen()
        if detected:
            break
    
    console.print(f"\n[bold green] Wake word detected![/bold green]")
    speech_output.speak("Daddy is here. Tell me?")



def runWakeWordMode(llm:LLMCore,speech_input:SpeechInput,speech_output:SpeechOutput,memory:ConversationMemory,wakeword:WakeWordDetector,router:Router,fs_agent:FileSystemAgent,word_agent: WordAgent, rag_agent:RAGAgent):
    goForWakeWord(wakeword,speech_output)
    rest_count = 0
    while True:
        console.print("[dim]Waiting for your command![/dim]")
        user_input = speech_input.listen(record_sec=10)

        if not user_input:
            rest_count+=1
            if rest_count==3:
                rest_count=0
                speech_output.speak("Daddy is going to take a nap!")
                goForWakeWord(wakeword,speech_output)
                continue
            console.print("[yellow]Didn't catch that. Try again.[/yellow]")
            speech_output.speak("Sorry, I didn't catch that.")
            console.print(f"[dim]Listening for wake word: 'Hey Daddy'...[/dim]")
            continue

        console.print(f"[bold green]You said:[/bold green] {user_input}")

        is_special, _, _ = handleSpecialCommands(user_input, "wake", memory,speech_input, wakeword, speech_output)

        if is_special:
            console.print(f"[dim]Listening for wake word: 'Hey Daddy'...[/dim]")
            continue

        processCommand(user_input, llm, memory, router, fs_agent, word_agent, rag_agent,speech_output)

        console.print(f"[dim]Listening for wake word: 'Hey Daddy'...[/dim]")

def runTextMode(llm:LLMCore,speech_input:SpeechInput,speech_output:SpeechOutput,memory:ConversationMemory,wakeword:WakeWordDetector,router:Router,fs_agent:FileSystemAgent,word_agent: WordAgent, rag_agent:RAGAgent):
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

        processCommand(user_input, llm, memory, router, fs_agent, word_agent, rag_agent,speech_output)

def runVoiceMode(llm:LLMCore,speech_input:SpeechInput,speech_output:SpeechOutput,memory:ConversationMemory,wakeword:WakeWordDetector,router:Router,fs_agent:FileSystemAgent,word_agent: WordAgent, rag_agent:RAGAgent):
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

        processCommand(user_input, llm, memory, router, fs_agent, word_agent, rag_agent,speech_output)



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
    fs_agent = FileSystemAgent()
    word_agent = WordAgent()
    router = Router()
    rag_engine = RAGEngine()
    rag_agent  = RAGAgent(rag_engine)
    speech_input = None

    if mode in ["voice", "wake"]:
        speech_input = SpeechInput()

    console.print(f"[green]✓ {ASSISTANT_NAME} is ready![/green]\n")

    greetings = {
        "text":  [f" ..Baby. {ASSISTANT_NAME}'s home..",f"Baby {ASSISTANT_NAME}'s home"],
        "voice": [f" ..Baby. {ASSISTANT_NAME}'s home..",f"Baby {ASSISTANT_NAME}'s home"],
        "wake":  [f" ..Baby. {ASSISTANT_NAME}'s home..",f"Baby {ASSISTANT_NAME}'s home"],
    }
    console.print(f"[cyan]{greetings[mode][1]}[/cyan]\n")
    speech_output.speak(greetings[mode][0])

    try:
        if mode == "text":
            runTextMode(llm,speech_input, speech_output, memory, wakeword,router,fs_agent,word_agent,rag_agent)
        elif mode == "voice":
            runVoiceMode(llm, speech_input, speech_output, memory, wakeword,router,fs_agent,word_agent,rag_agent)
        elif mode == "wake":
            runWakeWordMode(llm, speech_input, speech_output, memory, wakeword,router,fs_agent,word_agent,rag_agent)
    except KeyboardInterrupt:
        console.print(f"\n[cyan]Daddy wants to leave urgently! Take care bye bye![/cyan]")

if __name__=="__main__":
    main()