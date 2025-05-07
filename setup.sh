#!/bin/bash

# Definir colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # Sin Color

# Variables del Repositorio
REPO_URL="https://github.com/sysdevfiles/loanbot.git"
PROJECT_DIR_NAME="ControlPréstamos" # Nombre del directorio donde se clonará el proyecto
# Fijar la ruta padre para la clonación a /root
CLONE_PARENT_DIR="/root"

echo -e "${CYAN}=== Iniciando Configuración del Bot de Gestión de Préstamos para Ubuntu (como root) ===${NC}"

# Paso A: Verificar Git y Clonar Repositorio
echo -e "\n${CYAN}[Paso A/7] Verificando instalación de Git...${NC}"
if ! command -v git &> /dev/null
then
    echo -e "${YELLOW}Git no encontrado. Intentando instalar git...${NC}"
    apt-get update # Sin sudo, asumiendo root
    apt-get install -y git # Sin sudo, asumiendo root
    if ! command -v git &> /dev/null
    then
        echo -e "${RED}Error: Falló la instalación de Git.${NC}"
        echo -e "${YELLOW}Por favor, instálalo manualmente (ej. apt install git) y re-ejecuta este script.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Git instalado correctamente.${NC}"
else
    echo -e "${GREEN}Git encontrado.${NC}"
fi

# Ya no se pregunta al usuario dónde clonar, se usa CLONE_PARENT_DIR="/root"
# current_dir=$(pwd)
# default_clone_parent_dir="$current_dir" 
# read -p "$(echo -e ${YELLOW}Ingresa la ruta absoluta del directorio padre donde deseas clonar el proyecto '$PROJECT_DIR_NAME' [${default_clone_parent_dir}]: ${NC})" clone_parent_dir
# clone_parent_dir="${clone_parent_dir:-$default_clone_parent_dir}"

echo -e "${CYAN}El proyecto se clonará en el directorio padre: ${CLONE_PARENT_DIR}${NC}"

# Asegurarse de que el directorio padre para la clonación exista
if [ ! -d "$CLONE_PARENT_DIR" ]; then
    echo -e "${CYAN}El directorio padre para la clonación '$CLONE_PARENT_DIR' no existe. Intentando crearlo...${NC}"
    mkdir -p "$CLONE_PARENT_DIR"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: No se pudo crear el directorio padre para la clonación '$CLONE_PARENT_DIR'. Verifica los permisos.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Directorio padre '$CLONE_PARENT_DIR' creado exitosamente.${NC}"
fi

PROJECT_PATH="${CLONE_PARENT_DIR}/${PROJECT_DIR_NAME}"

if [ -d "$PROJECT_PATH" ]; then
    echo -e "${YELLOW}El directorio del proyecto '$PROJECT_PATH' ya existe.${NC}"
    echo -e "${YELLOW}¿Deseas eliminarlo y volver a clonar para una instalación completamente limpia? (yes/no): ${NC}"
    read re_clone
    if [[ "$re_clone" =~ ^([Yy]([Ee][Ss])?)$ ]]; then # Check for y, Y, yes, Yes, YES
        echo -e "${CYAN}Eliminando directorio existente '$PROJECT_PATH'...${NC}"
        rm -rf "$PROJECT_PATH"
        echo -e "${CYAN}Clonando repositorio '$REPO_URL' en '$PROJECT_PATH'...${NC}"
        git clone "$REPO_URL" "$PROJECT_PATH"
        if [ $? -ne 0 ]; then
            echo -e "${RED}Error: Falló la clonación del repositorio.${NC}"
            exit 1
        fi
        echo -e "${GREEN}Repositorio clonado exitosamente en '$PROJECT_PATH'.${NC}"
    else
        echo -e "${YELLOW}Usando el directorio existente '$PROJECT_PATH'. Se intentará limpiar el entorno virtual si existe.${NC}"
    fi
