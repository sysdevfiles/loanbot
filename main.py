import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, Filters, ContextTypes
import sqlite3 # Assuming you use this for local DB

# Import Google Sheets integration functions
from google_sheets_integration import (
    init_gspread_client,
    add_loan_to_sheet,
    update_loan_in_sheet,
    get_all_loans_from_sheet
)

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_ADMIN_ID = os.getenv('TELEGRAM_ADMIN_ID') # Cargar el Admin ID
DATABASE_NAME = os.getenv('DATABASE_NAME', 'loans.db')

# Initialize Google Sheets worksheet
gsheet_worksheet = None

# ... (Your existing database setup and helper functions for SQLite) ...

# Example: Function to connect to SQLite (adapt as needed)
def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# Example: Function to add a loan to SQLite (adapt as needed)
def db_add_loan(loan_id, user_id, user_name, amount, status, paid_amount, creation_date):
    # This is a placeholder for your actual SQLite loan adding logic
    print(f"Adding loan {loan_id} to SQLite for user {user_name}...")
    # conn = get_db_connection()
    # cursor = conn.cursor()
    # cursor.execute("INSERT INTO loans (id, user_id, user_name, ...) VALUES (?, ?, ?, ...)", 
    #                (loan_id, user_id, user_name, ...))
    # conn.commit()
    # conn.close()
    return True # Return True on success

# Example: Function to update loan status in SQLite (adapt as needed)
def db_update_loan_status(loan_id, new_status, new_paid_amount):
    # This is a placeholder for your actual SQLite loan update logic
    print(f"Updating loan {loan_id} in SQLite to status {new_status}, paid {new_paid_amount}...")
    # conn = get_db_connection()
    # cursor = conn.cursor()
    # cursor.execute("UPDATE loans SET status = ?, paid_amount = ? WHERE id = ?", 
    #                (new_status, new_paid_amount, loan_id))
    # conn.commit()
    # conn.close()
    return True # Return True on success


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '👋 ¡Hola! Soy tu bot de gestión de préstamos.\n\n'
        'Aquí tienes los comandos disponibles:\n'
        '📝 /nuevoprestamo - Registrar un nuevo préstamo.\n'
        '💳 /pagarcuota - Registrar un pago de cuota.\n'
        '📊 /listarprestamos - Ver todos los préstamos.\n'
        '👥 /listarclientes - Ver un resumen de clientes.\n'
        '✅ /clientespagaron - Ver clientes con préstamos totalmente pagados.\n'
        '⏳ /clientesnopagaron - Ver clientes con pagos pendientes.'
    )

# --- Example command for creating a loan ---
async def new_loan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Dummy data for demonstration
    # In a real scenario, you'd collect this data from the user
    user = update.effective_user
    loan_id = f"L{user.id}{len(context.bot_data.get('loans', [])) + 1}" # Simple unique ID
    borrower_id = str(user.id)
    borrower_name = user.full_name
    amount = 1000.00 # Example amount
    status = "Pendiente"
    paid_amount = 0.00
    creation_date = "2024-07-25" # Example date

    # Add to SQLite (your existing logic)
    if db_add_loan(loan_id, borrower_id, borrower_name, amount, status, paid_amount, creation_date):
        await update.message.reply_text(f"Préstamo {loan_id} registrado localmente.")

        # Add to Google Sheets
        if gsheet_worksheet:
            loan_data_for_sheet = [loan_id, borrower_id, borrower_name, amount, status, paid_amount, creation_date]
            if add_loan_to_sheet(gsheet_worksheet, loan_data_for_sheet):
                await update.message.reply_text(f"Préstamo {loan_id} también almacenado en Google Sheets.")
            else:
                await update.message.reply_text(f"Error al guardar préstamo {loan_id} en Google Sheets.")
        else:
            await update.message.reply_text("Integración con Google Sheets no está activa.")
    else:
        await update.message.reply_text("Error al registrar el préstamo localmente.")


