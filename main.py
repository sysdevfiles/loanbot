import logging
import os
import sqlite3
import csv
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, InputFile, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
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
            creation_date TEXT,
            current_capital REAL
        )
    """)
    # Migración para agregar current_capital si no existe
    try:
        cursor.execute("ALTER TABLE loans ADD COLUMN current_capital REAL")
    except sqlite3.OperationalError:
        pass  # Ya existe
    conn.commit()
    conn.close()

def db_add_loan(loan_id, user_id, user_name, client_name, amount, interest, payment_due_date, status, paid_amount, creation_date):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO loans (loan_id, user_id, user_name, client_name, amount, interest, payment_due_date, status, paid_amount, creation_date, current_capital)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (loan_id, user_id, user_name, client_name, amount, interest, payment_due_date, status, paid_amount, creation_date, amount))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding loan: {e}")
        return False

def db_update_loan_status_and_capital(loan_id, new_status, new_paid_amount, new_current_capital):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE loans SET status = ?, paid_amount = ?, current_capital = ? WHERE loan_id = ?
        """, (new_status, new_paid_amount, new_current_capital, loan_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating loan: {e}")
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
    if text == "📝 Nuevo Préstamo":
        await new_loan_command(update, context)
    elif text == "💳 Pagar Cuota":
        await pay_select_client(update, context)
    elif text == "📋 Listar Préstamos":
        await list_loans_command(update, context)
    elif text == "💾 Backup CSV":
        await backup_command(update, context)
    elif text == "📊 Saldos":
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
        loans = db_get_all_loans()
        loan = next((l for l in loans if l["loan_id"] == loan_id_to_update), None)
        if not loan:
            await update.message.reply_text(f"❌ Préstamo {loan_id_to_update} no encontrado.")
            return

        # Convertir fecha de registro al formato dd-mm-yyyy
        fecha_registro = datetime.strptime(loan["creation_date"], "%d-%m-%Y")
        fecha_hoy = datetime.now()
        dias_transcurridos = (fecha_hoy - fecha_registro).days
        if dias_transcurridos < 0:
            dias_transcurridos = 0

        interes_anual = 0.20
        capital_inicial = loan["amount"]
        interes_diario = (interes_anual / 365) * capital_inicial

        pagado_anterior = loan["paid_amount"]
        current_capital = loan["current_capital"] if loan["current_capital"] is not None else capital_inicial

        # Calcular cuota actual (20% del capital actual)
        cuota = round(current_capital * 0.20, 2)
        pago_restante = payment
        nuevo_capital = current_capital

        # Amortización: si el pago es mayor a la cuota, amortiza capital
        while pago_restante > 0 and nuevo_capital > 0:
            cuota_actual = round(nuevo_capital * 0.20, 2)
            if pago_restante >= cuota_actual:
                pago_restante -= cuota_actual
                nuevo_capital -= (payment - pago_restante - (payment - pago_restante > cuota_actual and cuota_actual or pago_restante))
            else:
                nuevo_capital -= pago_restante
                pago_restante = 0

        nuevo_capital = max(nuevo_capital, 0)

        # Interés diario sobre el capital inicial
        saldo = capital_inicial + (interes_diario * dias_transcurridos)
        saldo -= pagado_anterior
        saldo -= payment
        saldo = max(saldo, 0)
        nuevo_pagado = pagado_anterior + payment

        if saldo <= 0 or nuevo_capital <= 0:
            new_status = "Pagado"
        else:
            new_status = "Parcialmente Pagado"

        if db_update_loan_status_and_capital(loan_id_to_update, new_status, nuevo_pagado, nuevo_capital):
            await update.message.reply_text(
                f"💰 Pago registrado para préstamo {loan_id_to_update}.\n"
                f"Pagado total: {nuevo_pagado:.2f}\n"
                f"Capital inicial: {capital_inicial:.2f}\n"
                f"Capital actual: {nuevo_capital:.2f}\n"
                f"Saldo actualizado (con interés diario): {saldo:.2f}\n"
                f"Estado: {new_status}"
            )
        else:
            await update.message.reply_text(f"❌ Error al actualizar el pago para {loan_id_to_update}.")
    except (IndexError, ValueError) as e:
        await update.message.reply_text(f"Error en el comando. Uso: /pay <ID_Préstamo> <MontoPagado>. Detalle: {e}")

# Resumen de la lógica de "Pagar Cuota"

# - El usuario ejecuta `/pay <ID_Préstamo> <MontoPagado>`.
# - El bot busca el préstamo por su ID.
# - Calcula los días transcurridos desde la fecha de registro (`dd-mm-yyyy`).
# - Calcula el interés diario simple: `(0.20 / 365) * capital`.
# - El saldo se actualiza sumando el interés diario acumulado por los días transcurridos al capital, y restando lo pagado anteriormente y el nuevo pago.
# - El saldo nunca es negativo.
# - Si el saldo es 0 o menor, el estado del préstamo pasa a "Pagado", si no, queda como "Parcialmente Pagado".
# - El bot actualiza el monto pagado y el estado en la base de datos y responde con el nuevo saldo y estado.

# Ejemplo de mensaje de respuesta:
# 💰 Pago registrado para préstamo L1234.
# Pagado total: 500.00
# Saldo actualizado (con interés diario): 1200.00
# Estado: Parcialmente Pagado

async def list_loans_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loans = db_get_all_loans()
    if not loans:
        await update.message.reply_text("📋 No hay préstamos registrados.")
        return
    msg = "📋 <b>Préstamos registrados:</b>\n\n"
    for loan in loans:
        capital_inicial = loan["amount"]
        capital_actual = loan["current_capital"] if loan["current_capital"] is not None else capital_inicial
        msg += (
            f"🆔 {loan['loan_id']}\n"
            f"👤 Cliente: {loan['client_name']}\n"
            f"💵 Capital inicial: {capital_inicial}\n"
            f"💵 Capital actual: {capital_actual}\n"
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
        capital_inicial = loan["amount"]
        capital_actual = loan["current_capital"] if loan["current_capital"] is not None else capital_inicial
        pagado = loan["paid_amount"]
        cuota_actual = round(capital_actual * 0.20, 2) if capital_actual > 0 else 0
        msg += (
            f"👤 Cliente: {cliente}\n"
            f"💵 Capital inicial: {capital_inicial}\n"
            f"💵 Capital actual: {capital_actual}\n"
            f"💰 Próxima cuota (20%): {cuota_actual}\n"
            f"💸 Pagado: {pagado}\n"
            "-----------------------------\n"
        )
    await update.message.reply_text(msg[:4096], parse_mode="HTML")

# Estados para el registro de préstamo
ASK_CLIENT, ASK_AMOUNT = range(2)
ASK_INTEREST = 2  # No se pregunta, pero se usa para el flujo
ASK_CONFIRM = 3

# Estados para pagar cuota
PAY_SELECT_CLIENT, PAY_SELECT_LOAN, PAY_ENTER_AMOUNT = range(10, 13)

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
        # Fecha de registro automática en formato dd-mm-yyyy
        creation_date = datetime.now().strftime("%d-%m-%Y")
        context.user_data["creation_date"] = creation_date
        # Fecha de pago a 30 días en formato dd-mm-yyyy
        payment_due_date = (datetime.now() + timedelta(days=30)).strftime("%d-%m-%Y")
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

# --- Nuevo flujo para pagar cuota con selección de cliente ---

async def pay_select_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loans = db_get_all_loans()
    clientes = list({loan["client_name"] for loan in loans if loan["status"] != "Pagado"})
    if not clientes:
        await update.message.reply_text("No hay clientes con préstamos pendientes.")
        return ConversationHandler.END
    context.user_data["clientes"] = clientes
    keyboard = [[KeyboardButton(cliente)] for cliente in clientes]
    await update.message.reply_text(
        "Selecciona el cliente que va a realizar el pago:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return PAY_SELECT_CLIENT

async def pay_receive_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cliente = update.message.text.strip()
    if cliente not in context.user_data.get("clientes", []):
        await update.message.reply_text("Cliente no válido. Selecciona uno de la lista.")
        return PAY_SELECT_CLIENT
    context.user_data["cliente_pago"] = cliente
    loans = db_get_all_loans()
    prestamos_cliente = [loan for loan in loans if loan["client_name"] == cliente and loan["status"] != "Pagado"]
    if not prestamos_cliente:
        await update.message.reply_text("No hay préstamos pendientes para este cliente.")
        return ConversationHandler.END
    context.user_data["prestamos_cliente"] = prestamos_cliente
    # Mostrar lista con ID, nombre y monto
    msg = "Selecciona el préstamo a pagar:\n"
    keyboard = []
    for loan in prestamos_cliente:
        msg += f"ID: {loan['loan_id']} | Monto: {loan['current_capital'] if loan['current_capital'] is not None else loan['amount']} | Cliente: {loan['client_name']}\n"
        keyboard.append([KeyboardButton(loan["loan_id"])])
    await update.message.reply_text(
        msg,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return PAY_SELECT_LOAN

async def pay_receive_loan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loan_id = update.message.text.strip()
    prestamos_cliente = context.user_data.get("prestamos_cliente", [])
    loan = next((l for l in prestamos_cliente if l["loan_id"] == loan_id), None)
    if not loan:
        await update.message.reply_text("ID de préstamo no válido. Selecciona uno de la lista.")
        return PAY_SELECT_LOAN
    context.user_data["loan_pago"] = loan
    await update.message.reply_text(
        f"Ingrese el monto a pagar para el préstamo {loan_id} (capital actual: {loan['current_capital'] if loan['current_capital'] is not None else loan['amount']}):",
        reply_markup=ReplyKeyboardRemove()
    )
    return PAY_ENTER_AMOUNT

async def pay_process_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        payment = float(update.message.text.replace(",", "."))
        if payment <= 0:
            raise ValueError()
        loan = context.user_data.get("loan_pago")
        if not loan:
            await update.message.reply_text("Error interno. Intenta de nuevo.")
            return ConversationHandler.END

        # Convertir fecha de registro al formato dd-mm-yyyy
        fecha_registro = datetime.strptime(loan["creation_date"], "%d-%m-%Y")
        fecha_hoy = datetime.now()
        dias_transcurridos = (fecha_hoy - fecha_registro).days
        if dias_transcurridos < 0:
            dias_transcurridos = 0

        # Fórmula de interés diario: (Tasa de Interés Anual / 365) * Capital
        interes_anual = 0.20
        capital = loan["amount"]
        interes_diario = (interes_anual / 365) * capital

        pagado_anterior = loan["paid_amount"]

        # Saldo con interés diario simple acumulado
        saldo = capital + (interes_diario * dias_transcurridos)
        saldo -= pagado_anterior
        saldo -= payment

        saldo = max(saldo, 0)
        nuevo_pagado = pagado_anterior + payment

        if saldo <= 0:
            new_status = "Pagado"
        else:
            new_status = "Parcialmente Pagado"

        if db_update_loan_status(loan["loan_id"], new_status, nuevo_pagado):
            await update.message.reply_text(
                f"💰 Pago registrado para préstamo {loan['loan_id']}.\n"
                f"Pagado total: {nuevo_pagado:.2f}\n"
                f"Saldo actualizado (con interés diario): {saldo:.2f}\n"
                f"Estado: {new_status}"
            )
        else:
            await update.message.reply_text(f"❌ Error al actualizar el pago para {loan['loan_id']}.")
    except Exception as e:
        await update.message.reply_text(f"Error procesando el pago: {e}")
    return ConversationHandler.END

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

    pay_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("pay", pay_select_client), MessageHandler(filters.Regex("^💳 Pagar Cuota$"), pay_select_client)],
        states={
            PAY_SELECT_CLIENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, pay_receive_client)],
            PAY_SELECT_LOAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, pay_receive_loan)],
            PAY_ENTER_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, pay_process_amount)],
        },
        fallbacks=[CommandHandler("cancel", new_loan_cancel)],
        map_to_parent={
            ConversationHandler.END: ConversationHandler.END,
        }
    )

    application.add_handler(conv_handler)
    application.add_handler(pay_conv_handler)
    application.add_handler(CommandHandler("listarprestamos", list_loans_command))
    application.add_handler(CommandHandler("backup", backup_command))
    application.add_handler(CommandHandler("saldos", saldos_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_menu))
    print("Bot iniciado. Presiona Ctrl+C para detener.")
    application.run_polling()

if __name__ == '__main__':
    main()
