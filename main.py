from flask import Flask, render_template, request, redirect, url_for, send_file, send_from_directory, abort
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
from datetime import datetime
import json, os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ---------- FILE PATHS ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
HISTORY_FILE = os.path.join(BASE_DIR, "invoices.json")
FIRST_RUN_FILE = os.path.join(BASE_DIR, "first_run.flag")
LOGO_DIR = os.path.join(BASE_DIR, "static", "logo")

os.makedirs(LOGO_DIR, exist_ok=True)

# ---------- UTIL ----------
def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(default, f)
        return default
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

# ---------- VIEW INVOICE ----------
@app.route("/invoice/<invoice_no>")
def view_invoice(invoice_no):
    pdf_folder = os.path.join(app.root_path, "invoices")
    pdf_file = f"{invoice_no}.pdf"

    if not os.path.exists(os.path.join(pdf_folder, pdf_file)):
        abort(404)

    return send_from_directory(
        pdf_folder,
        pdf_file,
        mimetype="application/pdf"
    )

# ---------- WELCOME ----------
@app.route("/welcome", methods=["GET", "POST"])
def welcome():
    if request.method == "POST":
        with open(FIRST_RUN_FILE, "w") as f:
            f.write("done")
        return redirect("/")
    return render_template("welcome.html")

# ---------- HOME ----------
@app.route("/")
def index():
    if not os.path.exists(FIRST_RUN_FILE):
        return redirect("/welcome")
    return render_template("index.html")

# ---------- HISTORY ----------
@app.route("/history")
def history():
    invoices = load_json(HISTORY_FILE, [])
    return render_template("history.html", invoices=invoices)

# ---------- SETTINGS ----------
@app.route("/settings", methods=["GET", "POST"])
def settings():
    default_settings = {
        "theme": "light",
        "business_name": "SS Web Studio",
        "currency": "₹",
        "logo_path": ""
    }

    settings_data = load_json(SETTINGS_FILE, default_settings)

    if request.method == "POST":
        settings_data.update(request.form.to_dict())

        logo = request.files.get("logo")
        if logo and logo.filename:
            filename = secure_filename(logo.filename)
            logo_path = os.path.join(LOGO_DIR, filename)
            logo.save(logo_path)
            settings_data["logo_path"] = logo_path

        save_json(SETTINGS_FILE, settings_data)
        return redirect(url_for("settings"))

    return render_template("settings.html", settings=settings_data)

# ---------- CATEGORY ----------
@app.route("/shop")
def shop():
    return render_template("shop/invoice_form.html")

@app.route("/office")
def office():
    return render_template("office/office_invoice.html")

@app.route("/school")
def school():
    return render_template("school/school_invoice.html")

@app.route("/personal")
def personal():
    return render_template("personal/personal_invoice.html")

# ---------- HISTORY TOOLS ----------
@app.route("/clear-history")
def clear_history():
    save_json(HISTORY_FILE, [])
    return redirect(url_for("history"))

@app.route("/export-history")
def export_history():
    return send_file(HISTORY_FILE, as_attachment=True, download_name="invoice_history.json")

@app.route("/reset-app")
def reset_app():
    save_json(HISTORY_FILE, [])
    save_json(SETTINGS_FILE, {
        "theme": "light",
        "currency": "₹",
        "business_name": "SS Web Studio",
        "logo_path": ""
    })
    if os.path.exists(FIRST_RUN_FILE):
        os.remove(FIRST_RUN_FILE)
    return redirect("/")

# ---------- STATIC PAGES ----------
@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

# ---------- DELETE ----------
@app.route("/delete/<invoice_no>")
def delete_invoice(invoice_no):
    invoices = load_json(HISTORY_FILE, [])
    invoices = [i for i in invoices if i.get("invoice_no") != invoice_no]
    save_json(HISTORY_FILE, invoices)
    return redirect(url_for("history"))

# ---------- GENERATE PDF ----------
@app.route("/generate", methods=["POST"])
def generate_invoice():
    settings = load_json(SETTINGS_FILE, {})
    currency = settings.get("currency", "₹")
    business_name = settings.get("business_name", "SS Web Studio")
    logo_path = settings.get("logo_path")

    invoice_type = request.form.get("invoice_type", "personal")
    titles = {
        "shop": "SHOP / BUSINESS INVOICE",
        "office": "OFFICE / FREELANCE INVOICE",
        "school": "SCHOOL / FEES RECEIPT",
        "personal": "PERSONAL INVOICE"
    }
    invoice_title = titles.get(invoice_type, "INVOICE")

    name = request.form.get("name", "")
    mobile = request.form.get("mobile", "")
    service = request.form.get("service_name", "")
    qty = int(request.form.get("quantity", 1))
    rate = float(request.form.get("rate", 0))
    total = qty * rate
    note = request.form.get("note", "")

    show_mobile = request.form.get("show_mobile") is not None
    show_note = request.form.get("show_note") is not None

    invoice_no = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    pdf_name = request.form.get("name_pdf") or invoice_no

    invoices = load_json(HISTORY_FILE, [])
    invoices.append({
        "invoice_no": invoice_no,
        "name": name,
        "service": service,
        "amount": total,
        "date": datetime.now().strftime("%d-%m-%Y")
    })
    save_json(HISTORY_FILE, invoices)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    y = 800

    if logo_path and os.path.exists(logo_path):
        pdf.drawImage(ImageReader(logo_path), 400, y - 40, width=120, height=40, preserveAspectRatio=True)

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, business_name)
    y -= 30
    pdf.drawString(50, y, invoice_title)
    y -= 30

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, y, f"Invoice No: {invoice_no}")
    y -= 20
    pdf.drawString(50, y, f"Date: {datetime.now().strftime('%d-%m-%Y')}")
    y -= 30

    pdf.drawString(50, y, f"Name: {name}")
    y -= 20

    if show_mobile and mobile:
        pdf.drawString(50, y, f"Mobile: {mobile}")
        y -= 20

    pdf.drawString(50, y, f"Purpose: {service}")
    y -= 20
    pdf.drawString(50, y, f"Quantity: {qty}")
    y -= 20
    pdf.drawString(50, y, f"Rate: {currency}{rate:.2f}")
    y -= 20
    pdf.drawString(50, y, f"Total: {currency}{total:.2f}")
    y -= 30

    if show_note and note:
        pdf.drawString(50, y, f"Note: {note}")
        y -= 30

    pdf.drawString(50, 80, "Thank you!")
    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{pdf_name}.pdf",
        mimetype="application/pdf"
    )

# ---------- RUN ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)