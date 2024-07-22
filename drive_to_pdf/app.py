from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
    jsonify,
)
import os
from flask_cors import CORS
from merge_drive_files import create_pdf, load_config, save_config

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

PDF_OUTPUT_DIR = (
    "/Users/marie-luiseherrmann/Anlagendokumentation/drive_to_pdf/static/pdf_output"
)
DOWNLOAD_DIR = "downloads"


def ensure_output_dir():
    if not os.path.exists(PDF_OUTPUT_DIR):
        os.makedirs(PDF_OUTPUT_DIR)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    folder_id = request.form.get("folder_id")
    if folder_id:
        download_path = os.path.join(DOWNLOAD_DIR, folder_id)
        output_file = os.path.join(PDF_OUTPUT_DIR, f"{folder_id}_Projektbericht.pdf")
        create_pdf(folder_id, download_path, output_file)
        return redirect(url_for("index"))
    return "Fehler: Bitte geben Sie eine gültige Ordner-ID ein."


@app.route("/manage")
def manage():
    ensure_output_dir()  # Ensure the output directory exists
    pdf_files = [f for f in os.listdir(PDF_OUTPUT_DIR) if f.endswith(".pdf")]
    return render_template("manage.html", pdf_files=pdf_files)


@app.route("/edit/<filename>", methods=["GET", "POST"])
def edit(filename):
    if request.method == "POST":
        config = {
            "customer_name": request.form.get("customer_name"),
            "table_of_contents": [],
        }
        toc_titles = request.form.getlist("toc_title")
        toc_pages = request.form.getlist("toc_pages")

        for title, pages in zip(toc_titles, toc_pages):
            config["table_of_contents"].append({"title": title, "pages": pages})

        save_config(config)
        return redirect(url_for("manage"))

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

    new_filename = f"Anlagendokumentation_{customer_name}.pdf"
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
    app.run(debug=True, port=5001)
