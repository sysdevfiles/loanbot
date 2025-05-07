# Bot de Gestión de Préstamos Personales para Telegram

Este proyecto es un bot de Telegram diseñado para la gestión de préstamos personales. Permite registrar préstamos, actualizar el estado de los pagos y listar los préstamos existentes. Los datos se almacenan tanto en una base de datos local SQLite como en una hoja de cálculo de Google Spreadsheet para un registro accesible y estructurado.

## Características Principales

*   **Registro de Préstamos**: Guarda la información de cada nuevo préstamo.
*   **Actualización de Pagos**: Permite actualizar el monto pagado y el estado de un préstamo.
*   **Listado de Préstamos**: Muestra los préstamos registrados.
*   **Integración con Google Sheets**:
    *   Almacena automáticamente cada préstamo en una hoja de cálculo.
    *   Actualiza el estado de los pagos amortizados en la hoja de cálculo.
    *   Permite listar los préstamos directamente desde la hoja de Spreadsheet en Telegram.
*   **Almacenamiento Dual**: Utiliza SQLite para una base de datos local rápida y Google Sheets para un registro en la nube y fácil acceso.
*   **Gestión Segura de Credenciales**: Utiliza archivos `.env` para manejar información sensible.

## Tecnologías Utilizadas

*   **Python 3**
*   **python-telegram-bot**: Para la interacción con la API de Telegram.
*   **sqlite3**: Para la base de datos local.
*   **gspread** y **oauth2client**: Para la integración con Google Sheets API.
*   **python-dotenv**: Para la gestión de variables de entorno.
*   **requests**: Para posibles integraciones externas (no implementado activamente en el núcleo de préstamos).
*   **schedule**: Para automatización de tareas (no implementado activamente en el núcleo de préstamos).
*   **Flask** y **Gunicorn**: Para posibles servicios web adicionales (no implementado activamente en el núcleo de préstamos).

## Prerrequisitos

*   Python 3.7 o superior.
*   `pip` (gestor de paquetes de Python).
*   `git` (necesario si `setup.sh` clona el repositorio).
*   `wget` (para descargar el script de instalación).
*   Una cuenta de Telegram y un token de Bot.
*   Una cuenta de Google y acceso a Google Cloud Platform para configurar la API de Google Sheets.
*   Para Ubuntu: `python3-venv` (el script `setup.sh` intentará instalar `python3-pip` si no está presente).

## Instalación Detallada

Sigue estos pasos para configurar y ejecutar el bot en un servidor Ubuntu.

**Paso 1: Descargar y Ejecutar el Script de Instalación (`setup.sh`)**

Este comando descargará la última versión del script `setup.sh` desde el repositorio principal de GitHub, le dará permisos de ejecución, lo ejecutará y finalmente eliminará el archivo `setup.sh` descargado.

Se recomienda ejecutar este comando en el directorio donde deseas que se cree la carpeta principal del proyecto (por ejemplo, en `/opt/` o en tu directorio home). Ejecútalo como `root` si deseas que el script intente configurar el servicio systemd automáticamente.

```bash
wget --no-cache https://raw.githubusercontent.com/sysdevfiles/loanbot/main/setup.sh -O setup.sh && chmod +x setup.sh && bash setup.sh && rm setup.sh
```

**Nota Importante sobre el comportamiento esperado de `setup.sh`:**
Para que el comando anterior funcione como un instalador completo, el script `setup.sh` descargado debería:
1.  **Clonar el Repositorio:** Crear un directorio para el proyecto (ej. `ControlPréstamos`) y clonar el contenido completo de `https://github.com/sysdevfiles/loanbot.git` dentro de él.
2.  **Navegar al Directorio del Proyecto:** Cambiar al directorio recién clonado (ej. `cd ControlPréstamos`).
3.  **Continuar con la Configuración:** Realizar todas las tareas de configuración subsiguientes (crear `venv`, instalar dependencias desde el `requirements.txt` clonado, configurar el servicio systemd opcionalmente, etc.) dentro del contexto del proyecto clonado.

**El script `setup.sh` (una vez ejecutado) realizará lo siguiente:**
*   Verificará la instalación de `git`, Python 3 y `pip3`.
*   Te preguntará dónde clonar el proyecto `ControlPréstamos`.
*   Clonará el repositorio en la ubicación especificada.
*   Navegará al directorio del proyecto clonado.
*   Creará un entorno virtual llamado `venv`.
*   Activará el entorno virtual para la sesión del script.
*   Actualizará `pip` a la última versión.
*   Instalará todas las dependencias listadas en `requirements.txt`.
*   **Te solicitará interactivamente los valores para las variables de entorno y creará el archivo `.env`**.
*   **Creará un archivo JSON base para tus credenciales de Google OAuth 2.0 y te pedirá que lo edites con `nano` para pegar tus credenciales reales.**
*   Opcionalmente, te guiará para configurar el bot como un servicio systemd (si se ejecuta como `root`).

