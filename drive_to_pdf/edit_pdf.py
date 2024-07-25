from PyPDF2 import PdfReader, PdfWriter
import os


def add_page(pdf_path, page_path, output_path):
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    # Fügen Sie die bestehenden Seiten zur neuen PDF hinzu
    for page in reader.pages:
        writer.add_page(page)

    # Fügen Sie die neue Seite hinzu
    new_page_reader = PdfReader(page_path)
    writer.add_page(new_page_reader.pages[0])

    # Speichern Sie die neue PDF
    with open(output_path, "wb") as f_out:
        writer.write(f_out)


def remove_page(pdf_path, page_number, output_path):
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    # Fügen Sie alle Seiten außer der zu entfernenden zur neuen PDF hinzu
    for i in range(len(reader.pages)):
        if i != page_number:
            writer.add_page(reader.pages[i])

    # Speichern Sie die neue PDF
    with open(output_path, "wb") as f_out:
        writer.write(f_out)


def get_page_count(pdf_path):
    reader = PdfReader(pdf_path)
    return len(reader.pages)
