# Importaciones necesarias de librerías
import os
import subprocess
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
# Importaciones necesarias de las clases
from Connection.SSHConnection import SSHConnection

"""
Clase que gestiona la funcionalidad relacionada con claves SSH.
Permite:
- Generar un par de claves localmente
- Copiar la clave pública al servidor remoto
- Visualizar claves autorizadas en el servidor
"""


class KeyManagerCommand:
    """
    Costructor que inicializa el administrador de claves.
    :param ssh_client: Cliente SSH (puede ser None si no existe conexión, para la opción 2 se pide conectar)
    """

    def __init__(self, ssh_client=None):
        self.client = ssh_client  # Puede ser None si no hay conexión activa
        self.console = Console()

    """
    Método principal de la clase que muestra el menú para la generación de claves SSH 
    y permite al usuario seleccionar una acción.
    """

    def run(self):
        self.console.print(Panel("🔐 [bold]Gestión de claves SSH[/bold]", style="magenta"))

        options = {
            "1": ("Generar par de claves SSH localmente", self.generate_local_keys),
            "2": ("Copiar clave pública al servidor remoto", self.copy_key_to_server),
            "3": ("Ver claves existentes en el servidor", self.list_server_keys),
            "4": ("Volver", lambda: None)
        }

        """
        Este bucle muestra el submenú al haber clicado en la funcionalidad de gestionar claves SSH.
        Gracias este bucle el usuario puede observar todas las opciones que puede realizar
        """
        while True:
            for key, (desc, _) in options.items():
                self.console.print(f"[cyan]{key}[/cyan]. {desc}")

            choice = Prompt.ask("\nSeleccione una opción", choices=list(options.keys()))
            if choice == "4":
                break  # Vuelve al menú principal

            _, action = options[choice]
            action()  # Ejecuta la opción seleccionada llamando a su correspondiente clase (responsabilidad delegada)

    """
    Método que genera un par de claves SSH (privada y pública) localmente en la ruta indicada por el usuario.
    Las claves se guardan con nombres fijos: clave_privada y clave_publica.pub
    """

    def generate_local_keys(self):
        self.console.print("\n[bold blue]🛠 Generar par de claves SSH[/bold blue]")

        # Se le pregunta al usuario en qué directorio quiere guardar las claves
        folder = Prompt.ask(
            "[ ] Ruta del directorio donde guardar las claves",
            default="~/.ssh"
        )
        folder = os.path.expanduser(folder)  # Obtiene la ruta absoluta

        # Construir rutas completas para clave privada y pública
        private_key = os.path.join(folder, "clave_privada")
        public_key = os.path.join(folder, "clave_publica.pub")

        # Validar que no es una ruta inválida (puede haber elegido un archivo sin querer)
        if os.path.isfile(folder):
            self.console.print(f"[red]✖ La ruta '{folder}' es un archivo, no un directorio.[/red]")
            return

        # Si ya existen las claves, preguntar si sobrescribirlas
        if os.path.exists(private_key) or os.path.exists(public_key):
            self.console.print(f"[yellow]⚠ Ya existen claves en: {folder}[/yellow]")
            overwrite = Prompt.ask("[ ] ¿Desea sobrescribirlas?", choices=["si", "no"], default="no")
            if overwrite != "si":
                self.console.print("[dim]Operación cancelada por el usuario.[/dim]")
                return

        # Crear carpeta si no existe
        try:
            os.makedirs(folder, exist_ok=True)
            self.console.print(f"[blue]📁 Guardando claves en:[/blue] {folder}")

            # Intenta generar las claves con ssh-keygen
            subprocess.run([
                "ssh-keygen", "-t", "rsa", "-b", "2048",
                "-f", private_key, "-N", ""
            ], check=True)

            # Renombrar la clave pública para que el usuario pueda diferenciarlas mejor
            os.rename(private_key + ".pub", os.path.join(folder, "clave_publica.pub"))

            self.console.print(f"[green]✔ Claves generadas correctamente.[/green]")
            self.console.print(f"[bold]🔐 Clave privada:[/bold] {private_key}")
            self.console.print(f"[bold]🔓 Clave pública:[/bold] {public_key}")

        except Exception as e:
            self.console.print(f"[red]✖ Error al generar las claves: {e}[/red]")

    """
    Método que copia la clave pública local al archivo authorized_keys del servidor remoto.
    Si no hay conexión SSH activa, pregunta por realizar una conexión.
    """

    def copy_key_to_server(self):
        # Si no hay conexión SSH activa, se pregunta al usuario si quiere realizarla para poder seguir con la acción
        if not self.client:
            self.console.print("[yellow]⚠ No hay conexión SSH activa.[/yellow]")
            wants_connect = Prompt.ask("[ ] ¿Desea conectarse ahora al servidor?", choices=["si", "no"], default="si")
            if wants_connect != "si":
                self.console.print("[dim]Operación cancelada.[/dim]")
                return

            # Inicia una conexión SSH
            ssh_conn = SSHConnection.create_connection()
            if not ssh_conn:
                self.console.print("[red]✖ No se pudo establecer la conexión SSH.[/red]")
                return

            self.client = ssh_conn.get_client()  # Guarda el cliente resultante

        # Solicita la ruta a la clave pública local
        pub_key_path = Prompt.ask(
            "[ ] Ruta de la clave pública a copiar",
            default="~/.ssh/clave_publica.pub"
        )
        # Convierte rutas que contienen ~ en rutas absolutas del usuario
        pub_key_path = os.path.expanduser(pub_key_path)

        # Condición que valida si la ruta proporcionada es correcta
        if not os.path.exists(pub_key_path):
            self.console.print(f"[red]✖ No se encontró la clave pública en: {pub_key_path}[/red]")
            return

        try:
            self.console.print("[blue]🔍 Verificando directorio ~/.ssh en el servidor...[/blue]")
            # Crea el directorio .ssh en el home del usuario si no existe (-p no lanza error si el directorio ya existe)
            # y cambia los permisos del directorio .ssh a 700 (solo el propietario puede leer, escribir y acceder)
            self.client.exec_command("mkdir -p ~/.ssh && chmod 700 ~/.ssh")

            self.console.print("[blue]📥 Leyendo clave pública local...[/blue]")
            # Abre el archivo en modo lectura.
            # (Asegura cierre automático del archivo con with).
            with open(pub_key_path, "r") as pub_key_file:
                # Lee el contenido completo del archivo y elimina espacios y saltos de línea.
                pub_key = pub_key_file.read().strip()

            # Comprueba si la clave ya existe en el servidor
            stdin, stdout, stderr = self.client.exec_command(
                # Comando para leer (y si es necesario, crear) el archivo authorized_keys del servidor remoto,
                # donde se almacenan las claves públicas autorizadas para el acceso por SSH.
                "cat ~/.ssh/authorized_keys || touch ~/.ssh/authorized_keys")
            # Lee la salida del comando remoto (obtiene los bytes recibidos (read) y convierte esos bytes en texto).
            existing_keys = stdout.read().decode()

            # Condición para comprobar si la clave pública ya existe en el servidor
            if pub_key in existing_keys:
                self.console.print("[yellow]⚠ La clave ya existe en el servidor.[/yellow]")
                return

            # Si la clave pública no existe en el servidor, se añade
            self.console.print("[blue]🔐 Añadiendo clave pública a authorized_keys...[/blue]")
            # Busca todas las comillas dobles " dentro del texto pub_key y las reemplaza por \"
            # para que no rompan el comando echo en la shell
            escaped_key = pub_key.replace('"', r'\"')
            # Comando que añade la clave pública al final del archivo authorized_keys del servidor remoto
            # También, se cambian los permisos para que sean correctos.
            self.client.exec_command(
                f'echo "{escaped_key}" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys')

            self.console.print("[green]✔ Clave pública copiada y autorizada correctamente en el servidor.[/green]")

        except Exception as e:
            self.console.print(f"[red]✖ Error al copiar la clave: {e}[/red]")

    """
    Método que muestra todas las claves públicas autorizadas actualmente en el servidor remoto 
    (archivo authorized_keys). Si no hay conexión SSH activa, ofrece al usuario realizarla.
    """

    def list_server_keys(self):
        # Verifica si hay cliente SSH activo
        if not self.client:
            self.console.print("[yellow]⚠ No hay conexión SSH activa.[/yellow]")
            wants_connect = Prompt.ask("[ ] ¿Desea conectarse ahora al servidor?", choices=["si", "no"], default="si")
            if wants_connect != "si":
                self.console.print("[dim]Operación cancelada.[/dim]")
                return

            # Inicia nueva conexión SSH
            ssh_conn = SSHConnection.create_connection()
            if not ssh_conn:
                self.console.print("[red]✖ No se pudo establecer la conexión SSH.[/red]")
                return

            self.client = ssh_conn.get_client()  # Guarda el cliente resultante

        try:
            # Ejecuta el comando remoto para leer el archivo authorized_keys
            stdin, stdout, stderr = self.client.exec_command("cat ~/.ssh/authorized_keys")
            output = stdout.read().decode().strip()

            # Muestra el contenido si hay claves
            if output:
                self.console.print(Panel(output, title="🔑 Claves autorizadas en el servidor", style="cyan"))
            else:
                self.console.print("[yellow]No hay claves autorizadas registradas en el servidor.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]✖ Error al listar claves: {e}[/red]")
