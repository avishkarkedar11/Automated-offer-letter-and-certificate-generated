from flask import Flask, render_template, request, redirect, send_file
import mysql.connector
from reportlab.pdfgen import canvas
import os
import qrcode
from PIL import Image
import smtplib
from email.message import EmailMessage
import pandas as pd
from flask import session
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    send_file,
    session
)

app = Flask(__name__)
app.secret_key = "HR_AUTOMATION_SECRET_KEY_2026"

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "AviKedar@MySQL#11!",
    "database": "offer_letter_system"
}

#login route
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM admins
            WHERE email=%s AND password=%s
            """,
            (email, password)
        )

        admin = cursor.fetchone()

        cursor.close()
        conn.close()

        if admin:

            session["admin"] = admin[1]

            return redirect("/")

        return render_template(
            "login.html",
            error="Invalid Email or Password"
        )

    return render_template("login.html")

#home protection route
@app.route("/")
def home():

    if "admin" not in session:
        return redirect("/login")

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
 
 #logout route
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")
   
#csv upload route
@app.route("/upload-csv", methods=["GET", "POST"])
def upload_csv():

    if request.method == "POST":

        file = request.files["csv_file"]

        os.makedirs("uploads", exist_ok=True)

        filepath = os.path.join(
            "uploads",
            file.filename
        )

        os.makedirs("uploads", exist_ok=True)

        filepath = os.path.join(
            "uploads",
             file.filename
        )

        file.save(filepath)
        
        df = pd.read_csv(r"C:\Users\avish\Downloads\sample_candidates_upload.csv")

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        for _, row in df.iterrows():

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
                row["full_name"],
                row["email"],
                row["college"],
                row["role_name"],
                pd.to_datetime(
                    row["joining_date"],
                    dayfirst=True
                ).strftime("%Y-%m-%d"),
                row["company_name"],
                row["stipend"],
                row["duration"]
            )

            cursor.execute(query, values)

        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/")

    return render_template("upload_csv.html")

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
        width / 2,
        800,
        "TECHNOVA SOLUTIONS"
    )

    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(
        width / 2,
        780,
        "Innovating The Future Through Technology"
    )

    pdf.line(50, 765, 545, 765)

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(
        width / 2,
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
    pdf.drawString(50, 585, candidate[4])

    pdf.setFont("Helvetica", 12)

    pdf.drawString(50, 560, f"at {candidate[6]}")
    pdf.drawString(50, 530, f"Duration : {candidate[8]}")
    pdf.drawString(50, 500, f"Stipend : {candidate[7]}")

    pdf.drawString(
        50,
        450,
        "We look forward to working with you."
    )

    pdf.line(350, 180, 500, 180)

    pdf.drawString(380, 160, "HR Department")
    pdf.drawString(360, 140, candidate[6])

    pdf.save()

    return send_file(
        filename,
        as_attachment=True
    )

@app.route("/delete/<int:id>")
def delete_candidate(id):

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM candidates WHERE id=%s",
        (id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_candidate(id):

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    if request.method == "POST":

        full_name = request.form["full_name"]
        email = request.form["email"]
        college = request.form["college"]
        role_name = request.form["role_name"]
        joining_date = request.form["joining_date"]
        company_name = request.form["company_name"]
        stipend = request.form["stipend"]
        duration = request.form["duration"]

        query = """
        UPDATE candidates
        SET
        full_name=%s,
        email=%s,
        college=%s,
        role_name=%s,
        joining_date=%s,
        company_name=%s,
        stipend=%s,
        duration=%s
        WHERE id=%s
        """

        values = (
            full_name,
            email,
            college,
            role_name,
            joining_date,
            company_name,
            stipend,
            duration,
            id
        )

        cursor.execute(query, values)
        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/")

    cursor.execute(
        "SELECT * FROM candidates WHERE id=%s",
        (id,)
    )

    candidate = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "edit_candidate.html",
        candidate=candidate
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

    certificate_id = candidate[9]

    os.makedirs("generated/certificates", exist_ok=True)
    os.makedirs("generated/qr_codes", exist_ok=True)

    verification_url = (
        f"http://127.0.0.1:5000/verify/{certificate_id}"
    )

    qr_path = (
        f"generated/qr_codes/{certificate_id}.png"
    )

    qr = qrcode.make(verification_url)
    qr.save(qr_path)

    filename = (
        f"generated/certificates/"
        f"Certificate_{candidate[1].replace(' ','_')}.pdf"
    )

    pdf = canvas.Canvas(filename)

    width = 595

    pdf.rect(30, 30, 535, 782)

    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawCentredString(
        width / 2,
        740,
        "CERTIFICATE"
    )

    pdf.setFont("Helvetica", 20)
    pdf.drawCentredString(
        width / 2,
        700,
        "OF COMPLETION"
    )

    pdf.setFont("Helvetica", 14)

    pdf.drawCentredString(
        width / 2,
        620,
        "This is to certify that"
    )

    pdf.setFont("Helvetica-Bold", 24)

    pdf.drawCentredString(
        width / 2,
        570,
        candidate[1].upper()
    )

    pdf.setFont("Helvetica", 14)

    pdf.drawCentredString(
        width / 2,
        520,
        "has successfully completed the internship"
    )

    pdf.drawCentredString(
        width / 2,
        490,
        f"as a {candidate[4]}"
    )

    pdf.drawCentredString(
        width / 2,
        460,
        f"at {candidate[6]}"
    )

    pdf.drawCentredString(
        width / 2,
        430,
        f"for a duration of {candidate[8]}"
    )

    pdf.drawCentredString(
        width / 2,
        380,
        f"Certificate ID: {certificate_id}"
    )

    pdf.drawImage(
        qr_path,
        430,
        220,
        width=80,
        height=80
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
    
    
#send email with attachment  
def send_email_with_attachment(
    recipient_email,
    subject,
    body,
    attachment_path
):

    sender_email = "avikedar04@gmail.com"
    app_password = "tqdj mlcz jktb kecw"

    msg = EmailMessage()

    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient_email

    msg.set_content(body)

    with open(attachment_path, "rb") as file:
        msg.add_attachment(
            file.read(),
            maintype="application",
            subtype="pdf",
            filename=attachment_path.split("/")[-1]
        )

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465
    ) as smtp:

        smtp.login(
            sender_email,
            app_password
        )

        smtp.send_message(msg)
        
@app.route("/send-offer/<int:id>")
def send_offer(id):

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

    filename = (
        f"generated/offer_letters/"
        f"Offer_Letter_{candidate[1].replace(' ','_')}.pdf"
    )

    send_email_with_attachment(
        candidate[2],
        "Offer Letter",
        "Please find your offer letter attached.",
        filename
    )

    return redirect("/")            


# ==========================
# VERIFY CERTIFICATE
# ==========================
@app.route("/verify/<certificate_id>")
def verify_certificate(certificate_id):

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM candidates WHERE certificate_id=%s",
        (certificate_id,)
    )

    candidate = cursor.fetchone()

    cursor.close()
    conn.close()

    if not candidate:
        return """
        <h1 style='color:red'>
        Certificate Not Found ❌
        </h1>
        """

    return f"""
    <html>
    <head>
        <title>Certificate Verification</title>
    </head>

    <body style="font-family:Arial;padding:40px">

        <h1 style="color:green">
            Certificate Verified ✅
        </h1>

        <hr>

        <h3>Name: {candidate[1]}</h3>
        <h3>Email: {candidate[2]}</h3>
        <h3>Role: {candidate[4]}</h3>
        <h3>Company: {candidate[6]}</h3>
        <h3>Duration: {candidate[8]}</h3>
        <h3>Certificate ID: {candidate[9]}</h3>

    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(debug=True)