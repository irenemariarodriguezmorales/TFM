## SSHTool 

Herramienta que busca hacer más accesible el protocolo SSH, optimizando la experiencia de conexión remota y facilitando el descubrimiento de sus capacidades menos conocidas para todo tipo de usuarios. 

Para utilizar la herramienta, es recomendable crear un entorno virtual en un sistema Linux (único sistema operativo donde la herramienta funciona) con Python donde instalar las dependencias necesarias. Se debe tener instalado Python 3.6 o superior. 

Primero, se debe crear un entorno virtual para evitar conflictos con otras dependencias del sistema con “python3 -m venv venv_ubuntu”. Luego, se activa el entorno con “source venv_ubuntu/bin/activate”. Finalmente, se instalan las dependencias con “pip install rich paramiko” y “pip install pexpect”.

Para acceder al menú de ayuda se debe ejecutar "python3 SSHTool.py --help" o "python3 SSHTool.py --h"

Con estos pasos, se puede ejecutar la herramienta con “python3 SSHTool.py”. 
