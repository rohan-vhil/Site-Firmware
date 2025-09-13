# data_viewer.py
# Description: A script to continuously fetch and display data from the dummy receiver.
# Installation: You need to install 'requests' and 'rich' -> pip install requests rich

import requests
import time
import os
from rich.console import Console
from rich.syntax import Syntax
import json

console = Console()
VIEWER_URL = "http://127.0.0.1:5000/api/latest"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    console.print("[bold cyan]Live Data Viewer Started[/bold cyan]")
    console.print(f"Polling data from [bold yellow]{VIEWER_URL}[/bold yellow] every 5 seconds.")
    console.print("Press Ctrl+C to exit.")
    
    try:
        while True:
            try:
                response = requests.get(VIEWER_URL)
                response.raise_for_status()
                data = response.json()
                
                clear_screen()
                
                formatted_json = json.dumps(data, indent=4)
                syntax = Syntax(formatted_json, "json", theme="monokai", line_numbers=True)
                
                console.print(f"[bold green]Last Update:[/bold green] {data.get('last_updated', 'N/A')}")
                console.print(syntax)

            except requests.exceptions.ConnectionError:
                clear_screen()
                console.print("[bold red]Error: Connection failed.[/bold red] Is the dummy_receiver.py server running?")
            except Exception as e:
                console.print(f"[bold red]An error occurred: {e}[/bold red]")

            time.sleep(5)
            
    except KeyboardInterrupt:
        console.print("\n[bold cyan]Viewer stopped by user.[/bold cyan]")

if __name__ == "__main__":
    main()