# --- Example command for updating a loan (e.g., after a payment) ---
async def pay_loan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Dummy data for demonstration
    # Args: /pay <loan_id> <payment_amount>
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Uso: /pay <ID_Préstamo> <MontoPagado>")
            return
        
        loan_id_to_update = args[0]
        payment = float(args[1]) # This would be the new total paid amount or just the payment

        # This is a simplified example. You'd fetch current paid amount and add to it.
        new_paid_amount = payment # Assuming this is the new total paid amount
        new_status = "Parcialmente Pagado" # Or "Pagado" if full amount

        # Update in SQLite (your existing logic)
        if db_update_loan_status(loan_id_to_update, new_status, new_paid_amount):
            await update.message.reply_text(f"Pago para préstamo {loan_id_to_update} actualizado localmente.")

            # Update in Google Sheets
            if gsheet_worksheet:
                if update_loan_in_sheet(gsheet_worksheet, loan_id_to_update, new_status, new_paid_amount):
                    await update.message.reply_text(f"Préstamo {loan_id_to_update} también actualizado en Google Sheets.")
                else:
                    await update.message.reply_text(f"Error al actualizar préstamo {loan_id_to_update} en Google Sheets.")
            else:
                await update.message.reply_text("Integración con Google Sheets no está activa.")
        else:
            await update.message.reply_text(f"Error al actualizar el pago para {loan_id_to_update} localmente.")

    except (IndexError, ValueError) as e:
        await update.message.reply_text(f"Error en el comando. Uso: /pay <ID_Préstamo> <MontoPagado>. Detalle: {e}")


# --- New command to list loans from Google Sheets ---
async def list_loans_sheet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Paso 1 (implícito): gsheet_worksheet ya debería estar inicializado.
    # Se verifica si gsheet_worksheet es None.
    if not gsheet_worksheet:
        await update.message.reply_text("La integración con Google Sheets no está activa o falló al iniciar.")
        return

    # Paso 2: Llamada a la función de obtención de datos.
    loans = get_all_loans_from_sheet(gsheet_worksheet)
    if not loans:
        await update.message.reply_text("No se encontraron préstamos en Google Sheets o hubo un error al leerlos.")
        return

    # Paso 3: Procesamiento y presentación de los datos.
    response_message = "Préstamos desde Google Sheets:\n\n"
    for loan in loans:
        # loan es un diccionario, ej: {'ID Préstamo': 'L001', 'Monto': 1000, ...}
        response_message += (
            f"ID: {loan.get('ID Préstamo', 'N/A')}, "
            f"Prestatario: {loan.get('Nombre Prestatario', 'N/A')}, "
            f"Monto: {loan.get('Monto', 'N/A')}, "
            f"Estado: {loan.get('Estado', 'N/A')}, "
            f"Pagado: {loan.get('Monto Pagado', 'N/A')}\n"
        )
    
    if len(response_message) > 4096: # Telegram message limit
        await update.message.reply_text("La lista de préstamos es muy larga. Se mostrarán los primeros.")
        # Consider pagination or sending as a file for very long lists
        response_message = response_message[:4000] + "\n... (lista truncada)"
        
    await update.message.reply_text(response_message)


def main():
    global gsheet_worksheet
    
    # Obtener configuración de Google Sheets desde .env o interactivamente
    # Usa la nueva variable para el archivo de credenciales OAuth
    creds_file_path = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET_FILE') 
    sheet_name_val = os.getenv('GOOGLE_SHEET_NAME')
    worksheet_name_val = os.getenv('GOOGLE_SHEET_WORKSHEET_NAME')

    print("Configuración de Google Sheets (usando OAuth 2.0):")
    if not creds_file_path:
        creds_file_path = input("Ruta al archivo JSON de credenciales de cliente OAuth 2.0 (ej. config/client_secret_XXXX.json): ").strip()
    else:
        print(f"  Ruta de credenciales OAuth (desde .env): {creds_file_path}")

    # Initialize Google Sheets client
    print("\nInicializando cliente de Google Sheets (OAuth)...")
    # La función init_gspread_client ahora espera la ruta del archivo de credenciales OAuth
    gsheet_worksheet = init_gspread_client(creds_file_path, sheet_name_val, worksheet_name_val) 
    
    if gsheet_worksheet:
        print("Cliente de Google Sheets inicializado correctamente.")
    else:
        print("Error al inicializar Google Sheets. Revise la configuración proporcionada y los mensajes de error.")
        # Podrías decidir si el bot debe continuar sin la integración de Sheets o salir.
        # Por ahora, continuará, pero las funciones de Sheets no funcionarán.

    # ... (Your existing bot setup) ...
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    # Add your other command handlers here
    application.add_handler(CommandHandler("newloan", new_loan_command)) # Example
    application.add_handler(CommandHandler("pay", pay_loan_command))     # Example
    application.add_handler(CommandHandler("listloanssheet", list_loans_sheet_command))


    print("Bot iniciado. Presiona Ctrl+C para detener.")
    application.run_polling()

if __name__ == '__main__':
    main()
