import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

def validate_redirect_uris(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    uris = data.get("installed", {}).get("redirect_uris", [])
    has_localhost = "http://localhost" in uris
    has_oob = "urn:ietf:wg:oauth:2.0:oob" in uris
    return has_localhost, has_oob

def authenticate_google(json_path, scopes, token_path, prefer_oob=True):
    has_localhost, has_oob = validate_redirect_uris(json_path)
    if not (has_localhost or has_oob):
        raise RuntimeError("El archivo de credenciales no contiene ningún redirect_uri válido. Debe tener al menos 'http://localhost' o 'urn:ietf:wg:oauth:2.0:oob'.")

    creds = None
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, scopes)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(token_path, 'w') as token_file:
                    token_file.write(creds.to_json())
            except Exception:
                creds = None
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(json_path, scopes)
            # Forzar OOB si está disponible, ignorando navegador
            if has_oob:
                auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
                print(f"Por favor, visita esta URL para autorizar esta aplicación:\n{auth_url}\n")
                code = input("Ingresa el código de autorización obtenido del navegador: ").strip()
                flow.fetch_token(code=code)
                creds = flow.credentials
            elif has_localhost:
                creds = flow.run_local_server(port=0)
            else:
                raise RuntimeError("No hay redirect_uri adecuado para el flujo de autenticación.")
            with open(token_path, 'w') as token_file:
                token_file.write(creds.to_json())
    return creds
