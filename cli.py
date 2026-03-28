import click
import requests
import json
import os
import sys
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel

console = Console()

# Configuración por defecto
DEFAULT_URL = "http://localhost:8000"

def get_config():
    url = os.getenv("ECSPRESSO_URL", DEFAULT_URL).rstrip("/")
    api_key = os.getenv("ECSPRESSO_API_KEY")
    if not api_key:
        console.print("[bold red]Error:[/] Debes configurar la variable de entorno [cyan]ECSPRESSO_API_KEY[/]")
        sys.exit(1)
    return url, api_key

@click.group()
def cli():
    """ecspresso CLI - Gestión centralizada de ECS Task Definitions"""
    pass

@cli.group()
def td():
    """Comandos para Task Definitions"""
    pass

@td.command(name="get")
@click.option("--app", required=True, help="Nombre de la aplicación")
@click.option("--env", required=True, help="Entorno (development, staging, production)")
@click.option("--output", "-o", help="Archivo de salida (opcional)")
def get_td(app, env, output):
    """Obtiene la Task Definition generada para una app y entorno"""
    url, api_key = get_config()
    endpoint = f"{url}/api/v1/apps/{app}/td?env={env}"
    
    try:
        response = requests.get(endpoint, headers={"X-API-Key": api_key})
        response.raise_for_status()
        data = response.json()
        
        formatted_json = json.dumps(data, indent=2)
        if output:
            with open(output, 'w') as f:
                f.write(formatted_json)
            console.print(f"[bold green]✅ Task Definition guardada en {output}[/]")
        else:
            syntax = Syntax(formatted_json, "json", theme="monokai", line_numbers=True)
            console.print(Panel(syntax, title="Task Definition", expand=False))
            
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]❌ Error al obtener TD:[/] {e}")
        if hasattr(e.response, 'text'):
            console.print(f"[bold yellow]Detalle:[/] {e.response.text}")
        sys.exit(1)

@cli.command()
@click.option("--app", required=True, help="Nombre de la aplicación")
@click.option("--env", required=True, help="Entorno")
@click.option("--key", required=True, help="Key de la variable")
@click.option("--value", required=True, help="Valor de la variable")
def set_var(app, env, key, value):
    """Crea o actualiza una variable de entorno"""
    url, api_key = get_config()
    endpoint = f"{url}/api/v1/variables"
    payload = {
        "app_name": app,
        "environment": env,
        "key": key,
        "value": value
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers={"X-API-Key": api_key})
        response.raise_for_status()
        console.print(f"[bold green]✅ Variable '{key}' actualizada exitosamente.[/]")
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]❌ Error al guardar variable:[/] {e}")
        if hasattr(e.response, 'text'):
            console.print(f"[bold yellow]Detalle:[/] {e.response.text}")
        sys.exit(1)

@cli.command()
@click.option("--app", required=True, help="Nombre de la aplicación")
@click.option("--env", required=True, help="Entorno")
@click.option("--key", required=True, help="Key del secreto")
@click.option("--value", required=True, help="Valor real del secreto (se subirá a AWS SSM)")
def set_secret(app, env, key, value):
    """Crea o actualiza un secreto en AWS SSM"""
    url, api_key = get_config()
    endpoint = f"{url}/api/v1/secrets"
    payload = {
        "app_name": app,
        "environment": env,
        "key": key,
        "value": value
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers={"X-API-Key": api_key})
        response.raise_for_status()
        data = response.json()
        console.print(f"[bold green]✅ Secreto '{key}' sincronizado con AWS SSM.[/]")
        console.print(f"[cyan]🔗 ARN:[/] {data.get('arn')}")
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]❌ Error al guardar secreto:[/] {e}")
        if hasattr(e.response, 'text'):
            console.print(f"[bold yellow]Detalle:[/] {e.response.text}")
        sys.exit(1)

if __name__ == "__main__":
    cli()