else
    echo -e "${CYAN}Clonando repositorio '$REPO_URL' en '$PROJECT_PATH'...${NC}"
    git clone "$REPO_URL" "$PROJECT_PATH"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Falló la clonación del repositorio.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Repositorio clonado exitosamente en '$PROJECT_PATH'.${NC}"
fi

echo -e "${CYAN}Cambiando al directorio del proyecto: '$PROJECT_PATH'...${NC}"
cd "$PROJECT_PATH"
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: No se pudo cambiar al directorio del proyecto '$PROJECT_PATH'.${NC}"
    exit 1
fi
echo -e "${GREEN}Directorio actual: $(pwd)${NC}"

# Limpiar venv preexistente si no se re-clonó y existe
if ! [[ "$re_clone" =~ ^([Yy]([Ee][Ss])?)$ ]] && [ -d "venv" ]; then # Updated condition
    echo -e "${YELLOW}Directorio 'venv' existente encontrado. Eliminándolo para una instalación limpia del entorno virtual...${NC}"
    rm -rf "venv"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error al eliminar el directorio 'venv' existente. Puede que necesites hacerlo manualmente.${NC}"
    else
        echo -e "${GREEN}Directorio 'venv' anterior eliminado.${NC}"
    fi
fi

# Paso 1: Verificar Python (ahora Paso B)
echo -e "\n${CYAN}[Paso B/7] Verificando instalación de Python 3...${NC}"
if ! command -v python3 &> /dev/null
then
    echo -e "${RED}Error: Python 3 no encontrado.${NC}"
    echo -e "${YELLOW}Por favor, instálalo con: apt update && apt install python3${NC}"
    exit 1
fi
echo -e "${GREEN}Python 3 encontrado.${NC}"

# Paso 2: Verificar pip3 (ahora Paso C)
echo -e "\n${CYAN}[Paso C/7] Verificando instalación de pip3...${NC}"
if ! command -v pip3 &> /dev/null
then
    echo -e "${YELLOW}pip3 no encontrado. Intentando instalar python3-pip...${NC}"
    apt-get update # Sin sudo, asumiendo root
    apt-get install -y python3-pip # Sin sudo, asumiendo root
    
    if ! command -v pip3 &> /dev/null
    then
        echo -e "${RED}Error: Falló la instalación de pip3.${NC}"
        echo -e "${YELLOW}Por favor, instálalo manualmente (ej. apt install python3-pip) y re-ejecuta este script.${NC}"
        exit 1
    fi
    echo -e "${GREEN}pip3 instalado correctamente.${NC}"
else
    echo -e "${GREEN}pip3 encontrado.${NC}"
fi

# Paso 3: Crear entorno virtual (ahora Paso D)
echo -e "\n${CYAN}[Paso D/7] Creando entorno virtual 'venv' en $(pwd)/venv...${NC}"
python3 -m venv venv
echo -e "${GREEN}Entorno virtual 'venv' creado.${NC}"

# Activar el entorno virtual
# Nota: La activación del venv aquí es para este script. El servicio systemd usará la ruta absoluta al python del venv.
echo -e "\n${CYAN}Activando entorno virtual para la sesión actual del script...${NC}"
source venv/bin/activate
echo -e "${GREEN}Entorno virtual activado para esta sesión.${NC}"

# Paso 4: Actualizar pip (ahora Paso E)
echo -e "\n${CYAN}[Paso E/7] Actualizando pip...${NC}"
pip3 install --upgrade pip # Asegurando el uso explícito de pip3
echo -e "${GREEN}pip actualizado correctamente.${NC}"

