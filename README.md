# Anlagendokumentation
Installation
Klone das Repository:

bash
Code kopieren
git clone https://github.com/yourusername/Anlagendokumentation.git
Wechsel in das Verzeichnis:

bash
Code kopieren
cd Anlagendokumentation
Erstelle und aktiviere eine virtuelle Umgebung:

bash
Code kopieren
python3 -m venv .venv
source .venv/bin/activate
Installiere die Abhängigkeiten:

bash
Code kopieren
pip install -r requirements.txt
Konfiguration
Erstelle eine Datei namens config.json im Stammverzeichnis des Projekts mit folgendem Inhalt:

json
Code kopieren
{
    "customer_name": "Kunde",
    "table_of_contents": [
        {"title": "Bilder - Aufmaß", "folders": ["Fotos_Aufmaß"]},
        {"title": "Statikbericht", "folders": ["Planung", "Planungen"]},
        {"title": "Material-Liste der Unterkonstruktion", "folders": []},
        {
            "title": "Elektroplanung",
            "files": [
                "Elektro/Anlagenplanung 2D.pdf"
            ],
            "folders": ["AC-Montage"],
            "additional_paths": ["Planung", "Planungen"]
        },
        {"title": "Datenblätter der Komponenten", "folders": []},
        {
            "title": "Bilder - DC-Montage",
            "folders": [
                "Fotos_Montage",
                "DC-Montage/Fotos_DC-Montage",
                "AC-Montage/Fotos_DC-Montage",
                "AC-Montage/Fotos_PV-Anlage"
            ]
        },
        {"title": "Abnahmeprotokoll (DC-Montage)", "folders": []},
        {
            "title": "Bilder - AC-Montage",
            "folders": [
                "AC-Montage/Fotos_AC-Montage",
                "AC-Montage_Kunde/Fotos_AC-Montage"
            ]
        },
        {
            "title": "Netzanmeldung",
            "folders": ["Netzanmeldung", "Netzanmeldungen", "MaStR"]
        },
        {"title": "Kontaktdaten", "folders": []},
        {"title": "Weitere Dokumente", "folders": []}
    ]
}
Nutzung
Starte das Skript:

bash
Code kopieren
python app.py
Befolge die Anweisungen im Skript, um die gewünschten PDF-Dateien zu generieren.

Tests
Stelle sicher, dass die Tests ordnungsgemäß eingerichtet sind. Füge die folgenden Anweisungen hinzu:

Erstelle eine Testdatei test_script.py und füge grundlegende Tests hinzu, um die wichtigsten Funktionen zu überprüfen.
Führe die Tests aus:
bash
Code kopieren
pytest test_script.py
Beispiel für Tests
Hier ist ein einfaches Beispiel für eine Testdatei:

python
Code kopieren
import pytest
from merge_drive_files import create_cover_page, create_title_page

def test_create_cover_page():
    create_cover_page("Test Title", "Test Customer", "test_cover_page.pdf")
    assert os.path.exists("test_cover_page.pdf")

def test_create_title_page():
    create_title_page(1, "Test Section", "test_title_page.pdf")
    assert os.path.exists("test_title_page.pdf")
Füge diese Datei in dein Projektverzeichnis ein und stelle sicher, dass pytest installiert ist:

bash
Code kopieren
pip install pytest
Führe die Tests aus:

bash
Code kopieren
pytest test_script.py
GitHub Actions für automatisierte Tests
Um sicherzustellen, dass die Funktionalität des Codes nicht verloren geht, kannst du GitHub Actions verwenden, um automatisierte Tests auszuführen. Erstelle eine Datei .github/workflows/python-app.yml mit folgendem Inhalt:

yaml
Code kopieren
name: Python application

on: [push, pull_request]

jobs:
  build:

    runs-on: ubuntu-latest

    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10]

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest
    - name: Test with pytest
      run: |
        pytest
Das stellt sicher, dass deine Tests automatisch ausgeführt werden, wenn du Änderungen an deinem Repository vornimmst.