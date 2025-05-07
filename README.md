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

Se recomienda ejecutar este comando en un directorio temporal o en tu home, ya que el script clonará el proyecto en una ubicación fija (`/root/ControlPréstamos`). Ejecútalo como `root` para que el script pueda instalar paquetes, crear directorios en `/root`, y configurar el servicio systemd automáticamente.

```bash
wget --no-cache https://raw.githubusercontent.com/sysdevfiles/loanbot/main/setup.sh -O setup.sh && chmod +x setup.sh && bash setup.sh && rm setup.sh
```

**Nota Importante sobre el comportamiento esperado de `setup.sh`:**
El script `setup.sh` está diseñado para ser ejecutado como `root` y realizará lo siguiente:
1.  **Clonar el Repositorio:** Creará el directorio del proyecto en `/root/ControlPréstamos` (si no existe o si eliges re-clonar) y clonará el contenido completo de `https://github.com/sysdevfiles/loanbot.git` dentro de él. La ruta de clonación `/root` está fijada en el script.
2.  **Navegar al Directorio del Proyecto:** Cambiará al directorio `/root/ControlPréstamos`.
3.  **Continuar con la Configuración:** Realizará todas las tareas de configuración subsiguientes dentro del contexto del proyecto clonado.

**El script `setup.sh` (una vez ejecutado) realizará lo siguiente:**
*   Verificará la instalación de `git`, Python 3 y `pip3`, intentando instalarlos si faltan.
*   Clonará el repositorio en `/root/ControlPréstamos`. Si el directorio ya existe, te preguntará (yes/no) si deseas eliminarlo y volver a clonar.
*   Navegará al directorio del proyecto clonado (`/root/ControlPréstamos`).
*   Creará un entorno virtual llamado `venv`.
*   Activará el entorno virtual para la sesión del script.
*   Actualizará `pip` a la última versión.
*   Instalará todas las dependencias listadas en `requirements.txt`.
*   **Te solicitará interactivamente los valores para las variables de entorno (Token de Telegram, Admin ID opcional, nombres para Google Sheet y Worksheet, y la ruta para el archivo de credenciales JSON de Google OAuth).**
*   **Creará un archivo JSON base para tus credenciales de Google OAuth 2.0 en la ruta que especifiques (por defecto `config/client_secret_oauth.json` dentro del proyecto).**
*   **Automáticamente abrirá el editor `nano` para que pegues el contenido de tu archivo JSON de credenciales OAuth 2.0 descargado de Google Cloud Console en el archivo recién creado. Deberás guardar (Ctrl+O, Enter) y cerrar (Ctrl+X) `nano` para continuar.**
*   Creará/actualizará el archivo `.env` con la información proporcionada.
*   Opcionalmente (si respondes `yes`), te guiará para configurar el bot como un servicio systemd:
    *   Creará el archivo `/etc/systemd/system/loanbot.service`.
    *   Recargará el demonio de systemd.
    *   Habilitará el servicio para que inicie en el arranque.
    *   **NO iniciará el servicio automáticamente.** Te dará instrucciones para ejecutar `main.py` manualmente primero para la autorización de Google OAuth, y luego cómo iniciar el servicio.

**Una vez que `setup.sh` haya completado su ejecución:**

**Paso 2: Verificación y Completado de la Configuración (Sigue las instrucciones del script)**

1.  **Archivo `.env`**:
    *   El script `setup.sh` habrá creado un archivo `.env` en `/root/ControlPréstamos/.env` con los valores que proporcionaste.
    *   **Verifica** que los valores sean correctos, especialmente `GOOGLE_OAUTH_CLIENT_SECRET_FILE`, que debe apuntar al archivo JSON que editaste.

2.  **Archivo de Credenciales de Google OAuth 2.0**:
    *   El script `setup.sh` habrá creado un archivo JSON base (ej. `/root/ControlPréstamos/config/client_secret_oauth.json` o la ruta que hayas especificado).
    *   **Durante la ejecución del script, `nano` se abrió automáticamente para que editaras este archivo.** Debiste pegar el contenido completo de tu archivo JSON de credenciales de cliente OAuth 2.0 descargado de Google Cloud Console y luego guardar y cerrar `nano`.
    *   **Asegúrate de que el contenido del archivo JSON sea el correcto y que hayas guardado los cambios.**
    *   El contenido del archivo debe ser el JSON exacto proporcionado por Google.

