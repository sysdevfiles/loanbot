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

echo -e "${CYAN}Limpiando posibles residuos de instalaciones anteriores...${NC}"
# Eliminar entorno virtual anterior si existe
if [ -d "venv" ]; then
    rm -rf venv
fi
# Eliminar base de datos anterior si existe
if [ -f "loans.db" ]; then
    rm -f loans.db
fi
# Eliminar archivo .env anterior si existe
if [ -f ".env" ]; then
    rm -f .env
fi
# Eliminar servicio systemd anterior si existe
if [ -f "/etc/systemd/system/loanbot.service" ]; then
    systemctl stop loanbot.service >/dev/null 2>&1
    systemctl disable loanbot.service >/dev/null 2>&1
    rm -f /etc/systemd/system/loanbot.service
    systemctl daemon-reload
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
    pip3 install -r requirements.txt
    # Instalar el paquete de desarrollo de SQLite si no está presente (para Python)
    if ! python3 -c "import sqlite3" 2>/dev/null; then
        echo -e "${YELLOW}sqlite3 no encontrado en Python. Intentando instalar dependencias del sistema...${NC}"
        apt-get update
        apt-get install -y libsqlite3-dev
        # Recomendar reinstalar Python si sigue sin funcionar
    fi
    echo -e "${GREEN}Intento de instalación de dependencias completado.${NC}"
else
    echo -e "${RED}Error: ¡requirements.txt no encontrado!${NC}"
    exit 1
fi

# Paso G: Configurar el archivo .env interactivamente (antes era Paso 6, ahora es un paso intermedio)
echo -e "\n${CYAN}[Paso G/H] Configurando archivo .env...${NC}"
env_file_path="${PROJECT_PATH}/.env" # Ruta al archivo .env dentro del proyecto clonado

prompt_telegram_token_text="${YELLOW}Ingresa tu TELEGRAM_BOT_TOKEN: ${NC}"
prompt_telegram_admin_id_text="${YELLOW}Ingresa tu TELEGRAM_ADMIN_ID (opcional, para comandos de administrador): ${NC}"

echo -e "$prompt_telegram_token_text"
read telegram_bot_token

echo -e "$prompt_telegram_admin_id_text"
read telegram_admin_id

echo -e "${CYAN}Creando/Actualizando archivo '$env_file_path'...${NC}"
cat << EOF > "$env_file_path"
TELEGRAM_BOT_TOKEN=${telegram_bot_token}
TELEGRAM_ADMIN_ID=${telegram_admin_id}
DATABASE_NAME=loans.db
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Archivo .env creado/actualizado exitosamente en '$env_file_path'.${NC}"
    echo -e "${YELLOW}DATABASE_NAME se ha establecido a 'loans.db' por defecto.${NC}"
    if [ -n "$telegram_admin_id" ]; then
        echo -e "${YELLOW}TELEGRAM_ADMIN_ID configurado como: ${telegram_admin_id}${NC}"
    fi
else
    echo -e "${RED}Error al crear/actualizar el archivo .env.${NC}"
fi

# Paso H: Configurar el servicio systemd interactivamente (antes Paso G, ahora H)
echo -e "\n${CYAN}[Paso H/H] Configuración del servicio systemd...${NC}"
SERVICE_FILE_PATH="/etc/systemd/system/loanbot.service"
current_project_path=$(pwd)
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
systemctl daemon-reload
systemctl enable loanbot.service

echo -e "${GREEN}Servicio loanbot habilitado para iniciar con el sistema.${NC}"
echo -e "${YELLOW}Puedes iniciar el bot con: systemctl start loanbot.service${NC}"
echo -e "${YELLOW}Verifica el estado con: systemctl status loanbot.service${NC}"

echo -e "\n${GREEN}=== ¡Configuración Básica Completada en '$PROJECT_PATH'! ===${NC}"
echo -e "${GREEN}Entorno virtual 'venv' creado, dependencias instaladas, base de datos limpia, archivo '.env' configurado y servicio systemd listo.${NC}"

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
