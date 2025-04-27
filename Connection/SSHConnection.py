# Importaciones necesarias de librerías
import os
import paramiko
from rich.console import Console
from rich.prompt import Prompt
import subprocess
import pexpect
# Importaciones necesarias de otras clases
from Commands.CommandsExecutorCommand import CommandsExecutorCommand
from Commands.FileTransferCommand import FileTransferCommand
from Connection.ConnectionConfig import ConnectionConfig

"""
Es la clase que permite realizar conexiones SSH al servidor utilizando la librería paramiko.
Posse toda la lógica para realizar conexiones SSH, obtención de shell interactiva (para ejecutar comandos remotamente,
método get_shell()), ejecución de su propio submenú para realizar acciones una vez establecida la sesión SSH 
y cerrar la sesión SSH.
"""


class SSHConnection:
    """
    Este es el constructor donde se inicializa la conexión SSH con los parámetros necesarios.

    :param host: Dirección del servidor remoto (IP o nombre de host)
    :param username: Nombre de usuario SSH
    :param port: Puerto SSH (por defecto 22)
    """

    def __init__(self, host, username, port=22, auth_method="contraseña"):
        self.host = host
        self.username = username
        self.port = int(port)
        self.auth_method = auth_method
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.console = Console()
        self.shell = None  # Se pone a True cuando se inicia el shell interactivo (para ejecutar comandos remotamente)

    """
    Es un método estático que solicita al usuario los datos de conexión SSH.
    Es estático porque no necesita una instancia previa de la clase para funcionar.
    Devuelve una instancia de SSHConnection ya conectada o None si falla.
    Llama al metódo connect() para poder realizar el intento de conexión SSH con el servidor.
    """

    @staticmethod
    def create_connection():
        host, username, port, auth_method = ConnectionConfig.ask_user_connection_data()

        connection = SSHConnection(host, username, port, auth_method)  # Llama al constructor para crear una instancia
        if connection.connect():  # Se llama al método connect() para establecer una conexión
            return connection
        else:
            return None

    """
    Muestra el submenú tras la conexión SSH exitosa.
    El usuario puede ejecutar comandos remotamente, transferir archivos o cerrar sesión.
    """

    def show_session_menu(self):
        console = Console()
        options = {
            "1": ("Ejecutar comandos remotos", lambda: CommandsExecutorCommand(self.shell).run()),  # shell interactiva
            "2": ("Transferir archivos", lambda: FileTransferCommand(self.client, self.host, self.username, self.port).run()),
            "3": ("Volver al menú principal", None)
        }

        """
        Este bucle muestra el submenú una vez que se ha realizado SSH al servidor.
        El bucle termina cuando el usuario elige la opción "3"
        Gracias este bucle el usuario puede observar todas las opciones que puede realizar
        """
        while True:
            console.print("\n[bold]Opciones disponibles:[/bold]")
            for key, (desc, _) in options.items():
                console.print(f"[cyan]{key}[/cyan]. {desc}")

            choice = Prompt.ask("Seleccione una opción", choices=list(options.keys()))
            if choice == "3":
                self.close()  # Cierra la conexión y vuelve al menú principal
                break

            _, action = options[choice]
            if action:
                action()  # Ejecuta la opción seleccionada llamando a su correspondiente clase(responsabilidad delegada)

    """
    Método que establece una conexión SSH solicitando datos al usuario.
    También, inicializa un shell interactivo para ejecutar comandos en tiempo real.
    """

    def connect(self):
        try:
            # Si el usuario quiere realizar la autenticación por contraseña entra por esta condición
            if self.auth_method == "contraseña":
                password = self.console.input("[🔐] Introduzca su contraseña SSH: ")

                # Se procede con la conexión SSH
                self.client.connect(
                    hostname=self.host,
                    username=self.username,
                    password=password,
                    port=self.port,
                    look_for_keys=False,
                    allow_agent=False,
                )

            # Si el usuario quiere realizar la autenticación por clave entra por esta condición
            elif self.auth_method == "clave":
                #  Pregunta primero si tiene generada una clave privada
                if not self.check_keys():
                    return
                # Pregunta por la ruta de la clave privada
                key_path = Prompt.ask(
                    "[ ] Ruta de la clave privada",
                    default="~/.ssh/clave_privada"
                )
                # Obtiene la ruta absoluta de la clave privada
                key_path = os.path.expanduser(key_path)

                # Comprueba si la clave privada existe en la ruta proporcionada (puede haber elegido un directorio)
                if not os.path.exists(key_path):
                    raise Exception(f"No se encontró la clave privada en {key_path}")

                # Se procede con la conexión SSH
                private_key = paramiko.RSAKey.from_private_key_file(key_path)
                self.client.connect(
                    hostname=self.host,
                    username=self.username,
                    pkey=private_key,
                    port=self.port,
                    look_for_keys=False,
                    allow_agent=False,
                )

            # Si el usuario quiere realizar la autenticación por agente SSH entra por esta condición
            elif self.auth_method == "agente":
                #  Pregunta primero si tiene generada una clave privada
                if not self.check_keys():
                    return
                # Crea una instancia del agente SSH de la librería Paramiko.
                # Intenta conectarse al ssh-agent del sistema operativo (proceso en segundo plano que guarda claves
                # privadas en memoria RAM).
                agent = paramiko.Agent()
                # Devuelve una lista de claves privadas que están actualmente cargadas en el agente SSH
                agent_keys = agent.get_keys()

                # Si no hay claves cargadas, se pregunta al usuario si quiere añadirla al agente
                if not agent_keys:
                    self.console.print("[yellow]⚠ No hay claves disponibles en el agente SSH[/yellow]")
                    wants_to_add = Prompt.ask("[ ] ¿Desea añadir una clave al agente ahora?", choices=["sí", "no"], default="sí")

                    # Si el usuario dice que sí, entra por este camino
                    if wants_to_add == "sí":
                        key_path = Prompt.ask("[ ] Ruta de la clave privada a añadir", default="~/.ssh/clave_privada")
                        key_path = os.path.expanduser(key_path)  # Obtiene ruta absoluta

                        if not os.path.exists(key_path):  # Si no encuentra la clave privada, salta error
                            raise Exception(f"No se encontró la clave privada en {key_path}")

                        try:
                            subprocess.run(["ssh-add", key_path], check=True)  # Añade la clave al agente
                            self.console.print("[green]✔ Clave añadida correctamente al agente SSH[/green]")

                            # Reintentar obtener claves desde el agente
                            agent_keys = paramiko.Agent().get_keys()

                            if not agent_keys:
                                raise Exception("No se pudo cargar la clave en el agente SSH")

                        except Exception as e:
                            raise Exception(f"No se pudo añadir la clave al agente SSH: {e}")
                    else:
                        # Si el usuario no quiere añadir agente, se retorna
                        return

                # Si se encuentra al menos una clave, se utiliza la primera disponible para establecer la conexión
                self.client.connect(
                    hostname=self.host,
                    username=self.username,
                    pkey=agent_keys[0],
                    port=self.port,
                    look_for_keys=False,
                    allow_agent=True
                )

            # Si el usuario quiere realizar la autenticación por certificado digital
            elif self.auth_method == "certificado":
                #  Pregunta primero si tiene generada una clave privada
                if not self.check_keys():
                    return
                self.console.print("[bold blue]🔐 Autenticación por certificado digital[/bold blue]")
                ca_key_path = None  # Se usará solo si es necesario

                # 1. ¿Ya tienes un certificado firmado?
                has_cert = Prompt.ask("[ ] ¿Tiene ya un certificado digital generado?", choices=["sí", "no"],
                                      default="no")

                if has_cert == "no":
                    # 2. ¿Quieres generarlo ahora?
                    wants_generate = Prompt.ask("[ ] ¿Desea generar uno ahora?", choices=["sí", "no"], default="sí")
                    if wants_generate == "no":
                        self.console.print("[yellow]❌ Cancelando autenticación por certificado...[/yellow]")
                        return

                    # 3. Ruta a la clave pública que será firmada
                    pub_key_path = Prompt.ask(
                        "[ ] Ruta de la clave pública a firmar",
                        default="~/.ssh/clave_publica.pub"
                    )
                    pub_key_path = os.path.expanduser(pub_key_path)

                    if not os.path.exists(pub_key_path):
                        raise Exception(f"No se encontró la clave pública en: {pub_key_path}")

                    # 4. Ruta del directorio para guardar la clave de la CA
                    ca_folder = Prompt.ask("[ ] Ruta del directorio para guardar la clave de la CA", default="~/.ssh")
                    ca_folder = os.path.expanduser(ca_folder)
                    os.makedirs(ca_folder, exist_ok=True)

                    ca_key_path = os.path.join(ca_folder, "ca")

                    # 5. Generar clave CA si no existe
                    if not os.path.exists(ca_key_path):
                        self.console.print(f"[yellow]⚠ No se encontró una clave de CA en {ca_key_path}[/yellow]")
                        create_ca = Prompt.ask("[ ] ¿Desea generar una nueva clave de CA?", choices=["sí", "no"],
                                               default="sí")
                        if create_ca == "sí":
                            subprocess.run(["ssh-keygen", "-t", "rsa", "-b", "2048", "-f", ca_key_path, "-N", ""],
                                           check=True)
                            self.console.print(f"[green]✔ Clave de CA generada correctamente en: {ca_key_path}[/green]")
                        else:
                            self.console.print("[red]✖ No se puede continuar sin clave de CA.[/red]")
                            return

                    # 6. Generar certificado
                    cert_path = pub_key_path.replace(".pub", "-cert.pub")
                    subprocess.run([
                        "ssh-keygen", "-s", ca_key_path,
                        "-I", self.username,
                        "-n", self.username,
                        "-V", "+52w",
                        "-z", "1",
                        pub_key_path
                    ], check=True)
                    self.console.print(f"[green]✔ Certificado generado correctamente en:[/green] {cert_path}")

                    private_key_path = Prompt.ask("[ ] Ruta de la clave privada asociada",
                                                  default="~/.ssh/clave_privada")

                    private_key_path = os.path.expanduser(private_key_path)

                    if not os.path.exists(private_key_path):
                        raise Exception(f"No se encontró la clave privada en: {private_key_path}")

                else:
                    # 7. Pedir ruta del certificado y de la clave privada asociada
                    cert_path = Prompt.ask("[ ] Ruta del certificado digital (.pub)",
                                           default="~/.ssh/clave_publica-cert.pub")
                    cert_path = os.path.expanduser(cert_path)

                    private_key_path = Prompt.ask("[ ] Ruta de la clave privada asociada",
                                                  default="~/.ssh/clave_privada")
                    private_key_path = os.path.expanduser(private_key_path)

                    if not os.path.exists(cert_path) or not os.path.exists(private_key_path):
                        raise Exception("No se encontraron los archivos necesarios para la autenticación")

                    # 8. Preguntar también por la clave de la CA si se va a subir
                    ca_key_path = Prompt.ask("[ ] Ruta de la clave pública de la CA", default="~/.ssh/ca.pub")
                    ca_key_path = os.path.expanduser(ca_key_path).replace(".pub", "")  # quitar extensión si la tenía

                # 9. Autenticación SSH con la clave privada
                private_key = paramiko.RSAKey.from_private_key_file(private_key_path)
                self.client.connect(
                    hostname=self.host,
                    username=self.username,
                    pkey=private_key,
                    port=self.port,
                    look_for_keys=False,
                    allow_agent=False,
                )

                # 10. Subir clave pública de la CA (si existe)
                if ca_key_path:
                    self.console.print("[blue]📦 Subiendo clave pública de la CA al servidor...[/blue]")
                    sftp = self.client.open_sftp()
                    try:
                        sftp.mkdir(".ssh")
                    except IOError:
                        pass
                    sftp.put(ca_key_path + ".pub", ".ssh/ca.pub")
                    sftp.close()

                # 11. Configurar el servidor remoto para aceptar certificados
                cmd = "echo 'TrustedUserCAKeys ~/.ssh/ca.pub' >> /etc/ssh/sshd_config && systemctl restart ssh"

                # Intentar primero sin contraseña
                stdin, stdout, stderr = self.client.exec_command(f"sudo -n bash -c \"{cmd}\"")
                exit_status = stdout.channel.recv_exit_status()

                if exit_status != 0:
                    self.console.print(
                        "[yellow]⚠ No se pudo ejecutar sudo sin contraseña. Intentando con contraseña...[/yellow]")

                    # Pedir la contraseña SSH al usuario
                    ssh_password = Prompt.ask("[🔐] Introduzca su contraseña SSH para sudo", password=True)

                    # Llamada para introducir contraseña para usar sudo
                    output, error = self.run_sudo_command(ssh_password, cmd)

                    if error:
                        raise Exception(f"No se pudo configurar el servidor para aceptar certificados: {error}")
                    else:
                        self.console.print(
                            "[green]✔ Servidor configurado para aceptar certificados usando sudo con contraseña[/green]")
                else:
                    self.console.print("[green]✔ Servidor configurado correctamente con sudo sin contraseña[/green]")

            """
            El método invoke_shell() crea una shell interactiva. Esta inicialización sirve para que el usuario, si 
            elige la opción de ejecutar comandos remotos en el submenú que esta misma clase realiza, 
            pueda realizarlo sin ningún problema. 
            """
            self.shell = self.client.invoke_shell()
            self.console.print("\n[i] Estado: [bold green]Conectado[/bold green]")
            return True

        except Exception as e:
            raise Exception(f"No se pudo conectar: {str(e)}")

    """
    Método auxiliar que se utiliza en la autenticación por clave, agente y certificado para preguntar si ya tiene
    las claves generadas y la clave pública enviada al servidor remoto (estos pasos son necesarios para estos tres
    tipos de autenticación)
    """
    def check_keys(self):
        from Commands.KeyManagerCommand import KeyManagerCommand
        tiene_claves = Prompt.ask(
            "[ ] ¿Ya ha generado las claves SSH (pública y privada)?",
            choices=["sí", "no"],
            default="sí"
        )
        if tiene_claves == "no":
            self.console.print("[red]✖ Debe generar las claves SSH primero. Redirigiendo...[/red]")
            KeyManagerCommand().generate_local_keys()
            return False

        clave_enviada = Prompt.ask(
            "[ ] ¿Ha enviado la clave pública al servidor remoto?",
            choices=["sí", "no"],
            default="sí"
        )
        if clave_enviada == "no":
            self.console.print("[red]✖ Debe copiar la clave pública al servidor. Utilice la autenticación por"
                               " contraseña para enviarla. Redirigiendo...[/red]")
            KeyManagerCommand().copy_key_to_server()
            return False

        return True

    """
    Método que ejecuta un comando remoto con privilegios de sudo, 
    incluso si el servidor requiere introducir una contraseña.
    Se utiliza en la autenticación por certificado
    """

    def run_sudo_command(self, password, command):
        ssh_command = f"ssh -p {self.port} {self.username}@{self.host} 'sudo -S {command}'"
        child = pexpect.spawn(ssh_command, encoding='utf-8', timeout=10)
        try:
            i = child.expect([r"\[sudo\] password for .*:", pexpect.EOF, pexpect.TIMEOUT])
            if i == 0:
                child.sendline(password)
                child.expect(pexpect.EOF)
            output = str(child.before) + str(child.after)
            return output, None
        except pexpect.ExceptionPexpect as e:
            return "", str(e)

    """
    Método que devuelve el shell interactivo para ejecutar comandos en tiempo real
    """

    def get_shell(self):
        return self.shell

    """
    Método que devuelve el cliente SSH (gracias a paramiko) para realizar operaciones como SFTP o exec_command.
    """

    def get_client(self):
        return self.client

    """
    Método que cierra la conexión SSH y muestra un mensaje de estado.
    """

    def close(self):
        if self.client:
            self.client.close()
            self.console.print("[i] Estado: [bold yellow]Conexión cerrada[/bold yellow]")