3.  **Configurar Google Sheets API**:
    *   Ve a [Google Cloud Console](https://console.cloud.google.com/).
    *   Asegúrate de que las APIs "Google Drive API" y "Google Sheets API" estén habilitadas para el proyecto asociado a tus credenciales OAuth 2.0 (el `project_id` que está en tu JSON).
    *   **Importante para OAuth 2.0**: No necesitas "compartir" la hoja de cálculo con una dirección de correo de cuenta de servicio. La autorización se realizará a través de tu propia cuenta de Google cuando ejecutes el bot por primera vez.

**Paso 3: Verificación Manual de Dependencias (Opcional/Solución de Problemas)**
Si encuentras problemas con las importaciones de `gspread` o `oauth2client` después de ejecutar `setup.sh`, o si prefieres instalar manualmente, navega al directorio del proyecto clonado (`/root/ControlPréstamos`), asegúrate de que tu entorno virtual (`venv`) esté activado:
```bash
# cd /root/ControlPréstamos  (si no estás ya allí)
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
Este paso ahora es manejado interactivamente por el script `setup.sh`. Solo necesitas verificar los resultados como se describe en el "Paso 2: Verificación y Completado de la Configuración", especialmente la edición del archivo JSON de credenciales a través de `nano`.

**Paso 5: Configurar Google Sheets API (Detalles ya cubiertos arriba)**

**Paso 6 (Ahora Paso 5): Ejecutar el Bot Manualmente (Para Pruebas y Autorización Inicial de Google)**
Con el entorno virtual activado (desde `/root/ControlPréstamos`), el archivo `.env` configurado y el archivo JSON de credenciales OAuth 2.0 correctamente editado:
```bash
# cd /root/ControlPréstamos
# source venv/bin/activate
python3 main.py
```
El bot comenzará a escuchar los comandos en Telegram.
**Importante - Primera Ejecución con OAuth 2.0 (Obligatorio antes de usar Systemd):**
*   La consola te mostrará una URL. Cópiala y ábrela en un navegador.
*   Inicia sesión con tu cuenta de Google (la que tiene acceso a la hoja de cálculo).
*   Autoriza los permisos solicitados.
*   Copia el código de autorización que te dé el navegador y pégalo de vuelta en la consola si se te solicita.
Una vez autorizado y veas que el bot funciona (ej. responde a `/start`), puedes detenerlo con `Ctrl+C`. Este paso crea un archivo de token (usualmente en `/root/.config/gspread/loanbot_authorized_user.json`) que permitirá ejecuciones no interactivas futuras.

**Paso 7 (Ahora Paso 6): Configurar e Iniciar como Servicio Systemd (Para Producción en Ubuntu)**
Para que el bot se ejecute de forma continua en segundo plano y se inicie automáticamente con el sistema.

*   **Opción A: Configuración Interactiva con `setup.sh` (Recomendado)**
    1.  Durante la ejecución de `setup.sh` (como `root`), cuando el script pregunte `¿Deseas configurar el bot como un servicio systemd ahora? (yes/no):`, responde `yes`.
    2.  El script creará y habilitará el servicio `loanbot.service`.
    3.  **Sigue las instrucciones que te dará el script `setup.sh` al final de la sección de systemd:**
        *   Primero, ejecuta `python3 main.py` manualmente (como se describe en el "Paso 5" anterior) para completar la autorización de Google OAuth.
        *   Una vez hecho esto y el bot haya funcionado manualmente, puedes iniciar el servicio con:
            ```bash
            systemctl start loanbot.service
            ```
        *   Verifica su estado con:
            ```bash
            systemctl status loanbot.service
            ```

*   **Opción B: Configuración Manual**
    Si omitiste la configuración interactiva durante `setup.sh`, o si necesitas ajustar la configuración manualmente:
    1.  Crea un archivo llamado `loanbot.service` en `/etc/systemd/system/` (ej. `nano /etc/systemd/system/loanbot.service`).
    2.  Pega el siguiente contenido en el archivo. El script `setup.sh` usa `/root/ControlPréstamos` como `WorkingDirectory` y para `ExecStart`.
        ```systemd
        [Unit]
        Description=Bot de Telegram para Gestión de Préstamos
        After=network.target

        [Service]
        User=root
        Group=root
        WorkingDirectory=/root/ControlPréstamos 
        ExecStart=/root/ControlPréstamos/venv/bin/python3 /root/ControlPréstamos/main.py
        Restart=always
        RestartSec=10
        StandardOutput=syslog
        StandardError=syslog
        SyslogIdentifier=loanbot

        [Install]
        WantedBy=multi-user.target
        ```
    3.  Guarda el archivo.
    4.  Ejecuta los siguientes comandos (como `root`):
        ```bash
        systemctl daemon-reload
        systemctl enable loanbot.service
        ```
    5.  **Importante**: Antes de iniciar el servicio por primera vez, ejecuta el bot manualmente para la autorización de Google OAuth:
        ```bash
        cd /root/ControlPréstamos
        source venv/bin/activate
        python3 main.py 
        # Sigue el flujo de autorización en el navegador, luego detén el bot con Ctrl+C.
        deactivate # Opcional, si terminaste con la sesión manual
        ```
    6.  Ahora inicia el servicio:
        ```bash
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
/root/ControlPréstamos/  # Directorio principal del proyecto
├── .env                   # Variables de entorno (NO subir a Git)
├── .env.example           # Ejemplo de variables de entorno
├── .gitignore             # Archivos a ignorar por Git
├── main.py                # Lógica principal del bot y handlers de Telegram
├── google_sheets_integration.py # Módulo para interactuar con Google Sheets
├── requirements.txt       # Dependencias de Python
├── setup.sh               # Script de instalación para Linux (descargado y ejecutado)
├── setup.bat              # Script de instalación para Windows (si se desarrolla)
├── venv/                  # Entorno virtual (ignorado por Git)
└── README.md              # Este archivo
└── config/                # Directorio para archivos de configuración
    └── client_secret_oauth.json # Credenciales de Google OAuth 2.0 (editado por el usuario vía nano, NO subir a Git)
└── loans.db               # Base de datos SQLite (ignorado por Git, creado en ejecución)
```

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o un pull request.