# Paso 5: Instalar dependencias (ahora Paso F)
echo -e "\n${CYAN}[Paso F/7] Instalando dependencias desde requirements.txt...${NC}"
if [ -f requirements.txt ]; then
    pip3 install -r requirements.txt # Asegurando el uso explícito de pip3
    # El script continuará incluso si hay un error aquí (como con sqlite3)
    # Es importante que el requirements.txt en el repo esté correcto.
    echo -e "${GREEN}Intento de instalación de dependencias completado.${NC}"
    echo -e "${YELLOW}Nota: Si ves errores relacionados con 'sqlite3', debes eliminarlo del archivo 'requirements.txt' en tu repositorio de GitHub.${NC}"
else
    echo -e "${RED}Error: ¡requirements.txt no encontrado!${NC}"
    # No es necesario desactivar aquí si el script va a salir.
    exit 1
fi

# Paso G: Configurar el archivo .env interactivamente (antes era Paso 6, ahora es un paso intermedio)
echo -e "\n${CYAN}[Paso G/H] Configurando archivo .env y creando archivo de credenciales JSON...${NC}"
env_file_path="${PROJECT_PATH}/.env" # Ruta al archivo .env dentro del proyecto clonado

# Valores por defecto o vacíos
# default_db_name="loans.db" # No longer asking, will be set directly
default_google_sheet_name="Registro" # Default sheet name
default_google_worksheet_name="ControlPréstamos" # Default worksheet name
# Default path for the OAuth client secret JSON file
default_google_oauth_secret_file="config/client_secret_oauth.json" # Nombre genérico para el archivo que creará el script

# Corregir la sintaxis de read -p. No se necesita $(echo -e ...) para el prompt.
# Simplemente se usa la cadena directamente con -e para interpretar escapes si es necesario con bash,
# o se pueden poner los códigos de color directamente en la cadena.
# Para mayor portabilidad y simplicidad, se pueden definir las cadenas de prompt antes.

prompt_telegram_token_text="${YELLOW}Ingresa tu TELEGRAM_BOT_TOKEN: ${NC}"
prompt_telegram_admin_id_text="${YELLOW}Ingresa tu TELEGRAM_ADMIN_ID (opcional, para comandos de administrador): ${NC}"
prompt_google_sheet_name_text="${YELLOW}Nombre de tu Hoja de Cálculo de Google (Spreadsheet Name) [${default_google_sheet_name}]: ${NC}"
prompt_google_worksheet_name_text="${YELLOW}Nombre de la Hoja de Trabajo específica (Worksheet Name) [${default_google_worksheet_name}]: ${NC}"
prompt_google_oauth_file_path_text="${YELLOW}Ruta donde se creará el archivo JSON para tus credenciales de cliente OAuth 2.0 (relativa al proyecto, ej. ${default_google_oauth_secret_file}) [${default_google_oauth_secret_file}]: ${NC}"

echo -e "$prompt_telegram_token_text"
read telegram_bot_token

echo -e "$prompt_telegram_admin_id_text"
read telegram_admin_id

# No longer asking for database_name
echo -e "$prompt_google_sheet_name_text"
read google_sheet_name
google_sheet_name="${google_sheet_name:-$default_google_sheet_name}"

echo -e "$prompt_google_worksheet_name_text"
read google_worksheet_name
google_worksheet_name="${google_worksheet_name:-$default_google_worksheet_name}"

echo -e "$prompt_google_oauth_file_path_text"
read google_oauth_client_secret_file_to_create
google_oauth_client_secret_file_to_create="${google_oauth_client_secret_file_to_create:-$default_google_oauth_secret_file}"

# Crear el directorio para el archivo JSON si no existe
google_oauth_secret_file_full_path="${PROJECT_PATH}/${google_oauth_client_secret_file_to_create}"
google_oauth_secret_dir=$(dirname "$google_oauth_secret_file_full_path")

