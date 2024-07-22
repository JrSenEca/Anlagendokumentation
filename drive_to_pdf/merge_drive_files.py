import os
from PyPDF2 import PdfMerger, PdfReader
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import openpyxl
from docx import Document
import json
from tqdm import tqdm
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

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


def create_title_page(title, output_path):
    print(f"Erstelle Titelblatt: {title}")
    title_page = Image.new("RGB", (595, 842), (255, 255, 255))
    draw = ImageDraw.Draw(title_page)
    try:
        title_font = ImageFont.truetype("arial.ttf", 48)
    except IOError:
        title_font = ImageFont.load_default()

    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width, title_height = (
        title_bbox[2] - title_bbox[0],
        title_bbox[3] - title_bbox[1],
    )

    draw.text(((595 - title_width) / 2, 400), title, font=title_font, fill="black")
    title_page.save(output_path)


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
            print(f"Herunterladen: {file['title']}")
            file.GetContentFile(file_path)


def convert_excel_to_pdf(excel_path, pdf_path):
    workbook = openpyxl.load_workbook(excel_path)
    sheet = workbook.active

    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    y = height - 40
    for row in sheet.iter_rows(values_only=True):
        for cell in row:
            c.drawString(40, y, str(cell))
            y -= 15
            if y < 40:
                c.showPage()
                y = height - 40

    c.save()


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


def add_files_to_merger(merger, files):
    for file_path in files:
        if file_path.endswith(".pdf"):
            merger.append(file_path)
        elif file_path.endswith(".xlsx"):
            pdf_path = file_path.rsplit(".", 1)[0] + ".pdf"
            convert_excel_to_pdf(file_path, pdf_path)
            merger.append(pdf_path)
        elif file_path.endswith(".docx"):
            pdf_path = file_path.rsplit(".", 1)[0] + ".pdf"
            convert_docx_to_pdf(file_path, pdf_path)
            merger.append(pdf_path)
        elif any(file_path.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
            img = Image.open(file_path)
            img = img.convert("RGB")
            pdf_path = file_path.rsplit(".", 1)[0] + ".pdf"
            img.save(pdf_path)
            merger.append(pdf_path)
        else:
            print(f"Überspringe nicht unterstützte Datei: {file_path}")


def merge_pdfs(output_path, download_path, config):
    print("Beginne mit dem Zusammenfügen der PDFs...")
    merger = PdfMerger()
    customer_name = config.get("customer_name", "Kunde")

    cover_page_path = os.path.join(download_path, "cover_page.pdf")
    create_cover_page("Projektbericht", customer_name, cover_page_path)
    merger.append(cover_page_path)

    toc = config.get("table_of_contents", [])
    all_files = set(os.listdir(download_path))
    assigned_files = set()

    predefined_sections = [
        {"title": "Bilder - Aufmaß", "folders": ["Fotos_Aufmaß"]},
        {"title": "Statikbericht", "folders": ["Planung", "Planungen"]},
        {"title": "Material-Liste der Unterkonstruktion", "folders": []},
        {"title": "Elektroplanung", "folders": []},
        {"title": "Datenblätter der Komponenten", "folders": []},
        {
            "title": "Bilder - DC-Montage",
            "folders": ["Fotos_Montage", "Fotos_DC-Montage"],
        },
        {"title": "Abnahmeprotokoll (DC-Montage)", "folders": []},
        {"title": "Netzanmeldung", "folders": ["Netzanmeldung", "Netzanmeldungen"]},
        {
            "title": "Marktstammdatenregister-Anmeldung",
            "folders": ["MaStR", "Marktstammdaten"],
        },
        {"title": "Kontaktdaten", "folders": []},
    ]

    for section in predefined_sections:
        section_title = section["title"]
        section_path = os.path.join(download_path, section_title + ".pdf")
        create_title_page(section_title, section_path)
        merger.append(section_path)

        for folder_name in section["folders"]:
            folder_path = os.path.join(download_path, folder_name)
            if os.path.isdir(folder_path):
                files_to_add = [
                    os.path.join(folder_path, f)
                    for f in os.listdir(folder_path)
                    if os.path.isfile(os.path.join(folder_path, f))
                ]
                assigned_files.update(files_to_add)
                add_files_to_merger(merger, files_to_add)

    unassigned_files = all_files - assigned_files
    if unassigned_files:
        section_path = os.path.join(download_path, "Weitere Dokumente.pdf")
        create_title_page("Weitere Dokumente", section_path)
        merger.append(section_path)
        for file_title in unassigned_files:
            file_path = os.path.join(download_path, file_title)
            if os.path.isfile(file_path):
                add_files_to_merger(merger, [file_path])

    with open(output_path, "wb") as f_out:
        merger.write(f_out)
    print("PDF wurde erfolgreich erstellt.")


def create_pdf(folder_id, download_path, output_path):
    download_files(folder_id, download_path)
    config = load_config()
    merge_pdfs(output_path, download_path, config)
    print("Lösche den Download-Ordner...")
    for root, dirs, files in os.walk(download_path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    print("Vorgang abgeschlossen.")


def load_config():
    with open("config.json", "r") as f:
        return json.load(f)


def save_config(config):
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)


if __name__ == "__main__":
    folder_id = "your_google_drive_folder_id"
    create_pdf(folder_id, "downloads", PDF_OUTPUT_DIR)
