import gspread
import os
from dotenv import load_dotenv
from google_oauth_utils import authenticate_google

load_dotenv()

SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
HEADER = ['ID Préstamo', 'Fecha de Registro', 'Cliente', 'Capital', 'Interés', 'Fecha de Pago', 'Monto Amortizado', 'Saldo', 'Estatus']

TOKEN_JSON_PATH = os.path.join(os.path.expanduser("~"), ".config", "gspread", "loanbot_authorized_user.json")
os.makedirs(os.path.dirname(TOKEN_JSON_PATH), exist_ok=True)

def init_gspread_client(oauth_creds_file_path, sheet_name, worksheet_name):
    """Initializes and returns the gspread client and worksheet using OAuth2.0."""
    try:
        creds = authenticate_google(
            oauth_creds_file_path,
            SCOPE,
            TOKEN_JSON_PATH,
            prefer_oob=True  # Cambia a False si prefieres el flujo local
        )
        print("Inicializando cliente gspread con las credenciales obtenidas...")
        gc = gspread.Client(auth=creds)
        spreadsheet = gc.open(sheet_name)
        worksheet = spreadsheet.worksheet(worksheet_name)
        ensure_header(worksheet)
        print("Cliente de Google Sheets (OAuth) inicializado correctamente.")
        return worksheet
    except Exception as e:
        print(f"Error al autenticar o inicializar Google Sheets: {e}")
        return None

def ensure_header(worksheet):
    """Ensures the header row exists in the worksheet."""
    try:
        # Check if worksheet is empty or header is incorrect
        header_row = []
        if worksheet.row_count > 0: # Check if there's at least one row
            try:
                header_row = worksheet.row_values(1)
            except gspread.exceptions.APIError as e:
                # Handle cases where the sheet might be completely empty or inaccessible initially
                print(f"Could not read header row, possibly empty or API issue: {e}")
                # If it's a permission issue or sheet doesn't exist, init_gspread_client should catch it.
                # If it's just empty, we proceed to create the header.

        if not header_row or header_row != HEADER:
            # Clear existing content if header is wrong or sheet is not empty but has no valid header
            if worksheet.row_count > 0 and header_row: # if there's a wrong header
                 print("Incorrect header found. Clearing sheet and setting new header.")
                 # Be cautious with worksheet.clear() as it erases everything.
                 # For now, we assume if the header is wrong, a reset is intended.
                 # worksheet.clear() # This might be too destructive if only header is slightly off.
                 # A safer approach might be to delete row 1 and insert new, or check more carefully.
                 # For simplicity of this example, if header is present and wrong, we'll assume a reset.
                 # If only ensure_header is called on an empty sheet, this part is skipped.
                 if header_row != HEADER and len(header_row) > 0 : # only clear if there was a WRONG header
                    worksheet.clear()

            worksheet.insert_row(HEADER, 1) # Insert header if sheet was empty or cleared
            print("Header row created/corrected in Google Sheet.")
        # elif not worksheet.get_all_values() and header_row == HEADER: # Sheet exists, header is correct, but it's empty otherwise
        #      print("Sheet is empty but header is correct.")
        # The above elif might be redundant if get_all_values() is slow and not needed just for header check.
        # The primary goal is that row 1 IS the HEADER.

    except gspread.exceptions.APIError as e:
        if 'exceeds grid limits' in str(e).lower():
            print(f"Error ensuring header: Trying to insert into a sheet that might be too small or protected: {e}")
            # Potentially try to resize or just log and continue if header is critical
        else:
            print(f"API Error ensuring header: {e}")
    except Exception as e:
        print(f"General Error ensuring header: {e}")

def add_loan_to_sheet(worksheet, loan_data):
    """
    Adds a new loan record to the Google Sheet.
    loan_data should be a list in the order of HEADER.
    Example for new HEADER:
    [loan_id, registration_date, client_name, capital, interest, initial_payment_date_or_empty, initial_amortized_amount_or_0, initial_balance, status]
    """
    if not worksheet:
        print("Worksheet not initialized. Cannot add loan.")
        return False
    try:
        worksheet.append_row(loan_data)
        print(f"Loan {loan_data[0]} added to Google Sheet.")
        return True
    except Exception as e:
        print(f"Error adding loan to Google Sheet: {e}")
        return False