**Una vez que `setup.sh` haya completado su ejecución:**

**Paso 2: Verificación y Completado de la Configuración**

1.  **Archivo `.env`**:
    *   El script `setup.sh` habrá creado un archivo `.env` en el directorio del proyecto (ej. `ControlPréstamos/.env`) con los valores que proporcionaste.
    *   **Verifica** que los valores en `ControlPréstamos/.env` sean correctos, especialmente `GOOGLE_OAUTH_CLIENT_SECRET_FILE`, que debe apuntar al archivo JSON que editaste.

2.  **Archivo de Credenciales de Google OAuth 2.0**:
    *   El script `setup.sh` habrá creado un archivo JSON base (ej. `ControlPréstamos/config/client_secret_oauth.json`).
    *   Durante la ejecución del script, se te habrá pedido que edites este archivo usando `nano` (ej. `nano ControlPréstamos/config/client_secret_oauth.json`) y **pegues el contenido completo de tu archivo JSON de credenciales de cliente OAuth 2.0 descargado de Google Cloud Console**.
    *   **Asegúrate de haber guardado los cambios en `nano` (Ctrl+O, Enter, luego Ctrl+X).**
    *   El contenido del archivo debe ser el JSON exacto proporcionado por Google.

3.  **Configurar Google Sheets API**:
    *   Ve a [Google Cloud Console](https://console.cloud.google.com/).
    *   Asegúrate de que las APIs "Google Drive API" y "Google Sheets API" estén habilitadas para el proyecto asociado a tus credenciales OAuth 2.0 (el `project_id` que está en tu JSON).
    *   **Importante para OAuth 2.0**: No necesitas "compartir" la hoja de cálculo con una dirección de correo de cuenta de servicio. La autorización se realizará a través de tu propia cuenta de Google cuando ejecutes el bot por primera vez.

**Paso 3: Verificación Manual de Dependencias (Opcional/Solución de Problemas)**
Si encuentras problemas con las importaciones de `gspread` o `oauth2client` después de ejecutar `setup.sh`, o si prefieres instalar manualmente, navega al directorio del proyecto clonado (ej. `ControlPréstamos`), asegúrate de que tu entorno virtual (`venv`) esté activado:
```bash
# cd /ruta/a/ControlPréstamos  (si no estás ya allí)
source venv/bin/activate
```
Luego, puedes instalar o reinstalar los paquetes específicos:
```bash
pip3 install gspread oauth2client python-dotenv python-telegram-bot requests schedule Flask gunicorn
```
O verifica que estén en `requirements.txt` y vuelve a ejecutar:
```bash
pip3 install -r requirements.txt
```

**Paso 4 (Eliminado/Integrado): Configurar Variables de Entorno**
Este paso ahora es manejado interactivamente por el script `setup.sh`. Solo necesitas verificar los resultados como se describe en el "Paso 2: Verificación y Completado de la Configuración", especialmente la edición del archivo JSON de credenciales.

**Paso 5 (Ahora Paso 4): Configurar Google Sheets API (Detalles ya cubiertos arriba)**

**Paso 6 (Ahora Paso 5): Ejecutar el Bot Manualmente (Para Pruebas)**
Con el entorno virtual activado, el archivo `.env` configurado y el archivo JSON de credenciales OAuth 2.0 correctamente editado:
```bash
python3 main.py
```
El bot comenzará a escuchar los comandos en Telegram.
**Importante - Primera Ejecución con OAuth 2.0:**
*   La consola te mostrará una URL. Cópiala y ábrela en un navegador.
*   Inicia sesión con tu cuenta de Google (la que tiene acceso a la hoja de cálculo).
*   Autoriza los permisos solicitados.
*   Copia el código de autorización que te dé el navegador y pégalo de vuelta en la consola si se te solicita.
Una vez autorizado, el bot debería funcionar. Presiona `Ctrl+C` para detenerlo.

**Paso 7 (Ahora Paso 6): Configurar como Servicio Systemd (Para Producción en Ubuntu)**
Para que el bot se ejecute de forma continua en segundo plano y se inicie automáticamente con el sistema.
**Nota**: Las siguientes instrucciones asumen que estás operando como `root` en el VPS para la configuración del servicio.

*   **Opción A: Configuración Interactiva con `setup.sh` (Recomendado si ejecutas `setup.sh` como root)**
    1.  Durante la ejecución de `setup.sh` (como `root`), cuando el script pregunte `¿Deseas configurar el bot como un servicio systemd ahora? (s/N):`, responde `s`.
    2.  Ingresa la ruta absoluta al directorio de tu proyecto cuando se te solicite (ej. `/root/ControlPréstamos`).
    3.  El script intentará crear `/etc/systemd/system/loanbot.service`, recargar systemd y habilitar el servicio.
    4.  Si tiene éxito, podrás iniciar el servicio con:
        ```bash
        systemctl start loanbot.service
        ```

*   **Opción B: Configuración Manual**
    Si omitiste la configuración interactiva durante `setup.sh`, o si el script no se ejecutó como `root`, o necesitas ajustar la configuración manualmente:
    1.  Crea un archivo llamado `loanbot.service` en `/etc/systemd/system/` (ej. `nano /etc/systemd/system/loanbot.service`).
    2.  Pega el siguiente contenido en el archivo. Si ejecutaste `setup.sh` y omitiste este paso, el script habrá mostrado una plantilla similar en la consola que puedes usar como base.
        ```systemd
        [Unit]
        Description=Bot de Telegram para Gestión de Préstamos
        After=network.target

        [Service]
        # Ajusta User y Group si no vas a usar root (asegúrate de los permisos del directorio)
        User=root
        Group=root
        # CAMBIA ESTA RUTA a la ruta absoluta de tu proyecto
        WorkingDirectory=/ruta/absoluta/al/proyecto 
        # CAMBIA ESTA RUTA para que apunte al python de tu venv y al main.py
        ExecStart=/ruta/absoluta/al/proyecto/venv/bin/python3 /ruta/absoluta/al/proyecto/main.py
        Restart=always
        RestartSec=10
        StandardOutput=syslog
        StandardError=syslog
        SyslogIdentifier=loanbot

        [Install]
        WantedBy=multi-user.target
        ```
    3.  **Importante**: Reemplaza `/ruta/absoluta/al/proyecto` con la ruta correcta a tu directorio `ControlPréstamos` (ej. `/root/ControlPréstamos`).
    4.  Guarda el archivo.
    5.  Ejecuta los siguientes comandos (como `root`):
        ```bash
        systemctl daemon-reload
        systemctl enable loanbot.service
        systemctl start loanbot.service
        ```

**Verificar el Estado y Logs del Servicio (para ambas opciones)**:
```bash
systemctl status loanbot.service
journalctl -u loanbot.service -f # Para ver logs en tiempo real (presiona Ctrl+C para salir)
```

**Otros comandos útiles de `systemctl`** (ejecutar como `root`):
*   Detener: `systemctl stop loanbot.service`
*   Reiniciar: `systemctl restart loanbot.service`
*   Deshabilitar inicio automático: `systemctl disable loanbot.service`

## Comandos del Bot (Ejemplos)

*   `/start` - Inicia la interacción con el bot.
*   `/newloan` - (Ejemplo) Registra un nuevo préstamo (la lógica para obtener datos del usuario debe ser implementada).
*   `/pay <ID_Préstamo> <MontoPagado>` - (Ejemplo) Actualiza el estado de un pago.
*   `/listloanssheet` - Lista los préstamos directamente desde Google Sheets.
*   `/help` - Muestra información de ayuda (debe ser implementado). 

(Adapta la lista de comandos según la implementación final en `main.py`)

## Estructura del Proyecto (Simplificada)

```
c:\ControlPréstamos\
├── .env                   # Variables de entorno (NO subir a Git)
├── .env.example           # Ejemplo de variables de entorno
├── .gitignore             # Archivos a ignorar por Git
├── main.py                # Lógica principal del bot y handlers de Telegram
├── google_sheets_integration.py # Módulo para interactuar con Google Sheets
├── requirements.txt       # Dependencias de Python
├── setup.sh               # Script de instalación para Linux/macOS
├── setup.bat              # Script de instalación para Windows
├── venv/                  # Entorno virtual (ignorado por Git)
└── README.md              # Este archivo
└── (opcional) config/
    └── client_secret_oauth.json # Credenciales de Google OAuth 2.0 (editado por el usuario, NO subir a Git)
└── (opcional) loans.db    # Base de datos SQLite (ignorado por Git)
```

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o un pull request.