if [ ! -d "$google_oauth_secret_dir" ]; then
    echo -e "${CYAN}Creando directorio para el archivo de credenciales: $google_oauth_secret_dir...${NC}"
    mkdir -p "$google_oauth_secret_dir"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: No se pudo crear el directorio $google_oauth_secret_dir.${NC}"
        echo -e "${YELLOW}Por favor, crea este directorio manualmente y re-ejecuta el script, o verifica los permisos.${NC}"
        # Considerar salir del script o continuar sin crear el archivo JSON
        # exit 1; # Podrías añadir un exit si es crítico
    fi
fi

# Crear un archivo JSON vacío o con estructura mínima para que el usuario lo edite
echo -e "${CYAN}Creando archivo JSON base en '$google_oauth_secret_file_full_path' para que pegues tus credenciales...${NC}"
cat << EOF_JSON_BASE > "$google_oauth_secret_file_full_path"
{
  "installed": {
    "client_id": "TU_CLIENT_ID_AQUI",
    "project_id": "TU_PROJECT_ID_AQUI",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "TU_CLIENT_SECRET_AQUI",
    "redirect_uris": ["http://localhost"]
  }
}
EOF_JSON_BASE

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Archivo JSON base creado exitosamente en '$google_oauth_secret_file_full_path'.${NC}"
    echo -e "${YELLOW}Se abrirá nano para que pegues el contenido de tu JSON de credenciales OAuth 2.0 descargado de Google Cloud Console.${NC}"
    echo -e "${YELLOW}Pega el contenido, guarda los cambios (Ctrl+O, Enter) y cierra nano (Ctrl+X) para continuar.${NC}"
    
    # Abrir nano para editar el archivo
    if command -v nano &> /dev/null; then
        nano "$google_oauth_secret_file_full_path"
        echo -e "${GREEN}Edición de archivo JSON completada.${NC}"
    else
        echo -e "${RED}Comando 'nano' no encontrado. Por favor, edita el archivo manualmente:${NC}"
        echo -e "${GREEN}\"$google_oauth_secret_file_full_path\"${NC}"
        echo -e "${YELLOW}Luego presiona Enter para continuar...${NC}"
        read # Pausa para edición manual si nano no está
    fi
else
    echo -e "${RED}Error al crear el archivo JSON base en '$google_oauth_secret_file_full_path'.${NC}"
fi

echo -e "${CYAN}Creando/Actualizando archivo '$env_file_path'...${NC}"
cat << EOF > "$env_file_path"
TELEGRAM_BOT_TOKEN=${telegram_bot_token}
TELEGRAM_ADMIN_ID=${telegram_admin_id}
DATABASE_NAME=loans.db

# Google Sheets Integration
GOOGLE_SHEET_NAME="${google_sheet_name}"
GOOGLE_SHEET_WORKSHEET_NAME="${google_worksheet_name}"
GOOGLE_OAUTH_CLIENT_SECRET_FILE="${google_oauth_client_secret_file_to_create}"
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Archivo .env creado/actualizado exitosamente en '$env_file_path'.${NC}"
    echo -e "${YELLOW}DATABASE_NAME se ha establecido a 'loans.db' por defecto.${NC}"
    if [ -n "$telegram_admin_id" ]; then
        echo -e "${YELLOW}TELEGRAM_ADMIN_ID configurado como: ${telegram_admin_id}${NC}"
    fi
    echo -e "${YELLOW}La primera vez que ejecutes el bot, se te pedirá autorizar el acceso a Google Sheets/Drive a través de tu navegador, usando el archivo JSON recién creado.${NC}"
else
    echo -e "${RED}Error al crear/actualizar el archivo .env.${NC}"
fi

# Paso H: Configurar el servicio systemd interactivamente (antes Paso G, ahora H)
echo -e "\n${CYAN}[Paso H/H] Configuración del servicio systemd (Opcional Interactivo)...${NC}"
prompt_setup_service_text="${YELLOW}¿Deseas configurar el bot como un servicio systemd ahora? (yes/no): ${NC}" # Ensure this uses (yes/no)
echo -e "$prompt_setup_service_text"
read setup_service

