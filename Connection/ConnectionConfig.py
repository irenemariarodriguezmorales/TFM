from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt


class ConnectionConfig:

    @staticmethod
    def ask_user_connection_data():
        console = Console()
        console.print("\n[bold green]🌐 Iniciar conexión SSH[/bold green]")

        # ⚠ Panel de advertencia si elige métodos que requieren clave
        console.print(Panel.fit(
            "[yellow]⚠ Para autenticación por clave, agente o certificado, debe haber generado previamente un par de claves SSH (pública y privada) "
            "y debe haber copiado la clave pública al servidor remoto.\n\n"
            "Esto puede hacerlo desde la opción 2 del menú principal ('Configurar claves SSH').[/yellow]",
            title="Advertencia importante",
            border_style="red"
        ))

        host = Prompt.ask("[💻] Host")
        username = Prompt.ask("[👤] Usuario")
        port = Prompt.ask("[🔢] Puerto", default="22")

        auth_method = Prompt.ask(
            "[ ] ¿Método de autenticación?",
            choices=["contraseña", "clave", "agente", "certificado"],
            default="contraseña"
        )

        return host, username, port, auth_method
