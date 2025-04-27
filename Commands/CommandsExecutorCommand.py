# Importaciones necesarias de librerías
import threading
import time
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule

"""
Clase que gestiona una terminal interactiva para ejecutar comandos remotos a través de una conexión SSH (previamente 
realizada). Utiliza un shell interactivo creado anteriormente mediante la librería paramiko.
"""


class CommandsExecutorCommand:
    """
    Constructor de la clase que inicializa la terminal con el shell SSH proporcionado.
    :param ssh_shell: Canal interactivo de la sesión SSH (obtenido con invoke_shell())
    """

    def __init__(self, ssh_shell):
        self.shell = ssh_shell
        self.console = Console()
        self.keep_running = True  # Controla cuándo se debe cerrar la terminal

    """
    Método principal de la clase que ejecuta la terminal interactiva SSH.
    Permite al usuario introducir comandos y ver la salida en tiempo real.
    El bucle termina cuando se introduce 'exit' o se presiona Ctrl+C.
    """

    def run(self):
        self.console.clear()  # Limpia la consola y muestra un panel de bienvenida
        self.console.print(Panel.fit(
            Text.from_markup(
                "[bold cyan]🔧 Terminal interactiva SSH[/bold cyan]\n[i]Puedes ejecutar comandos como en una terminal real[/i]\n\n"
                "[dim]Escribe 'exit' o presiona Ctrl+C para salir[/dim]"
            ),
            title="[bold green]Modo comandos remotos[/bold green]",
            subtitle="SSH Tool",
            border_style="blue"
        ))

        # Se crea una línea visual de separación con mensaje de bienvenida
        self.console.print()
        self.console.print(Rule("[cyan]🌐 Conectado al servidor... mostrando bienvenida del sistema[/cyan]"))
        self.console.print()

        # Crea un hilo que se encarga de leer continuamente del servidor
        thread = threading.Thread(target=self.read_from_shell, daemon=True)
        thread.start()

        try:
            # Bucle principal de la terminal: espera comandos del usuario
            while self.keep_running:
                user_input = input()  # Espera entrada del usuario
                if user_input.strip().lower() == "exit":  # Termina la sesión si se escribe "exit"
                    self.keep_running = False
                    break
                self.shell.send(user_input + "\n")  # Envía el comando al servidor
        except KeyboardInterrupt:  # Si el usuario presiona Ctrl+C, también se detiene la terminal
            self.keep_running = False
        finally:
            self.console.print()  # Mensaje de despedida visual al salir
            self.console.print(Panel("[cyan]🔚 Sesión SSH finalizada[/cyan]", border_style="cyan"))

    """
    Método que lee continuamente la salida del servidor a través del shell SSH.
    Imprime en pantalla todo lo que llegue como respuesta a los comandos ejecutados.
    Se ejecuta en un hilo separado para no bloquear la entrada del usuario.
    """

    def read_from_shell(self):
        while self.keep_running:
            if self.shell.recv_ready():  # Comprueba si hay datos disponibles para leer
                """
                Lee lo que responde el servidor
                (Lee hasta 1024 bytes y convierte los bytes recibidos a una cadena de texto legible.
                Si hay caracteres que no se pueden decodificar correctamente los ignora).
                """
                output = self.shell.recv(1024).decode("utf-8", errors="ignore")  # Guarda la respuesta para mostrarla
                print(output, end='', flush=True)  # Imprime la salida directamente en consola
            time.sleep(0.1)  # Pequeña pausa para evitar uso excesivo de CPU
