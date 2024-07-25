import os
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from docx import Document
import json
from tqdm import tqdm
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import traceback
from pdfrw import PdfReader, PdfWriter, PageMerge

gauth = GoogleAuth()
gauth.LoadCredentialsFile("mycreds.txt")
if gauth.credentials is None or gauth.access_token_expired:
    gauth.LocalWebserverAuth()
    if gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.LocalWebserverAuth()
    gauth.SaveCredentialsFile("mycreds.txt")
drive = GoogleDrive(gauth)

PDF_OUTPUT_DIR = (
    "/Users/marie-luiseherrmann/Anlagendokumentation/drive_to_pdf/static/pdf_output"
)

DOWNLOAD_DIR = "/Users/marie-luiseherrmann/Anlagendokumentation/drive_to_pdf/downloads"


def ensure_output_dir(output_dir):
    os.makedirs(output_dir, exist_ok=True)


def create_cover_page(title, customer_name, output_path):
    print(f"Erstelle Deckblatt: {title}")
    cover_page = Image.new("RGB", (595, 842), (255, 255, 255))
    draw = ImageDraw.Draw(cover_page)
    try:
        title_font = ImageFont.truetype("arial.ttf", 48)
        customer_font = ImageFont.truetype("arial.ttf", 36)
    except IOError:
        title_font = ImageFont.load_default()
        customer_font = ImageFont.load_default()

    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    customer_bbox = draw.textbbox((0, 0), customer_name, font=customer_font)

    title_width, title_height = (
        title_bbox[2] - title_bbox[0],
        title_bbox[3] - title_bbox[1],
    )
    customer_width, customer_height = (
        customer_bbox[2] - customer_bbox[0],
        customer_bbox[3] - customer_bbox[1],
    )

    draw.text(((595 - title_width) / 2, 300), title, font=title_font, fill="black")
    draw.text(
        ((595 - customer_width) / 2, 400),
        customer_name,
        font=customer_font,
        fill="black",
    )

    cover_page.save(output_path)


def create_title_page(section_number, title, output_path):
    print(f"Erstelle Titelblatt: {title}")
    title_page = Image.new("RGB", (595, 842), (255, 255, 255))
    draw = ImageDraw.Draw(title_page)
    try:
        section_font = ImageFont.truetype("arial.ttf", 28)
        title_font = ImageFont.truetype("arial.ttf", 22)
    except IOError:
        section_font = ImageFont.load_default()
        title_font = ImageFont.load_default()

    section_text = f"Anlage {section_number}"
    section_bbox = draw.textbbox((0, 0), section_text, font=section_font)
    section_width, section_height = (
        section_bbox[2] - section_bbox[0],
        section_bbox[3] - section_bbox[1],
    )

    draw.text(
        ((595 - section_width) / 2, 300), section_text, font=section_font, fill="black"
    )
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width, title_height = (
        title_bbox[2] - title_bbox[0],
        title_bbox[3] - title_bbox[1],
    )

    draw.text(((595 - title_width) / 2, 400), title, font=title_font, fill="black")
    title_page.save(output_path)


def get_folder_name(folder_id):
    file = drive.CreateFile({"id": folder_id})
    file.FetchMetadata(fields="title")
    return file["title"]


def convert_docx_to_pdf(docx_path, pdf_path):
    doc = Document(docx_path)
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    y = height - 40
    for para in doc.paragraphs:
        c.drawString(40, y, para.text)
        y -= 15
        if y < 40:
            c.showPage()
            y = height - 40

    c.save()


