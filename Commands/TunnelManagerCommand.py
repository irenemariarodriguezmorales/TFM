# Importaciones necesarias de librerías
import subprocess
# Importaciones necesarias de las clases
from rich.console import Console
from rich.prompt import Prompt
from Connection.Tunnel import Tunnel

"""
Clase que permite al usuario gestionar túneles SSH.
Proporciona un menú interactivo para crear túneles locales o remotos. También permite visualizar
los túneles activos actualmente en el sistema.

Utiliza la clase Tunnel para crear los túneles y utiliza el cliente SSH activo
proporcionado por SSHConnection.
"""


class TunnelManagerCommand:
    """
    Constructor de la clase. Inicializa las variables necesarias para la gestión de túneles.

    :param ssh_connection: Instancia activa de SSHConnection con los datos de la sesión SSH actual.
    """

    def __init__(self, ssh_connection):
        self.console = Console()
        self.ssh_connection = ssh_connection
        self.host = ssh_connection.host
        self.username = ssh_connection.username
        self.port = ssh_connection.port

    """
    Método principal que muestra el menú de opciones para gestionar túneles SSH.
    Permite al usuario elegir entre crear un túnel local, uno remoto, ver túneles activos o salir.
    """

    def run(self):
        self.console.print("[bold blue]🔌 Gestión de Túneles SSH[/bold blue]")

        options = {
            "1": ("Crear túnel local (Local Forwarding)", self.local_tunnel),
            "2": ("Crear túnel remoto (Remote Forwarding)", self.remote_tunnel),
            "3": ("Ver túneles activos", self.list_active_tunnels),
            "4": ("Volver", lambda: None)
        }

        while True:
            # Muestra todas las opciones disponibles en el menú
            for key, (desc, _) in options.items():
                self.console.print(f"[cyan]{key}[/cyan]. {desc}")
            # Solicita al usuario que seleccione una opción del menú
            choice = Prompt.ask("\nSeleccione una opción", choices=list(options.keys()))
            if choice == "4":
                break # Opción "Volver"

            _, action = options[choice]
            action()

    """
    Método que solicita los datos necesarios y crea un túnel local.
    Verifica primero si el usuario ha generado y copiado sus claves SSH.
    """

    def local_tunnel(self):
        if not self.ssh_connection.check_keys():
            return

        local_port = Prompt.ask("[ ] Puerto local (ej: 8080)")
        remote_host = Prompt.ask("[ ] Host remoto (ej: localhost)")
        remote_port = Prompt.ask("[ ] Puerto remoto (ej: 3306)")
        # Se delega en la clase Tunnel la creación del túnel
        Tunnel.create_local(self.username, self.host, self.port, local_port, remote_host, remote_port)

    """
    Método que solicita los datos necesarios y crea un túnel remoto.
    Verifica primero si el usuario ha generado y copiado sus claves SSH.
    """

    def remote_tunnel(self):
        if not self.ssh_connection.check_keys():
            return

        remote_port = Prompt.ask("[ ] Puerto remoto (ej: 9090)")
        local_host = Prompt.ask("[ ] Host local (ej: localhost)")
        local_port = Prompt.ask("[ ] Puerto local (ej: 3000)")
        # se delega en la clase Tunnel la creación del túnel
        Tunnel.create_remote(self.username, self.host, self.port, remote_port, local_host, local_port)

    """
    Método que analiza los procesos en ejecución del sistema para encontrar túneles SSH activos.
    Busca comandos ssh con las opciones -L o -R que indican túneles locales o remotos.
    Muestra los resultados al usuario de forma legible.
    """
    def list_active_tunnels(self):
        self.console.print("\n[bold yellow]🔍 Buscando túneles SSH activos...[/bold yellow]\n")

        try:
            # Ejecuta el comando ps aux para obtener todos los procesos del sistema
            result = subprocess.run(
                ["ps", "aux"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            # Filtra procesos que son conexiones SSH con túneles locales (-L) o remotos (-R)
            ssh_lines = [
                line for line in result.stdout.splitlines()
                if "ssh" in line and (" -L" in line or " -R" in line)
            ]
            # Si no hay resultados, lo indica al usuario
            if not ssh_lines:
                self.console.print("[dim]No se encontraron túneles SSH activos.[/dim]")
                return
            # Muestra cada línea encontrada como un túnel activo
            for line in ssh_lines:
                self.console.print(f"[green]✔[/green] {line}")

        except Exception as e:
            self.console.print(f"[red]✖ Error al obtener túneles activos:[/red] {e}")
