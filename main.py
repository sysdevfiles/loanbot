import logging
import os
import sqlite3
import csv
from datetime import datetime, timedelta
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
            client_name TEXT,
            amount REAL,
            interest REAL,
            payment_due_date TEXT,
            status TEXT,
            paid_amount REAL,
            creation_date TEXT
        )
    """)
    conn.commit()
    conn.close()

def db_add_loan(loan_id, user_id, user_name, client_name, amount, interest, payment_due_date, status, paid_amount, creation_date):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO loans (loan_id, user_id, user_name, client_name, amount, interest, payment_due_date, status, paid_amount, creation_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (loan_id, user_id, user_name, client_name, amount, interest, payment_due_date, status, paid_amount, creation_date))
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
    [KeyboardButton("📋 Listar Préstamos"), KeyboardButton("💾 Backup CSV")],
    [KeyboardButton("📊 Saldos")]
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Recibido /start")
    try:
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
    except Exception as e:
        print(f"Error enviando menú de /start: {e}")
        await update.message.reply_text("Ocurrió un error mostrando el menú principal.")

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
    elif (text == "📊 Saldos"):
        await saldos_command(update, context)
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
        # Buscar el préstamo
        loans = db_get_all_loans()
        loan = next((l for l in loans if l["loan_id"] == loan_id_to_update), None)
        if not loan:
            await update.message.reply_text(f"❌ Préstamo {loan_id_to_update} no encontrado.")
            return
        # Sumar el pago al pagado actual
        new_paid_amount = loan["paid_amount"] + payment
        # Calcular nuevo estado
        capital = loan["amount"]
        if new_paid_amount >= capital:
            new_status = "Pagado"
            new_paid_amount = capital  # No permitir pagado mayor al capital
        else:
            new_status = "Parcialmente Pagado"
        if db_update_loan_status(loan_id_to_update, new_status, new_paid_amount):
            await update.message.reply_text(
                f"💰 Pago registrado para préstamo {loan_id_to_update}.\n"
                f"Pagado total: {new_paid_amount}\n"
                f"Estado: {new_status}"
            )
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
            f"🆔 {loan['loan_id']}\n"
            f"👤 Cliente: {loan['client_name']}\n"
            f"💵 Capital: {loan['amount']}\n"
            f"💰 Interés: {loan['interest']}\n"
            f"📅 Fecha de registro: {loan['creation_date']}\n"
            f"📆 Fecha de pago: {loan['payment_due_date']}\n"
            f"🏷️ Estado: {loan['status']}\n"
            f"💸 Pagado: {loan['paid_amount']}\n"
            "-----------------------------\n"
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
        writer.writerow(["ID", "Loan ID", "User ID", "User Name", "Client Name", "Amount", "Interest", "Payment Due Date", "Status", "Paid Amount", "Creation Date"])
        for loan in loans:
            writer.writerow([
                loan["id"], loan["loan_id"], loan["user_id"], loan["user_name"], loan["client_name"],
                loan["amount"], loan["interest"], loan["payment_due_date"], loan["status"], loan["paid_amount"], loan["creation_date"]
            ])
    with open(csv_path, "rb") as f:
        await update.message.reply_document(document=InputFile(f, filename=csv_path))
    os.remove(csv_path)

async def saldos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loans = db_get_all_loans()
    if not loans:
        await update.message.reply_text("📊 No hay préstamos registrados.")
        return
    msg = "📊 <b>Saldos de Clientes:</b>\n\n"
    for loan in loans:
        cliente = loan["client_name"]
        capital = loan["amount"]
        interes = loan["interest"]
        pagado = loan["paid_amount"]
        saldo = capital - pagado
        cuota = round(capital * 0.20, 2)
        # Si pagado > cuota, recalcula saldo/capital/couta en ciclo
        pagos_restantes = pagado
        nuevo_capital = capital
        while pagos_restantes > 0 and nuevo_capital > 0:
            cuota_actual = round(nuevo_capital * 0.20, 2)
            if pagos_restantes >= cuota_actual:
                pagos_restantes -= cuota_actual
                nuevo_capital -= cuota_actual
            else:
                nuevo_capital -= pagos_restantes
                pagos_restantes = 0
        saldo_final = max(nuevo_capital, 0)
        cuota_actual = round(saldo_final * 0.20, 2) if saldo_final > 0 else 0
        msg += (
            f"👤 Cliente: {cliente}\n"
            f"💵 Capital actual: {saldo_final}\n"
            f"💰 Próxima cuota (20%): {cuota_actual}\n"
            f"💸 Pagado: {pagado}\n"
            "-----------------------------\n"
        )
    await update.message.reply_text(msg[:4096], parse_mode="HTML")

# Estados para el registro de préstamo
ASK_CLIENT, ASK_AMOUNT = range(2)
ASK_INTEREST = 2  # No se pregunta, pero se usa para el flujo
ASK_CONFIRM = 3

async def new_loan_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("👤 Ingresa el nombre del cliente:")
    return ASK_CLIENT

async def new_loan_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    client_name = update.message.text.strip()
    if not client_name:
        await update.message.reply_text("❌ El nombre del cliente no puede estar vacío. Intenta de nuevo:")
        return ASK_CLIENT
    context.user_data["client_name"] = client_name
    await update.message.reply_text("💵 Ingresa el capital del préstamo (solo números):")
    return ASK_AMOUNT

async def new_loan_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.replace(",", "."))
        if amount <= 0:
            raise ValueError()
        context.user_data["amount"] = amount
        # Interés fijo del 20%
        interest = round(amount * 0.20, 2)
        context.user_data["interest"] = interest
        # Fecha de registro automática
        creation_date = datetime.now().strftime("%Y-%m-%d")
        context.user_data["creation_date"] = creation_date
        # Fecha de pago a 30 días
        payment_due_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        context.user_data["payment_due_date"] = payment_due_date
        # Confirmación
        await update.message.reply_text(
            f"Resumen del préstamo:\n"
            f"👤 Cliente: {context.user_data['client_name']}\n"
            f"💵 Capital: {amount}\n"
            f"💰 Interés (20%): {interest}\n"
            f"📅 Fecha de registro: {creation_date}\n"
            f"📆 Fecha de pago: {payment_due_date}\n\n"
            f"¿Deseas guardar este préstamo? (si/no)"
        )
        return ASK_CONFIRM
    except ValueError:
        await update.message.reply_text("❌ Capital inválido. Ingresa solo números positivos:")
        return ASK_AMOUNT

async def new_loan_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text not in ["si", "sí", "s", "yes", "y"]:
        await update.message.reply_text("Registro de préstamo cancelado.")
        return ConversationHandler.END

    user = update.effective_user
    loans = db_get_all_loans()
    loan_id = f"L{user.id}{len(loans) + 1}"
    borrower_id = str(user.id)
    borrower_name = user.full_name
    client_name = context.user_data["client_name"]
    amount = context.user_data["amount"]
    interest = context.user_data["interest"]
    creation_date = context.user_data["creation_date"]
    payment_due_date = context.user_data["payment_due_date"]
    status = "Pendiente"
    paid_amount = 0.0

    if db_add_loan(loan_id, borrower_id, borrower_name, client_name, amount, interest, payment_due_date, status, paid_amount, creation_date):
        await update.message.reply_text(
            f"✅ Préstamo registrado:\n"
            f"ID: {loan_id}\n"
            f"👤 Cliente: {client_name}\n"
            f"💵 Capital: {amount}\n"
            f"💰 Interés: {interest}\n"
            f"📅 Fecha de registro: {creation_date}\n"
            f"📆 Fecha de pago: {payment_due_date}"
        )
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

    application.add_handler(CommandHandler("start", start))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("nuevoprestamo", new_loan_start), MessageHandler(filters.Regex("^📝 Nuevo Préstamo$"), new_loan_start)],
        states={
            ASK_CLIENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, new_loan_client)],
            ASK_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, new_loan_amount)],
            ASK_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, new_loan_confirm)],
        },
        fallbacks=[CommandHandler("cancel", new_loan_cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("pay", pay_loan_command))
    application.add_handler(CommandHandler("listarprestamos", list_loans_command))
    application.add_handler(CommandHandler("backup", backup_command))
    application.add_handler(CommandHandler("saldos", saldos_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_menu))
    print("Bot iniciado. Presiona Ctrl+C para detener.")
    application.run_polling()

if __name__ == '__main__':
    main()
