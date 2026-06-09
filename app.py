from flask import Flask, render_template, request, redirect, send_file
import mysql.connector
from reportlab.pdfgen import canvas
import os

app = Flask(__name__)

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "AviKedar@MySQL#11!",
    "database": "offer_letter_system"
}


# ==========================
# HOME PAGE
# ==========================
@app.route("/")
def home():

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM candidates")
    candidates = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "index.html",
        candidates=candidates
    )


# ==========================
# ADD CANDIDATE
# ==========================
@app.route("/add", methods=["GET", "POST"])
def add_candidate():

    if request.method == "POST":

        full_name = request.form["full_name"]
        email = request.form["email"]
        college = request.form["college"]
        role_name = request.form["role_name"]
        joining_date = request.form["joining_date"]
        company_name = request.form["company_name"]
        stipend = request.form["stipend"]
        duration = request.form["duration"]

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        query = """
        INSERT INTO candidates
        (
            full_name,
            email,
            college,
            role_name,
            joining_date,
            company_name,
            stipend,
            duration
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """

        values = (
            full_name,
            email,
            college,
            role_name,
            joining_date,
            company_name,
            stipend,
            duration
        )

        cursor.execute(query, values)
        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/")

    return render_template("add_candidate.html")


# ==========================
# OFFER LETTER
# ==========================
@app.route("/generate-offer/<int:id>")
def generate_offer(id):

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM candidates WHERE id=%s",
        (id,)
    )

    candidate = cursor.fetchone()

    cursor.close()
    conn.close()

    if not candidate:
        return "Candidate Not Found"

    os.makedirs("generated/offer_letters", exist_ok=True)

    filename = (
        f"generated/offer_letters/"
        f"Offer_Letter_{candidate[1].replace(' ','_')}.pdf"
    )

    pdf = canvas.Canvas(filename)

    width = 595

    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawCentredString(
        width/2,
        800,
        "TECHNOVA SOLUTIONS"
    )

    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(
        width/2,
        780,
        "Innovating The Future Through Technology"
    )

    pdf.line(50, 765, 545, 765)

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(
        width/2,
        730,
        "OFFER LETTER"
    )

    pdf.setFont("Helvetica", 12)

    pdf.drawString(50, 690, f"Date: {candidate[5]}")
    pdf.drawString(50, 650, f"Dear {candidate[1]},")

    pdf.drawString(
        50,
        610,
        "We are pleased to offer you the position of"
    )

    pdf.setFont("Helvetica-Bold", 12)

    pdf.drawString(
        50,
        585,
        candidate[4]
    )

    pdf.setFont("Helvetica", 12)

    pdf.drawString(
        50,
        560,
        f"at {candidate[6]}"
    )

    pdf.drawString(
        50,
        530,
        f"Duration : {candidate[8]}"
    )

    pdf.drawString(
        50,
        500,
        f"Stipend : {candidate[7]}"
    )

    pdf.drawString(
        50,
        450,
        "We look forward to working with you."
    )

    pdf.line(350, 180, 500, 180)

    pdf.drawString(
        380,
        160,
        "HR Department"
    )

    pdf.drawString(
        360,
        140,
        candidate[6]
    )

    pdf.save()

    return send_file(
        filename,
        as_attachment=True
    )


# ==========================
# CERTIFICATE
# ==========================
@app.route("/generate-certificate/<int:id>")
def generate_certificate(id):

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM candidates WHERE id=%s",
        (id,)
    )

    candidate = cursor.fetchone()

    cursor.close()
    conn.close()

    if not candidate:
        return "Candidate Not Found"

    os.makedirs("generated/certificates", exist_ok=True)

    filename = (
        f"generated/certificates/"
        f"Certificate_{candidate[1].replace(' ','_')}.pdf"
    )

    pdf = canvas.Canvas(filename)

    width = 595

    pdf.rect(30, 30, 535, 782)

    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawCentredString(
        width/2,
        740,
        "CERTIFICATE"
    )

    pdf.setFont("Helvetica", 20)
    pdf.drawCentredString(
        width/2,
        700,
        "OF COMPLETION"
    )

    pdf.setFont("Helvetica", 14)

    pdf.drawCentredString(
        width/2,
        620,
        "This is to certify that"
    )

    pdf.setFont("Helvetica-Bold", 24)

    pdf.drawCentredString(
        width/2,
        570,
        candidate[1].upper()
    )

    pdf.setFont("Helvetica", 14)

    pdf.drawCentredString(
        width/2,
        520,
        "has successfully completed the internship"
    )

    pdf.drawCentredString(
        width/2,
        490,
        f"as a {candidate[4]}"
    )

    pdf.drawCentredString(
        width/2,
        460,
        f"at {candidate[6]}"
    )

    pdf.drawCentredString(
        width/2,
        430,
        f"for a duration of {candidate[8]}"
    )

    pdf.line(380, 180, 520, 180)

    pdf.drawString(
        420,
        160,
        "HR Department"
    )

    pdf.drawString(
        400,
        140,
        candidate[6]
    )

    pdf.save()

    return send_file(
        filename,
        as_attachment=True
    )


if __name__ == "__main__":
    app.run(debug=True)