if [[ "$setup_service" =~ ^([Yy]([Ee][Ss])?)$ ]]; then # Check for y, Y, yes, Yes, YES
    echo -e "${CYAN}Configurando el servicio systemd...${NC}"
    
    # Usar el directorio actual del proyecto clonado
    current_project_path=$(pwd)

    # Validar que la ruta exista y sea un directorio (debería serlo si el cd funcionó)
    if [ ! -d "$current_project_path" ]; then
        echo -e "${RED}Error: La ruta del proyecto actual '$current_project_path' no es válida.${NC}"
        echo -e "${YELLOW}La configuración del servicio systemd se omitirá. Puedes hacerlo manualmente más tarde.${NC}"
    else
        SERVICE_FILE_PATH="/etc/systemd/system/loanbot.service"
        # Limpiar servicio systemd preexistente
        if [ -f "$SERVICE_FILE_PATH" ]; then
            echo -e "${YELLOW}Servicio 'loanbot.service' existente encontrado en '$SERVICE_FILE_PATH'.${NC}"
            echo -e "${CYAN}Intentando detener y deshabilitar el servicio existente...${NC}"
            systemctl stop loanbot.service >/dev/null 2>&1 # Best effort, silenciar errores
            systemctl disable loanbot.service >/dev/null 2>&1 # Best effort, silenciar errores
            echo -e "${CYAN}Eliminando archivo de servicio anterior '$SERVICE_FILE_PATH'...${NC}"
            rm -f "$SERVICE_FILE_PATH"
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}Archivo de servicio anterior eliminado.${NC}"
            else
                echo -e "${RED}No se pudo eliminar el archivo de servicio anterior. Puede que necesites hacerlo manualmente.${NC}"
            fi
            echo -e "${CYAN}Recargando demonio de systemd después de eliminar el servicio anterior...${NC}"
            systemctl daemon-reload
        fi

        service_file_content="[Unit]
Description=Bot de Telegram para Gestión de Préstamos
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=${current_project_path}
ExecStart=${current_project_path}/venv/bin/python3 ${current_project_path}/main.py
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=loanbot