def add_files_to_merger(merger, files, added_files):
    for file_path in files:
        if os.path.isdir(file_path):
            sub_files = [os.path.join(file_path, f) for f in os.listdir(file_path)]
            add_files_to_merger(merger, sub_files, added_files)
        elif file_path.endswith(".pdf"):
            if file_path not in added_files:
                try:
                    reader = PdfReader(file_path)
                    merger.addpages(reader.pages)
                    added_files.add(file_path)
                except Exception as e:
                    print(f"Fehler beim Hinzufügen der PDF-Datei {file_path}: {e}")
                    traceback.print_exc()
        elif file_path.endswith(".docx"):
            try:
                pdf_path = file_path.rsplit(".", 1)[0] + ".pdf"
                convert_docx_to_pdf(file_path, pdf_path)
                add_files_to_merger(merger, [pdf_path], added_files)
            except Exception as e:
                print(f"Fehler beim Konvertieren der Word-Datei {file_path}: {e}")
                traceback.print_exc()
        elif any(file_path.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
            try:
                img = Image.open(file_path)
                img = img.convert("RGB")
                pdf_path = file_path.rsplit(".", 1)[0] + ".pdf"
                img.save(pdf_path)
                add_files_to_merger(merger, [pdf_path], added_files)
            except Exception as e:
                print(f"Fehler beim Konvertieren der Bild-Datei {file_path}: {e}")
                traceback.print_exc()
        elif file_path.endswith(".xlsx"):
            print(f"Überspringe Excel-Datei: {file_path}")
        else:
            print(f"Überspringe nicht unterstützte Datei: {file_path}")


def merge_pdfs(output_file, download_path, config):
    print("Beginne mit dem Zusammenfügen der PDFs...")
    merger = PdfWriter()
    customer_name = config.get("customer_name", "Kunde")

    cover_page_path = os.path.join(download_path, "cover_page.pdf")
    create_cover_page("Projektbericht", customer_name, cover_page_path)
    if os.path.exists(cover_page_path):
        merger.addpages(PdfReader(cover_page_path).pages)
    else:
        print("Deckblatt konnte nicht erstellt werden, überspringe.")

    toc = config.get("table_of_contents", [])
    all_files = set(os.listdir(download_path))
    assigned_files = set()
    section_number = 1
    added_files = set()

    predefined_sections = [
        {"title": "Bilder - Aufmaß", "folders": ["Fotos_Aufmaß"]},
        {"title": "Statikbericht", "folders": ["Planung", "Planungen"]},
        {"title": "Material-Liste der Unterkonstruktion", "folders": []},
        {
            "title": "Elektroplanung",
            "files": [
                "Elektro/Anlagenplanung 2D.pdf",
                f"PV SOL Anlagenplanung {customer_name}.pdf",
                f"PV SOL Planung {customer_name}.pdf",
            ],
            "folders": ["AC-Montage"],
            "additional_paths": ["Planung", "Planungen"],
        },
        {"title": "Datenblätter der Komponenten", "folders": []},
        {
            "title": "Bilder - DC-Montage",
            "folders": [
                "Fotos_Montage",
                "DC-Montage/Fotos_DC-Montage",
                "AC-Montage/Fotos_DC-Montage",
                "AC-Montage/Fotos_PV-Anlage",
            ],
        },
        {"title": "Abnahmeprotokoll (DC-Montage)", "folders": []},
        {
            "title": "Bilder - AC-Montage",
            "folders": [
                "AC-Montage/Fotos_AC-Montage",
                f"AC-Montage {customer_name}/Fotos_AC-Montage",
            ],
        },
        {
            "title": "Netzanmeldung",
            "folders": ["Netzanmeldung", "Netzanmeldungen", "MaStR"],
        },
        {"title": "Kontaktdaten", "folders": []},
        {"title": "Weitere Dokumente", "folders": []},
    ]

    def add_files_from_folders(merger, folder_names, download_path, added_files):
        for folder_name in folder_names:
            folder_path = os.path.join(download_path, folder_name)
            if os.path.isdir(folder_path):
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        add_files_to_merger(merger, [file_path], added_files)

    for section in predefined_sections:
        section_title = section["title"]
        section_path = os.path.join(download_path, section_title + ".pdf")
        create_title_page(section_number, section_title, section_path)
        if os.path.exists(section_path):
            merger.addpages(PdfReader(section_path).pages)
        section_number += 1

        if "files" in section:
            for file_name in section["files"]:
                file_path = os.path.join(download_path, file_name)
                if os.path.isfile(file_path):
                    add_files_to_merger(merger, [file_path], added_files)

        if "folders" in section:
            add_files_from_folders(
                merger, section["folders"], download_path, added_files
            )

        if "additional_paths" in section:
            for path in section["additional_paths"]:
                folder_path = os.path.join(download_path, path)
                if os.path.isdir(folder_path):
                    add_files_from_folders(
                        merger, [folder_path], download_path, added_files
                    )

    unassigned_files = all_files - assigned_files
    if unassigned_files:
        section_path = os.path.join(download_path, "Weitere Dokumente.pdf")
        create_title_page(section_number, "Weitere Dokumente", section_path)
        if os.path.exists(section_path):
            merger.addpages(PdfReader(section_path).pages)
        for file_title in unassigned_files:
            file_path = os.path.join(download_path, file_title)
            if os.path.isfile(file_path):
                add_files_to_merger(merger, [file_path], added_files)

    with open(output_file, "wb") as f_out:
        merger.write(f_out)
    print(f"PDF erfolgreich erstellt: {output_file}")
    delete_downloaded_files(download_path)


def delete_downloaded_files(download_path):
    print("Lösche den Download-Ordner...")
    for root, dirs, files in os.walk(download_path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    print("Vorgang abgeschlossen.")


def create_pdf(folder_id, download_path, output_dir):
    ensure_output_dir(output_dir)
    output_file = os.path.join(
        output_dir, f"Anlagendokumentation_{get_folder_name(folder_id)}.pdf"
    )
    download_files(folder_id, download_path)
    config = load_config()
    merge_pdfs(output_file, download_path, config)


def download_files(folder_id, download_path):
    print(f"Lade Dateien von Ordner ID: {folder_id}")
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    file_list = drive.ListFile(
        {"q": f"'{folder_id}' in parents and trashed=false"}
    ).GetList()
    for file in tqdm(file_list, desc="Herunterladen"):
        file_path = os.path.join(download_path, file["title"])
        if file["mimeType"] == "application/vnd.google-apps.folder":
            download_files(file["id"], file_path)
        else:
            try:
                file.GetContentFile(file_path)
            except Exception as e:
                print(f"Fehler beim Herunterladen der Datei {file['title']}: {e}")
                traceback.print_exc()


def load_config():
    with open("config.json", "r") as f:
        return json.load(f)


def save_config(config):
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)


if __name__ == "__main__":
    folder_id = "your_google_drive_folder_id"
    create_pdf(folder_id, DOWNLOAD_DIR, PDF_OUTPUT_DIR)
