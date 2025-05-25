# Importaciones necesarias de librerías
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

"""
Clase que gestiona la recopilación de datos de conexión SSH desde el usuario.
Solicita el host, nombre de usuario, puerto y método de autenticación de forma interactiva.
También proporciona mensajes de advertencia y guarda temporalmente los datos introducidos
para evitar que el usuario los vuelva a escribir durante la misma sesión.
"""


class ConnectionConfig:

    # Variables de clase para recordar la última configuración ingresada por el usuario
    host_saved = ""
    username_saved = ""
    port_saved = ""

    """
    Método estático que solicita los datos de conexión SSH al usuario.
    Muestra un mensaje informativo si elige métodos de autenticación que requieren clave.
    Almacena los valores en variables de clase para reutilizarlos si ya fueron introducidos previamente.
    """

    @staticmethod
    def ask_user_connection_data():
        console = Console()
        console.print("\n[bold green]🌐 Iniciar conexión SSH[/bold green]")

        # Muestra una advertencia cuando se usan métodos de autenticación que requieren clave pública
        console.print(Panel.fit(
            "[yellow]⚠ Para autenticación por clave, agente o certificado, debe haber generado previamente un par de claves SSH (pública y privada) "
            "y debe haber copiado la clave pública al servidor remoto.\n\n"
            "Esto puede hacerlo desde la opción 2 del menú principal ('Configurar claves SSH').[/yellow]",
            title="Advertencia importante",
            border_style="red"
        ))

        # Si el usuario ya introdujo los datos previamente, los reutiliza
        if ConnectionConfig.host_saved and ConnectionConfig.username_saved and ConnectionConfig.port_saved:
            host = ConnectionConfig.host_saved
            username = ConnectionConfig.username_saved
            port = ConnectionConfig.port_saved

            console.print(f"\n[bold green]Host: {host}[/bold green]")
            console.print(f"\n[bold green]Usuario: {username}[/bold green]")
            console.print(f"\n[bold green]Puerto: {port}[/bold green]")
        else:
            # Solicita los datos de conexión al usuario
            host = Prompt.ask("[💻] Host")
            username = Prompt.ask("[👤] Usuario")
            port = Prompt.ask("[🔢] Puerto", default="22")

            # Guarda los datos en variables de clase para futuras reutilizaciones
            ConnectionConfig.host_saved = host
            ConnectionConfig.username_saved = username
            ConnectionConfig.port_saved = port

        # Solicita el método de autenticación (contraseña, clave, agente, certificado)
        auth_method = Prompt.ask(
            "[ ] ¿Método de autenticación?",
            choices=["contraseña", "clave", "agente", "certificado"],
            default="contraseña"
        )

        return host, username, port, auth_method
