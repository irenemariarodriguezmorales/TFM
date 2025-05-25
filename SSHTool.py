# Importaciones necesarias de librerías
import sys
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
# Importaciones necesarias de otras clases
from Connection.SSHConnection import SSHConnection
from Commands.KeyManagerCommand import KeyManagerCommand

'''
Es la clase principal de la herramienta. En esta clase comienza el flujo principal (ver main)
Muestra el menú principal y llama a las clases correspondientes dependiendo de la opción
que elija el usuario (conexión a un servidor y gestión de claves SSH).
'''


def show_help():
    help_text = """
🔐 SSH Tool - Ayuda de uso

Uso:
  python3 SSHTool.py           Inicia la herramienta con el menú principal
  python3 SSHTool.py --help    Muestra este mensaje de ayuda
  python3 SSHTool.py -h        Muestra este mensaje de ayuda

Funcionalidades:
  1. Conectar a un servidor SSH
     → Establece una conexión SSH mediante contraseña, clave, agente o certificado.

  2. Configurar claves SSH
     → Opciones para generar claves, copiarlas al servidor y ver claves autorizadas.

  Tras realizar realizar una conexión SSH a un servidor podrá realizar las siguiente acciones:
  
  1. Transferir archivos
     → Envía o descarga archivos usando SFTP o SCP.

  2. Ejecutar comandos remotos
     → Acceso a terminal SSH interactiva con salida en tiempo real.

  3. Salir
     → Cierra la conexión y finaliza el programa.

Consejo:
  Use primero la opción de "Configurar claves SSH" para evitar errores si desea autenticación por clave, agente y/o certificado.

"""
    print(help_text)
    sys.exit(0)


class SSHTool:
    """
    Este es el constructor.
    Se incializa la consola Rich para tener una salida elegante, se inicializa running a True (para que se muestre
    el menú principal, dejará de mostrarse cuando el usuario decida salir de la herramienta),
    y se declara que no existe ninguna conexión establecida desde el inicio.
    """

    def __init__(self):
        self.console = Console()
        self.running = True
        self.ssh_connection = None

    """
    Muestra el menú principal de la herramienta y gestiona la elección de opciones.
    """

    def display_main_menu(self):
        self.console.print(Panel.fit("🔐 [bold blue]SSH Tool - Herramienta para gestión SSH[/bold blue]"))

        menu_options = {
            "1": ("Conectar a un servidor SSH", self.connect_server),
            "2": ("Configurar claves SSH", self.manage_keys),
            "3": ("Salir", self.exit_tool)
        }

        """
        Mientras self.running sea True, la herramienta seguirá mostrando el menú principal.
        Recorre el diccionario menu_options (que contiene las 3 opciones disponibles) 
        y las muestra con su número (key) y descripción (desc).
        """
        while self.running:
            self.console.print("\n[bold]Menú Principal:[/bold]")
            for key, (desc, _) in menu_options.items():
                self.console.print(f"[cyan]{key}[/cyan]. {desc}")

            # Pregunta al usuario qué desea hacer y según la opción se ejecuta la función correspondiente
            choice = Prompt.ask("\nSeleccione una opción", choices=list(menu_options.keys()))
            _, action = menu_options[choice]
            action()

    """
    Método que inicia el proceso de conexión SSH preguntando por host, usuario y puerto (método from_user_input()).
    Si la conexión es exitosa, delega en SSHConnection para mostrar su menú propio (método show_session_menu()).
    """

    def connect_server(self):
        self.console.print("\n[bold]Conectar a un servidor SSH[/bold]", style="green")
        self.ssh_connection = SSHConnection.create_connection()
        if self.ssh_connection:
            self.ssh_connection.show_session_menu()
        else:
            self.console.print(
                "[bold red]\n✖ No se pudo establecer la conexión SSH. Volviendo al menú principal...[/bold red]")

    """
    Método que permite gestionar claves SSH locales y remotas:
    - Generar claves locales
    - Copiar clave pública al servidor
    - Ver claves existentes en el servidor
    Se llama a la clase KeyManagerCommand.
    """

    def manage_keys(self):
        ssh_client = self.ssh_connection.get_client() if self.ssh_connection else None
        manager = KeyManagerCommand(ssh_client)
        manager.run()

    """
    Método encargado de finalizar la ejecución del programa y muestra un mensaje de despedida.
    """

    def exit_tool(self):
        self.console.print("\n👋 Saliendo de SSH Tool...", style="bold red")
        self.running = False


# Punto donde comienza la ejecución de la herramienta
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--help", "--h"):
        show_help()
    try:
        tool = SSHTool()
        tool.display_main_menu()
    except KeyboardInterrupt:
        print("\nOperación cancelada por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)
