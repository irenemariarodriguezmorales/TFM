# Importaciones necesarias de librerías
import os
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
import subprocess

"""
Clase encargada de controlar la transferencia de archivos mediante SFTP o SCP sobre una conexión SSH que ya existe.
Permite al usuario subir o descargar archivos.
"""


class FileTransferCommand:
    """
    Constructor que inicializa la clase con el cliente SSH proporcionado.
    """

    def __init__(self, ssh_client, host, username, port):

        self.client = ssh_client
        self.console = Console()
        self.sftp = None  # SFTP se inicializa en tiempo de ejecución
        self.host = host
        self.username = username
        self.port = port

    """
    Método principal de la clase que muestra el menú de transferencia de archivos (subir/descargar).
    También pregunta qué protocolo se quiere usar (SCP o SFTP)
    """

    def run(self):
        self.console.print(Panel("📂 [bold]Transferencia de archivos por SSH[/bold]", style="green"))

        # Pregunta qué acción desea hacer el usuario
        action = Prompt.ask(
            "[ ] ¿Qué desea hacer?",
            choices=["subir", "descargar", "volver"],
            default="subir"
        )

        if action == "volver":
            return

        # Pregunta qué protocolo quiere utilizar para la transferencia
        protocol = Prompt.ask(
            "[ ] ¿Qué protocolo desea utilizar?",
            choices=["sftp", "scp"],
            default="sftp"
        )

        try:
            if protocol == "sftp":
                self.transfer_by_sftp(action)
            elif protocol == "scp":
                self.transfer_by_scp(action)
        except Exception as e:
            self.console.print(f"[bold red]✖ Error durante la transferencia: {e}[/bold red]")

    """
        Método que pregunta las rutas de origen y destino según la acción seleccionada por el usuario usando el 
        protocolo SFTP.
    """

    def transfer_by_sftp(self, action):
        # Abre sesión SFTP sobre el cliente SSH
        self.sftp = self.client.open_sftp()

        if action == "subir":  # Si el usuario decide subir un archivo al servidor remoto
            local_path = Prompt.ask("[📁] Ruta del archivo local")
            remote_path = Prompt.ask("[🗂️] Ruta destino en el servidor")

            # Si el destino parece ser un directorio, se añade el nombre del archivo automáticamente
            if remote_path.endswith("/") or "." not in os.path.basename(remote_path):
                filename = os.path.basename(local_path)
                remote_path = os.path.join(remote_path, filename).replace("\\", "/")

            self.transfer_file_sftp("put", local_path, remote_path)

        elif action == "descargar":  # Si el usuario quiere descargar en local un archivo que está en el servidor
            remote_path = Prompt.ask("[🗂️] Ruta del archivo en el servidor")
            local_path = Prompt.ask("[📁] Ruta destino en tu equipo")

            # Si el destino es un directorio, se añade el nombre del archivo del servidor
            if os.path.isdir(local_path):
                filename = os.path.basename(remote_path)
                local_path = os.path.join(local_path, filename)

            self.transfer_file_sftp("get", remote_path, local_path)

        # Cierra sesión SFTP
        self.sftp.close()

    """
    Método que pregunta las rutas de origen y destino según la acción seleccionada por el usuario usando el 
    protocolo SCP, usa el programa scp que ya está instalado en el sistema. Pregunta por la contraseña del servidor.
    """

    def transfer_by_scp(self, action):
        scp_cmd = []
        if action == "subir":
            local_path = Prompt.ask("[📁] Ruta del archivo local")
            remote_path = Prompt.ask("[🗂️] Ruta destino en el servidor")
            scp_cmd = [
                "scp", "-P", str(self.port),
                local_path,
                f"{self.username}@{self.host}:{remote_path}"
            ]
        elif action == "descargar":
            remote_path = Prompt.ask("[🗂️] Ruta del archivo en el servidor")
            local_path = Prompt.ask("[📁] Ruta destino en tu equipo")
            scp_cmd = [
                "scp", "-P", str(self.port),
                f"{self.username}@{self.host}:{remote_path}",
                local_path
            ]
        try:
            subprocess.run(scp_cmd, check=True)
            self.console.print(f"[bold green]✔ Transferencia SCP completada correctamente[/bold green]")
        except Exception as e:
            self.console.print(f"[bold red]✖ Error en la transferencia: {e}[/bold red]")

    """
    Método que realiza la transferencia de archivos vía SFTP usando put o get según la opción elegida por el usuario.
    :param sftp_method: 'put' para subir o 'get' para descargar
    :param src: Ruta origen del archivo
    :param dest: Ruta destino del archivo
    """

    def transfer_file_sftp(self, sftp_method, src, dest):
        try:
            if sftp_method == "put":
                self.sftp.put(src, dest)
            else:
                self.sftp.get(src, dest)

            self.console.print(f"[bold green]✔ Transferencia completada: {os.path.basename(dest)}[/bold green]")
        except Exception as e:
            self.console.print(f"[bold red]✖ Error en la transferencia: {e}[/bold red]")