def update_loan_in_sheet(worksheet, loan_id, payment_date, payment_amount):
    """
    Updates an existing loan's payment date, amortized amount, recalculates the balance, and updates status.
    Assumes 'Capital' and 'Interés' are fixed once the loan is created.
    Returns the new status or None if update fails.
    """
    if not worksheet:
        print("Worksheet not initialized. Cannot update loan.")
        return None
    try:
        cell = worksheet.find(str(loan_id), in_column=HEADER.index('ID Préstamo') + 1)
        if cell:
            row_number = cell.row
            current_row_values = worksheet.row_values(row_number)

            # Get existing values needed for calculation
            try:
                capital_str = current_row_values[HEADER.index('Capital')]
                interest_str = current_row_values[HEADER.index('Interés')]
                current_amortized_str = current_row_values[HEADER.index('Monto Amortizado')]
                
                capital = float(capital_str) if capital_str else 0.0
                interest = float(interest_str) if interest_str else 0.0
                current_amortized_amount = float(current_amortized_str) if current_amortized_str else 0.0
            except (ValueError, IndexError) as e:
                print(f"Error converting financial data for loan {loan_id} to float: {e}. Row values: {current_row_values}")
                return None

            new_total_amortized_amount = current_amortized_amount + float(payment_amount)
            
            # Saldo = (Capital + Interés) - Monto Amortizado Total
            new_balance = (capital + interest) - new_total_amortized_amount

            # Determine new status based on the new balance
            if new_balance <= 0:
                new_status = "Pagado"
                new_balance = 0 # Ensure balance doesn't go negative in sheet for "Pagado"
            else:
                new_status = "Impago"

            # Update specific cells
            updates = [
                {'range': gspread.utils.rowcol_to_a1(row_number, HEADER.index('Fecha de Pago') + 1), 'values': [[payment_date]]},
                {'range': gspread.utils.rowcol_to_a1(row_number, HEADER.index('Monto Amortizado') + 1), 'values': [[new_total_amortized_amount]]},
                {'range': gspread.utils.rowcol_to_a1(row_number, HEADER.index('Saldo') + 1), 'values': [[new_balance]]},
                {'range': gspread.utils.rowcol_to_a1(row_number, HEADER.index('Estatus') + 1), 'values': [[new_status]]}
            ]
            worksheet.batch_update(updates)
            
            print(f"Loan {loan_id} updated in Google Sheet. New Balance: {new_balance}, New Status: {new_status}")
            return new_status # Return the new status
        else:
            print(f"Loan {loan_id} not found in Google Sheet for update.")
            return None
    except Exception as e:
        print(f"Error updating loan in Google Sheet: {e}")
        return None

def get_all_loans_from_sheet(worksheet):
    """Retrieves all loan records from the Google Sheet."""
    if not worksheet:
        print("Worksheet not initialized. Cannot get loans.")
        return []
    try:
        records = worksheet.get_all_records() # Returns a list of dictionaries
        return records
    except Exception as e:
        print(f"Error retrieving loans from Google Sheet: {e}")
        return []

# Example usage (optional, for testing this module directly)
if __name__ == '__main__':
    # For direct testing, you'd need to provide these or load from .env
    oauth_creds_file_env = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET_FILE', 'config/client_secret_XXXX.json') # Ensure this matches your .env
    sheet_name_env = os.getenv('GOOGLE_SHEET_NAME_FOR_TEST', 'Your Spreadsheet Name')
    worksheet_name_env = os.getenv('GOOGLE_SHEET_WORKSHEET_NAME_FOR_TEST', 'Sheet1')
    
    # Create config directory if it doesn't exist for storing authorized_user.json
    # This is relevant if you customize the authorized_user_filename path to be within the project.
    # For the example path os.path.join(os.path.expanduser("~"), ".config", "gspread", ...)
    # ensure ~/.config/gspread exists or gspread handles its creation.
    
    # For the custom path in init_gspread_client:
    token_dir = os.path.join(os.path.expanduser("~"), ".config", "gspread")
    if not os.path.exists(token_dir):
        try:
            os.makedirs(token_dir)
            print(f"Directorio de tokens creado en: {token_dir}")
        except OSError as e:
            print(f"No se pudo crear el directorio de tokens en {token_dir}: {e}")


    worksheet_instance = init_gspread_client(oauth_creds_file_env, sheet_name_env, worksheet_name_env)
    if worksheet_instance:
        print("Google Sheet client initialized for testing.")
        # Test add
        # loan_id_test = "TEST001"
        # test_loan_data = [
        #     loan_id_test, "2024-07-26", "Test Client", 1000.00, 200.00, "", 0.00, 1200.00, "Pendiente de Pago"
        # ]
        # add_loan_to_sheet(worksheet_instance, test_loan_data)
        
        # Test update
        # update_loan_in_sheet(worksheet_instance, loan_id_test, "2024-07-27", 100.00)
        
        # Test list
        # loans = get_all_loans_from_sheet(worksheet_instance)
        # for loan_record in loans:
        #     print(loan_record)
        pass
    else:
        print("Failed to initialize Google Sheet client for testing.")
