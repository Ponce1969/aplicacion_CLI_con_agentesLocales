"""CLI principal del sistema de agentes."""

import sys
from typing import NoReturn

from rich.prompt import Prompt

from core.orchestrator import Orchestrator
from utils.display import (
    clear_screen,
    console,
    print_cache,
    print_error,
    print_header,
    print_help,
    print_info,
    print_patterns,
    print_principal,
    print_rag,
    print_stats,
    print_success,
    print_user,
    print_validation,
    print_warning,
)


class AgentCLI:
    """CLI interactivo para el sistema de agentes."""

    def __init__(self) -> None:
        self.orchestrator = Orchestrator()
        self.running = True

    def run(self, initial_query: str | None = None) -> None:
        """
        Ejecuta el CLI interactivo.

        Args:
            initial_query: Si se proporciona, procesa esta consulta y sale.
        """
        print_header()
        self._check_system_status()

        # Modo no interactivo (single-shot)
        if initial_query:
            self._process_query(initial_query)
            return

        # Modo interactivo
        print_help()

        while self.running:
            try:
                query = Prompt.ask("\n[bold cyan]💬 Tu consulta[/bold cyan]")

                if not query.strip():
                    continue

                if self._handle_command(query):
                    continue

                self._process_query(query)

            except KeyboardInterrupt:
                self._exit()
            except Exception as e:
                print_error(f"Error inesperado: {e}")

    def _check_system_status(self) -> None:
        """Verifica el estado del sistema."""
        print_info("Verificando sistema...")

        if not self.orchestrator.principal.is_available():
            print_error("Ollama no está disponible")
            print_warning("Ejecuta: ollama serve")
            sys.exit(1)

        if not self.orchestrator.executor.is_available():
            print_warning("Agente ejecutor no disponible")

        if not self.orchestrator.rag.is_available():
            print_warning("RAG remoto no disponible (modo offline)")

        print_success("Sistema listo")

    def _handle_command(self, query: str) -> bool:
        """Maneja comandos especiales."""
        if not query.startswith("/"):
            return False

        command = query.lower().strip()

        commands = {
            "/exit": self._exit,
            "/help": lambda: print_help(),
            "/stats": lambda: print_stats(self.orchestrator.get_stats()),
            "/patterns": self._show_patterns,
            "/clear": self._clear_and_header
        }

        handler = commands.get(command)
        if handler:
            handler()
            return True

        print_warning(f"Comando desconocido: {command}")
        print_info("Usa /help para ver comandos disponibles")
        return True

    def _clear_and_header(self) -> None:
        """Limpia pantalla y muestra header."""
        clear_screen()
        print_header()

    def _process_query(self, query: str) -> None:
        """Procesa una consulta del usuario."""
        print_user(query)

        with console.status("[cyan]Procesando...[/cyan]", spinner="dots"):
            result = self.orchestrator.process(query)

        source = result.get("source", "unknown")
        response = result.get("response", "")
        patterns = result.get("patterns", [])
        validation = result.get("validation")
        execution_time = result.get("execution_time", 0)

        if patterns:
            print_patterns(patterns)

        if source == "cache":
            print_cache(response)
        elif source == "rag_gemini":
            print_rag(response, "gemini")
        elif source == "rag_kimi":
            print_rag(response, "kimi")
        elif source == "principal":
            print_principal(response)
        else:
            print_principal(response)

        if validation:
            print_validation(validation)

        print_info(f"Tiempo: {execution_time:.2f}s | Fuente: {source}")

    def _show_patterns(self) -> None:
        """Muestra patrones aprendidos."""
        patterns = self.orchestrator.storage.get_frequent_patterns()

        if not patterns:
            print_info("No hay patrones aprendidos aún")
            return

        print_info(f"Mostrando {len(patterns)} patrones aprendidos:")

        for i, pattern in enumerate(patterns[:10], 1):
            console.print(
                f"\n[cyan]{i}. {pattern['type']}[/cyan] "
                f"[dim]({pattern['usage_count']} usos)[/dim]"
            )
            console.print(f"[dim]{pattern['template'][:150]}...[/dim]")

    def _exit(self) -> NoReturn:
        """Sale del sistema."""
        print_info("\nCerrando sistema...")
        self.orchestrator.close()
        print_success("¡Hasta luego! 👋")
        sys.exit(0)


def main() -> None:
    """Entry point del CLI."""
    try:
        cli = AgentCLI()
        cli.run()
    except Exception as e:
        print_error(f"Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
