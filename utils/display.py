"""Utilidades de visualización con Rich."""

import sys
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

console = Console(force_terminal=True)


def supports_unicode() -> bool:
    """Check if the terminal supports UTF-8 encoding."""
    return sys.stdout.encoding.lower().startswith("utf")


def print_user(message: str) -> None:
    """Imprime mensaje del usuario."""
    console.print(f"👤 [bold cyan]Usuario:[/bold cyan] {message}")


def print_principal(message: str, show_model: bool = True) -> None:
    """Imprime respuesta del agente principal."""
    model_tag = "[dim](qwen-orchestrator)[/dim]" if show_model else ""
    console.print(f"\n🤖 [green]Agente Principal[/green] {model_tag}")

    if "```" in message:
        _print_with_code(message)
    else:
        console.print(f"[green]{message}[/green]")


def print_executor(message: str, show_model: bool = True) -> None:
    """Imprime respuesta del agente ejecutor."""
    model_tag = "[dim](qwen-validator)[/dim]" if show_model else ""
    console.print(f"\n⚡ [yellow]Agente Ejecutor[/yellow] {model_tag}")
    console.print(f"[yellow]{message}[/yellow]")


def print_rag(message: str, source: str = "gemini") -> None:
    """Imprime respuesta de la API."""
    console.print("\n📚 [blue]Respuesta de la API[/blue]")
    console.print(f"[blue]{message}[/blue]")


def print_cache(message: str) -> None:
    """Imprime respuesta desde cache."""
    console.print("\n💾 [magenta]Cache (SQLite)[/magenta]")
    console.print(f"[magenta]{message}[/magenta]")


def print_code(code: str, language: str = "python") -> None:
    """Imprime código con syntax highlighting."""
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    console.print(syntax)


def print_error(message: str) -> None:
    """Imprime mensaje de error."""
    console.print(f"[red bold]❌ Error:[/red bold] [red]{message}[/red]")


def print_success(message: str) -> None:
    """Imprime mensaje de éxito."""
    console.print(f"[green bold]✅ {message}[/green bold]")


def print_info(message: str) -> None:
    """Imprime mensaje informativo."""
    console.print(f"[blue]ℹ️  {message}[/blue]")


def print_warning(message: str) -> None:
    """Imprime advertencia."""
    console.print(f"[yellow]⚠️  {message}[/yellow]")


def print_header() -> None:
    """Imprime header del sistema."""
    console.print("\n" + "=" * 70)
    console.print(
        "[bold cyan]🤖 Sistema de Agentes Inteligentes[/bold cyan]",
        justify="center",
    )
    console.print("[dim]qwen-orchestrator + qwen-validator[/dim]", justify="center")
    console.print("=" * 70 + "\n")


def print_stats(stats: dict[str, Any]) -> None:
    """Imprime estadísticas del sistema."""
    table = Table(title="📊 Estadísticas del Sistema", show_header=True)

    table.add_column("Métrica", style="cyan", width=30)
    table.add_column("Valor", style="green", justify="right")

    storage = stats.get("storage", {})
    table.add_row("Total Interacciones", str(storage.get("total_interactions", 0)))
    table.add_row("Patrones Aprendidos", str(storage.get("learned_patterns", 0)))
    table.add_row("Cache Hits", str(storage.get("cache_hits", 0)))
    table.add_row("Uso de RAG", str(storage.get("rag_usage", 0)))
    table.add_row("Tasa de Éxito", f"{storage.get('success_rate', 0)}%")

    console.print("\n")
    console.print(table)


def print_validation(validation: dict[str, Any]) -> None:
    """Imprime resultado de validación."""
    is_valid = validation.get("is_valid", False)

    if is_valid:
        console.print("\n[green bold]✅ Validación: APROBADA[/green bold]")
    else:
        console.print("\n[yellow bold]⚠️  Validación: REQUIERE AJUSTES[/yellow bold]")

    feedback = validation.get("feedback", "")
    if feedback:
        console.print(f"[dim]{feedback}[/dim]")

    suggestions = validation.get("suggestions", [])
    if suggestions:
        console.print("\n[cyan]Sugerencias:[/cyan]")
        for i, suggestion in enumerate(suggestions, 1):
            console.print(f"  {i}. {suggestion}")


def print_patterns(patterns: list[str]) -> None:
    """Imprime patrones detectados."""
    if patterns:
        console.print(f"\n[dim]🔍 Patrones detectados: {', '.join(patterns)}[/dim]")


def _print_with_code(message: str) -> None:
    """Imprime mensaje que contiene bloques de código."""
    parts = message.split("```")

    for i, part in enumerate(parts):
        if i % 2 == 0:
            # Texto normal
            if part.strip():
                console.print(f"[green]{part}[/green]")
        else:
            # Bloque de código
            lines = part.split("\n")
            language = lines[0].strip() if lines else "python"
            code = "\n".join(lines[1:]) if len(lines) > 1 else part

            if code.strip():
                print_code(code.strip(), language or "python")


def print_help() -> None:
    """Imprime ayuda del sistema."""
    help_panel = Panel(
        """[cyan bold]Comandos Disponibles:[/cyan bold]

[yellow]/stats[/yellow]     - Ver estadísticas del sistema
[yellow]/patterns[/yellow]  - Ver patrones aprendidos
[yellow]/clear[/yellow]     - Limpiar pantalla
[yellow]/help[/yellow]      - Mostrar esta ayuda
[yellow]/exit[/yellow]      - Salir del sistema

[cyan bold]Funcionamiento:[/cyan bold]

• [green]Agente Principal (qwen-orchestrator)[/green]: Analiza y genera respuestas
• [yellow]Agente Ejecutor (qwen-validator)[/yellow]: Valida código
• [blue]RAG (Gemini + DeepSeek)[/blue]: Consulta cuando hay baja confianza
• [magenta]Cache (SQLite)[/magenta]: Respuestas instantáneas de patrones aprendidos

[dim]El sistema aprende de tus patrones de backend y reduce consultas a RAG.[/dim]""",
        title="🤖 Ayuda del Sistema",
        border_style="cyan",
    )
    console.print(help_panel)


def clear_screen() -> None:
    """Limpia la pantalla."""
    console.clear()
