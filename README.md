# Bot de Gestión de Préstamos Personales para Telegram

Este proyecto es un bot de Telegram diseñado para la gestión de préstamos personales. Permite registrar préstamos, actualizar pagos, listar préstamos y descargar un respaldo en CSV compatible con Excel. Todos los datos se almacenan en una base de datos local SQLite.

## Características Principales

*   **Registro de Préstamos**: El bot guía al usuario paso a paso para ingresar el monto y la fecha del préstamo.
*   **Actualización de Pagos**: Permite registrar pagos sobre préstamos existentes.
*   **Listado de Préstamos**: Muestra todos los préstamos registrados.
*   **Backup CSV**: Permite descargar todos los préstamos en formato CSV para abrir en Excel.
*   **Menú con Botones**: El usuario puede operar el bot usando botones con emojis para una experiencia más intuitiva.
*   **Gestión Segura de Credenciales**: Utiliza archivos `.env` para manejar información sensible.

## Tecnologías Utilizadas

*   **Python 3**
*   **python-telegram-bot**: Para la interacción con la API de Telegram.
*   **sqlite3**: Para la base de datos local.
*   **python-dotenv**: Para la gestión de variables de entorno.

## Prerrequisitos

*   Python 3.7 o superior.
*   `pip` (gestor de paquetes de Python).
*   `git` (para clonar el repositorio).
*   Una cuenta de Telegram y un token de Bot.

## Instalación

1. Clona el repositorio en tu servidor o PC:
    ```bash
    git clone https://github.com/sysdevfiles/loanbot.git /root/ControlPréstamos
    cd /root/ControlPréstamos
    ```

2. Ejecuta el script de instalación:
    ```bash
    bash setup.sh
    ```

3. Sigue las instrucciones para configurar el archivo `.env` con tu token de Telegram.

4. Activa el entorno virtual y ejecuta el bot:
    ```bash
    source venv/bin/activate
    python3 main.py
    ```

## Comandos y Menú

El bot puede usarse tanto con comandos como con botones del menú:

- **/start** — Muestra el menú principal.
- **📝 Nuevo Préstamo** — Inicia el registro guiado de un nuevo préstamo.
- **💳 Pagar Cuota** — Muestra la instrucción para registrar un pago (`/pay <ID_Préstamo> <MontoPagado>`).
- **📋 Listar Préstamos** — Muestra todos los préstamos registrados.
- **💾 Backup CSV** — Descarga un respaldo de todos los préstamos en formato CSV.
- **/cancel** — Cancela el registro de un préstamo en cualquier momento.

## Estructura del Proyecto

```
/root/ControlPréstamos/
├── .env                   # Variables de entorno (NO subir a Git)
├── .gitignore             # Archivos a ignorar por Git
├── main.py                # Lógica principal del bot
├── requirements.txt       # Dependencias de Python
├── setup.sh               # Script de instalación para Linux
├── venv/                  # Entorno virtual (ignorado por Git)
├── README.md              # Este archivo
└── loans.db               # Base de datos SQLite (ignorado por Git, creado en ejecución)
```

## Notas

- El bot ya **no utiliza Google Sheets** ni OAuth, solo SQLite local.
- El backup CSV se puede abrir directamente en Excel.
- Puedes personalizar los campos del préstamo modificando el flujo de conversación en `main.py`.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o un pull request.
