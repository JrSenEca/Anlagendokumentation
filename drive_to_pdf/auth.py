from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# Authentifizierung
gauth = GoogleAuth()

# Versuche gespeicherte Anmeldeinformationen zu laden
gauth.LoadCredentialsFile("mycreds.txt")

if gauth.credentials is None or gauth.access_token_expired:
    # Authentifizierung über den Browser
    gauth.LocalWebserverAuth()
    # Speichere Anmeldeinformationen in einer Datei
    gauth.SaveCredentialsFile("mycreds.txt")
else:
    gauth.Authorize()

# Erstelle Google Drive Instanz
drive = GoogleDrive(gauth)

print("Authentication successful.")
