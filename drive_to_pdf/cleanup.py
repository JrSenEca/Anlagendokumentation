import os
import shutil

# Definiere die zu behaltenden Dateien und Verzeichnisse
keep_files = {
    "merge_drive_files.py",
    "client_secrets.json",
    "venv",
    "pdf_output",
    "cleanup.py",
    "static",
    "templates",
    "app.py",
    "auth.py",
    "config.json",
    "mycreds.txt",
}

# Liste alle Dateien und Verzeichnisse im aktuellen Verzeichnis auf
all_files = set(os.listdir("."))

# Berechne die zu löschenden Dateien und Verzeichnisse
delete_files = all_files - keep_files

# Lösche die zu löschenden Dateien und Verzeichnisse
for file in delete_files:
    if os.path.isfile(file):
        os.remove(file)
        print(f"Datei gelöscht: {file}")
    elif os.path.isdir(file):
        shutil.rmtree(file)
        print(f"Verzeichnis gelöscht: {file}")

print("Aufräumvorgang abgeschlossen.")
