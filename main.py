import logging
import os
import sqlite3
import csv
from dotenv import load_dotenv
from telegram import Update, InputFile, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'loans.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id TEXT UNIQUE,
            user_id TEXT,
            user_name TEXT,
            amount REAL,
            status TEXT,
            paid_amount REAL,
            creation_date TEXT
        )
    """)
    conn.commit()
    conn.close()

def db_add_loan(loan_id, user_id, user_name, amount, status, paid_amount, creation_date):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO loans (loan_id, user_id, user_name, amount, status, paid_amount, creation_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (loan_id, user_id, user_name, amount, status, paid_amount, creation_date))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding loan: {e}")
        return False

def db_update_loan_status(loan_id, new_status, new_paid_amount):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE loans SET status = ?, paid_amount = ? WHERE loan_id = ?
        """, (new_status, new_paid_amount, loan_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating loan: {e}")
        return False

def db_get_all_loans():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM loans")
    rows = cursor.fetchall()
    conn.close()
    return rows

MAIN_MENU = [
    [KeyboardButton("📝 Nuevo Préstamo"), KeyboardButton("💳 Pagar Cuota")],
    [KeyboardButton("📋 Listar Préstamos"), KeyboardButton("💾 Backup CSV")]
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Recibido /start")
    help_msg = (
        "🤖 <b>Bienvenido al Bot de Préstamos</b>\n\n"
        "Selecciona una opción del menú o usa los comandos:\n"
        "📝 /nuevoprestamo - Registrar un nuevo préstamo\n"
        "💳 /pay - Registrar un pago\n"
        "📋 /listarprestamos - Ver todos los préstamos\n"
        "💾 /backup - Descargar respaldo en CSV\n\n"
        "<b>Comandos útiles para el servicio:</b>\n"
        "<code>systemctl start loanbot.service</code> - Iniciar el bot\n"
        "<code>systemctl stop loanbot.service</code> - Detener el bot\n"
        "<code>systemctl restart loanbot.service</code> - Reiniciar el bot\n"
        "<code>systemctl status loanbot.service</code> - Ver estado del bot\n"
        "<code>systemctl enable loanbot.service</code> - Habilitar inicio automático\n"
        "<code>systemctl disable loanbot.service</code> - Deshabilitar inicio automático\n"
        "<code>systemctl daemon-reload</code> - Recargar configuración de systemd\n"
        "<code>journalctl -u loanbot.service -f</code> - Ver logs en tiempo real\n"
    )
    await update.message.reply_text(
        help_msg,
        reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True),
        parse_mode="HTML"
    )

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if (text == "📝 Nuevo Préstamo"):
        await new_loan_command(update, context)
    elif (text == "💳 Pagar Cuota"):
        await update.message.reply_text("Usa el comando: /pay <ID_Préstamo> <MontoPagado> 💳")
    elif (text == "📋 Listar Préstamos"):
        await list_loans_command(update, context)
    elif (text == "💾 Backup CSV"):
        await backup_command(update, context)
    else:
        await update.message.reply_text("Por favor, selecciona una opción del menú.")

async def new_loan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    loan_id = f"L{user.id}{len(db_get_all_loans()) + 1}"
    borrower_id = str(user.id)
    borrower_name = user.full_name
    amount = 1000.00
    status = "Pendiente"
    paid_amount = 0.00
    creation_date = "2024-07-25"
    if db_add_loan(loan_id, borrower_id, borrower_name, amount, status, paid_amount, creation_date):
        await update.message.reply_text(f"✅ Préstamo {loan_id} registrado en la base de datos.")
    else:
        await update.message.reply_text("❌ Error al registrar el préstamo.")

async def pay_loan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Uso: /pay <ID_Préstamo> <MontoPagado> 💳")
            return
        loan_id_to_update = args[0]
        payment = float(args[1])
        new_paid_amount = payment
        new_status = "Parcialmente Pagado"
        if db_update_loan_status(loan_id_to_update, new_status, new_paid_amount):
            await update.message.reply_text(f"💰 Pago para préstamo {loan_id_to_update} actualizado.")
        else:
            await update.message.reply_text(f"❌ Error al actualizar el pago para {loan_id_to_update}.")
    except (IndexError, ValueError) as e:
        await update.message.reply_text(f"Error en el comando. Uso: /pay <ID_Préstamo> <MontoPagado>. Detalle: {e}")

async def list_loans_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loans = db_get_all_loans()
    if not loans:
        await update.message.reply_text("📋 No hay préstamos registrados.")
        return
    msg = "📋 <b>Préstamos registrados:</b>\n\n"
    for loan in loans:
        msg += (
            f"🆔 {loan['loan_id']} | 👤 {loan['user_name']} | 💵 {loan['amount']} | "
            f"📅 {loan['creation_date']} | 🏷️ {loan['status']} | 💸 {loan['paid_amount']}\n"
        )
    await update.message.reply_text(msg[:4096], parse_mode="HTML")

async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loans = db_get_all_loans()
    if not loans:
        await update.message.reply_text("No hay datos para respaldar.")
        return
    csv_path = "loans_backup.csv"
    with open(csv_path, "w", newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["ID", "Loan ID", "User ID", "User Name", "Amount", "Status", "Paid Amount", "Creation Date"])
        for loan in loans:
            writer.writerow([
                loan["id"], loan["loan_id"], loan["user_id"], loan["user_name"],
                loan["amount"], loan["status"], loan["paid_amount"], loan["creation_date"]
            ])
    with open(csv_path, "rb") as f:
        await update.message.reply_document(document=InputFile(f, filename=csv_path))
    os.remove(csv_path)

# Estados para el registro de préstamo
ASK_AMOUNT, ASK_DATE = range(2)

async def new_loan_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 Ingresa el monto del préstamo:")
    return ASK_AMOUNT

async def new_loan_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.replace(",", "."))
        context.user_data["amount"] = amount
        await update.message.reply_text("📅 Ingresa la fecha del préstamo (YYYY-MM-DD):")
        return ASK_DATE
    except ValueError:
        await update.message.reply_text("❌ Monto inválido. Ingresa solo números:")
        return ASK_AMOUNT

async def new_loan_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date = update.message.text.strip()
    user = update.effective_user
    loans = db_get_all_loans()
    loan_id = f"L{user.id}{len(loans) + 1}"
    borrower_id = str(user.id)
    borrower_name = user.full_name
    amount = context.user_data["amount"]
    status = "Pendiente"
    paid_amount = 0.0
    creation_date = date
    if db_add_loan(loan_id, borrower_id, borrower_name, amount, status, paid_amount, creation_date):
        await update.message.reply_text(f"✅ Préstamo {loan_id} registrado: 💵 {amount} | 📅 {date}")
    else:
        await update.message.reply_text("❌ Error al registrar el préstamo.")
    return ConversationHandler.END

async def new_loan_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registro de préstamo cancelado.")
    return ConversationHandler.END

def main():
    init_db()
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Conversación para registro de préstamo
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("nuevoprestamo", new_loan_start), MessageHandler(filters.Regex("^📝 Nuevo Préstamo$"), new_loan_start)],
        states={
            ASK_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, new_loan_amount)],
            ASK_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, new_loan_date)],
        },
        fallbacks=[CommandHandler("cancel", new_loan_cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("pay", pay_loan_command))
    application.add_handler(CommandHandler("listarprestamos", list_loans_command))
    application.add_handler(CommandHandler("backup", backup_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_menu))
    print("Bot iniciado. Presiona Ctrl+C para detener.")
    application.run_polling()

if __name__ == '__main__':
    main()