[Install]
WantedBy=multi-user.target"

        echo -e "${CYAN}Creando archivo de servicio en $SERVICE_FILE_PATH...${NC}"
        echo "$service_file_content" > "$SERVICE_FILE_PATH"
        write_status=$? # Capture the exit status of the echo command
        
        if [ "$write_status" -eq 0 ]; then # Check the captured status
            echo -e "${GREEN}Archivo de servicio creado exitosamente.${NC}"
            
            echo -e "${CYAN}Recargando demonio de systemd...${NC}"
            systemctl daemon-reload
            
            echo -e "${CYAN}Habilitando el servicio loanbot para que inicie en el arranque...${NC}"
            systemctl enable loanbot.service
            
            echo -e "${GREEN}Servicio loanbot habilitado.${NC}"

            echo -e "\n${YELLOW}ACCIÓN IMPORTANTE REQUERIDA AHORA PARA GOOGLE SHEETS:${NC}"
            echo -e "${YELLOW}Se ejecutará el bot ('main.py') interactivamente UNA VEZ para que autorices el acceso a Google Sheets.${NC}"
            echo -e "${YELLOW}Esto es necesario ANTES de que el servicio systemd pueda iniciar correctamente.${NC}"
            echo -e "${CYAN}Pasos a seguir:${NC}"
            echo -e "${CYAN}1. Cuando se te indique, sigue las instrucciones en la consola que aparecerán (probablemente abrir una URL en tu navegador y autorizar).${NC}"
            echo -e "${CYAN}2. Una vez que el bot confirme la conexión a Google Sheets y veas un mensaje como 'Bot iniciado. Presiona Ctrl+C para detener.' (o similar),${NC}"
            echo -e "${CYAN}   ${RED}PRESIONA Ctrl+C${CYAN} para detener esta ejecución manual. Esto devolverá el control a este script de configuración.${NC}"
            echo -e "${YELLOW}Presiona Enter para iniciar la ejecución manual de 'main.py' para la autorización...${NC}"
            read -r

            # Ejecutar main.py interactivamente para la autorización de Google.
            # El entorno virtual ya está activado para la sesión de este script.
            echo -e "${CYAN}Ejecutando 'python3 main.py' para autorización...${NC}"
            if ! python3 "${current_project_path}/main.py"; then
                # El usuario probablemente presionó Ctrl+C, lo cual es esperado.
                # El código de salida para Ctrl+C es 130. Otros errores podrían ser diferentes.
                # No trataremos esto como un error fatal del script setup.sh, ya que se espera Ctrl+C.
                echo -e "${YELLOW}Ejecución manual de 'main.py' detenida (Ctrl+C esperado después de la autorización).${NC}"
            else
                # Si main.py sale con código 0 (lo cual es inusual si está en modo polling), también lo registramos.
                echo -e "${GREEN}Ejecución manual de 'main.py' completada.${NC}"
            fi

            echo -e "\n${CYAN}Proceso de autorización manual completado.${NC}"
            echo -e "${CYAN}Intentando iniciar el servicio loanbot ahora para que corra en segundo plano...${NC}"
            systemctl start loanbot.service
            
            echo -e "${CYAN}Esperando unos segundos para que el servicio se estabilice...${NC}"
            sleep 5 # Espera 5 segundos

            if systemctl is-active --quiet loanbot.service; then
                echo -e "${GREEN}Servicio loanbot iniciado exitosamente y corriendo en segundo plano.${NC}"
            elif systemctl is-failed --quiet loanbot.service; then
                echo -e "${RED}Error: El servicio loanbot falló al iniciar después del intento de autorización.${NC}"
                echo -e "${YELLOW}Esto podría indicar que la autorización de Google no se completó correctamente o hay otro problema.${NC}"
                echo -e "${YELLOW}Revisa los logs con: journalctl -u loanbot.service -n 50${NC}"
                echo -e "${YELLOW}Si es necesario, detén el servicio (systemctl stop loanbot.service), ejecuta 'python3 main.py' manualmente de nuevo para asegurar la autorización, y luego reinicia el servicio (systemctl restart loanbot.service).${NC}"
            else
                echo -e "${YELLOW}El estado del servicio loanbot es incierto. Verifica manualmente con 'systemctl status loanbot.service'.${NC}"
                echo -e "${YELLOW}Si no funciona, asegúrate de que la autorización de Google se haya completado correctamente.${NC}"
            fi

            echo -e "\n${CYAN}Comandos útiles para gestionar el servicio loanbot:${NC}"
            echo -e "  ${GREEN}systemctl start loanbot.service${NC}    - Iniciar el servicio"
            echo -e "  ${GREEN}systemctl stop loanbot.service${NC}     - Detener el servicio"
            echo -e "  ${GREEN}systemctl restart loanbot.service${NC} - Reiniciar el servicio"
            echo -e "  ${GREEN}systemctl status loanbot.service${NC}   - Verificar el estado del servicio"
            echo -e "  ${GREEN}journalctl -u loanbot.service -f${NC}  - Ver los logs del servicio en tiempo real"
            echo -e "  ${GREEN}systemctl daemon-reload${NC}            - Recargar systemd (si modificas el archivo .service manualmente)"
            echo -e "\n${YELLOW}IMPORTANTE: Si el servicio falla repetidamente, asegúrate de haber completado la autorización de Google Sheets ejecutando 'python3 main.py' manualmente primero.${NC}"

        else
            echo -e "${RED}Error al crear el archivo de servicio. Verifica los permisos.${NC}"
            echo -e "${YELLOW}La configuración del servicio systemd se omitirá. Puedes hacerlo manualmente más tarde.${NC}"
        fi
    fi
