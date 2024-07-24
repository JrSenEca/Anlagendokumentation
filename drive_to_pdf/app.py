import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
    jsonify,
)
from flask_cors import CORS
from merge_drive_files import create_pdf, load_config, save_config, PDF_OUTPUT_DIR

# Google Drive Authentication
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

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


DOWNLOAD_DIR = "downloads"


def ensure_output_dir():
    if not os.path.exists(PDF_OUTPUT_DIR):
        os.makedirs(PDF_OUTPUT_DIR)


def get_folder_name(folder_id):
    file = drive.CreateFile({"id": folder_id})
    file.FetchMetadata(fields="title")
    return file["title"]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    folder_id = request.form.get("folder_id")
    if folder_id:
        create_pdf(folder_id, DOWNLOAD_DIR, PDF_OUTPUT_DIR)
        folder_name = get_folder_name(folder_id)
        filename = f"Anlagendokumentation_{folder_name}.pdf"
        return jsonify({"success": True, "filename": filename})
    return jsonify(
        {"success": False, "error": "Bitte geben Sie eine gültige Ordner-ID ein."}
    )


@app.route("/manage")
def manage():
    ensure_output_dir()  # Ensure the output directory exists
    pdf_files = [f for f in os.listdir(PDF_OUTPUT_DIR) if f.endswith(".pdf")]
    return render_template("manage.html", pdf_files=pdf_files)


@app.route("/edit/<filename>", methods=["GET", "POST"])
def edit(filename):
    config = load_config()
    return render_template("edit.html", config=config, filename=filename)


@app.route("/upload", methods=["POST"])
def upload():
    section = request.form.get("section")
    uploaded_files = request.files.getlist("file")
    upload_path = os.path.join(PDF_OUTPUT_DIR, section)
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)

    for file in uploaded_files:
        file.save(os.path.join(upload_path, file.filename))

    return jsonify({"success": True})


@app.route("/delete_file", methods=["POST"])
def delete_file():
    section = request.json.get("section")
    filename = request.json.get("filename")
    file_path = os.path.join(PDF_OUTPUT_DIR, section, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({"success": True})
    return jsonify({"success": False})


@app.route("/save_customer_name", methods=["POST"])
def save_customer_name():
    data = request.get_json()
    customer_name = data["customer_name"]
    filename = data["filename"]

    base_name, ext = os.path.splitext(filename)
    new_filename = f"Anlagendokumentation_{customer_name}{ext}"
    old_filepath = os.path.join(PDF_OUTPUT_DIR, filename)
    new_filepath = os.path.join(PDF_OUTPUT_DIR, new_filename)

    if os.path.exists(old_filepath):
        os.rename(old_filepath, new_filepath)
        return jsonify({"new_filename": new_filename})
    else:
        return jsonify({"error": "Datei nicht gefunden"}), 404


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(PDF_OUTPUT_DIR, filename)


@app.route("/static/pdf_output/<filename>")
def view_pdf(filename):
    return send_from_directory(PDF_OUTPUT_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True, port=5002)
