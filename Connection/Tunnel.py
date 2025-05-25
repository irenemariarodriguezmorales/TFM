# Importaciones necesarias de librerías
import subprocess
import time
# Importaciones necesarias de las clases
from rich.console import Console
from rich.prompt import Prompt
from os.path import expanduser

"""
Clase que gestiona la creación de túneles SSH (locales y remotos) utilizando claves privadas.
"""


class Tunnel:
    """
    Opciones para configurar el comportamiento de la conexión SSH.
    - Desactiva la comprobación estricta de claves de host (StrictHostKeyChecking).
    - Evita guardar claves de host en el archivo known_hosts (UserKnownHostsFile).
    - Establece un tiempo de 60 segundos para mantener la conexión ssh activa (ServerAliveInterval).
    """

    SSH_OPTIONS = [
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ServerAliveInterval=60"
    ]

    """
    Método que crea un túnel local.
    
    Parámetros:
    - user: Usuario SSH.
    - host: Dirección del servidor SSH.
    - port: Puerto SSH del servidor.
    - local_port: Puerto local que estará disponible para redirigir el tráfico.
    - remote_host: Host de destino al que se conectará el servidor remoto.
    - remote_port: Puerto remoto al que se redirigirá el tráfico.
    """

    @staticmethod
    def create_local(user, host, port, local_port, remote_host, remote_port):
        console = Console()
        console.print(
            f"[green]🚇 Creando túnel local con clave SSH: localhost:{local_port} → {remote_host}:{remote_port}[/green]")

        # Solicita al usuario la ruta de la clave privada (con valor por defecto)
        key_path = Prompt.ask("[ ] Ruta de la clave privada", default="~/.ssh/clave_privada")
        key_path = expanduser(key_path)

        # Construye el comando SSH.
        command = [
            "ssh",
            *Tunnel.SSH_OPTIONS,
            "-i", key_path,
            "-L", f"{local_port}:{remote_host}:{remote_port}",
            f"{user}@{host}",
            "-p", str(port),
            "-N" # No ejecutar comandos remotos, solo establecer la conexión.
        ]

        console.print(f"[dim]Ejecutando:[/dim] {' '.join(command)}")

        try:
            # Lanza el comando en segundo plano como un proceso separado.
            proc = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                start_new_session=True # Permite que el túnel siga activo si la herramienta se cierra.
            )

            # Espera un segundo para detectar errores.
            time.sleep(1)

            # Si el proceso ha terminado, extrae el error
            if proc.poll() is not None:
                _, err = proc.communicate()
                raise RuntimeError(f"SSH falló: {err.decode().strip()}")

            console.print("[bold green]✔ Túnel local iniciado en segundo plano[/bold green]")
        except Exception as e:
            console.print(f"[bold red]✖ Error al crear túnel:[/bold red] {e}")

    """
    Método que crea un túnel remoto.
    """
    @staticmethod
    def create_remote(user, host, port, remote_port, local_host, local_port):
        console = Console()
        console.print(
            f"[green]🚇 Creando túnel remoto con clave SSH: {host}:{remote_port} → {local_host}:{local_port}[/green]")

        # Solicita al usuario la ruta de la clave privada.
        key_path = Prompt.ask("[ ] Ruta de la clave privada", default="~/.ssh/clave_privada")
        key_path = expanduser(key_path)

        # Construye el comando SSH.
        command = [
            "ssh",
            *Tunnel.SSH_OPTIONS,
            "-i", key_path,
            "-R", f"{remote_port}:{local_host}:{local_port}",
            f"{user}@{host}",
            "-p", str(port),
            "-N"
        ]

        console.print(f"[dim]Ejecutando:[/dim] {' '.join(command)}")

        try:
            # Lanza el comando en segundo plano como un proceso separado
            proc = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                start_new_session=True
            )

            time.sleep(1)

            if proc.poll() is not None:
                _, err = proc.communicate()
                raise RuntimeError(f"SSH falló: {err.decode().strip()}")

            console.print("[bold green]✔ Túnel remoto iniciado en segundo plano[/bold green]")
        except Exception as e:
            console.print(f"[bold red]✖ Error al crear túnel:[/bold red] {e}")