else
    echo -e "${YELLOW}Configuración del servicio systemd omitida. Puedes crear un archivo 'loanbot.service' en '/etc/systemd/system/' manualmente.${NC}"
    echo -e "${YELLOW}Usa la siguiente plantilla y ajusta 'WorkingDirectory' y 'ExecStart' con la ruta absoluta a tu proyecto:"
    echo -e "${CYAN}----------------------------------------------------${NC}"
    echo -e "${CYAN}[Unit]${NC}"
    echo -e "${CYAN}Description=Bot de Telegram para Gestión de Préstamos${NC}"
    echo -e "${CYAN}After=network.target${NC}"
    echo -e ""
    echo -e "${CYAN}[Service]${NC}"
    echo -e "${CYAN}User=root${NC}"
    echo -e "${CYAN}Group=root${NC}"
    echo -e "${CYAN}WorkingDirectory=/ruta/absoluta/al/proyecto${NC}"
    echo -e "${CYAN}ExecStart=/ruta/absoluta/al/proyecto/venv/bin/python3 /ruta/absoluta/al/proyecto/main.py${NC}"
    echo -e "${CYAN}Restart=always${NC}"
    echo -e "${CYAN}RestartSec=10${NC}"
    echo -e "${CYAN}StandardOutput=syslog${NC}"
    echo -e "${CYAN}StandardError=syslog${NC}"
    echo -e "${CYAN}SyslogIdentifier=loanbot${NC}"
    echo -e ""
    echo -e "${CYAN}[Install]${NC}"
    echo -e "${CYAN}WantedBy=multi-user.target${NC}"
    echo -e "${CYAN}----------------------------------------------------${NC}"
    echo -e "${YELLOW}Luego ejecuta: systemctl daemon-reload && systemctl enable loanbot.service && systemctl start loanbot.service${NC}"
fi

echo -e "\n${GREEN}=== ¡Configuración Básica Completada en '$PROJECT_PATH'! ===${NC}"
echo -e "${GREEN}Entorno virtual 'venv' creado, dependencias instaladas y archivo '.env' configurado.${NC}"
echo -e "${GREEN}Se ha creado un archivo base para tus credenciales JSON en '${google_oauth_secret_file_full_path}'. Asegúrate de haberlo editado con tus credenciales reales.${NC}"

echo -e "\n${YELLOW}--- Próximos Pasos Detallados en README.md (dentro de '$PROJECT_PATH') ---${NC}"
echo -e "${CYAN}1.${NC} Revisa la sección ${YELLOW}'Instalación Detallada'${NC} en el archivo ${GREEN}README.md${NC} (ubicado en ${PROJECT_PATH}/README.md) para:"
echo -e "   - Verificar la configuración del archivo ${YELLOW}'.env'${NC} (en ${PROJECT_PATH}/.env)."
echo -e "   - Confirmar que hayas editado el archivo JSON de credenciales en ${GREEN}\"${google_oauth_secret_file_full_path}\"${NC} con tus datos reales usando un editor como nano."
echo -e "   - Asegurarte de que las APIs ${YELLOW}Google Sheets API y Google Drive API${NC} estén habilitadas en Google Cloud Console para el proyecto correspondiente a tus credenciales."
echo -e "   - ${GREEN}El script intentó guiarte a través de la autorización inicial de Google. Si el servicio systemd no funciona, revisa los logs y considera ejecutar 'python3 main.py' manualmente de nuevo en el directorio del proyecto para asegurar la autorización.${NC}"
echo ""
echo -e "${YELLOW}Para activar el entorno virtual en una nueva terminal, navega a '${PROJECT_PATH}' y usa: ${GREEN}source venv/bin/activate${NC}"
echo -e "${YELLOW}Para desactivar el entorno virtual (en la sesión actual del script, si aún está activa), escribe: ${GREEN}deactivate${NC}"
echo ""
