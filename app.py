from flask import Flask, render_template, request, redirect, send_file
import mysql.connector
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
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
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", "AviKedar@MySQL#11!"),
    "database": os.environ.get("DB_DATABASE", "offer_letter_system"),
    "port": int(os.environ.get("DB_PORT", 3306))
}

# Helper to resolve file paths for serverless vs local environments
def get_file_path(subdir, filename):
    if "VERCEL" in os.environ:
        base_dir = os.path.join("/tmp", "generated", subdir)
    else:
        base_dir = os.path.join("generated", subdir)
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, filename)

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

#home protectionroute
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

        # Parse CSV stream directly in-memory
        df = pd.read_csv(file)

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
def homepage():

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

    certificate_id = candidate[9]
    if not certificate_id:
        import datetime
        year = datetime.datetime.now().year
        certificate_id = f"CERT-{year}-{id:04d}"
        
        # Update database with auto-generated certificate_id
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE candidates SET certificate_id=%s WHERE id=%s",
            (certificate_id, id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        # Refresh candidate data
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM candidates WHERE id=%s",
            (id,)
        )
        candidate = cursor.fetchone()
        cursor.close()
        conn.close()

    filename = get_file_path("offer_letters", f"Offer_Letter_{candidate[1].replace(' ','_')}.pdf")

    # Initialize A4 Portrait Canvas
    pdf = canvas.Canvas(filename, pagesize=A4)
    width, height = A4 # 595.27, 841.89

    # ----------------------------------------------------
    # HEADER RIBBONS & ACCENTS
    # ----------------------------------------------------
    # Top dark band
    pdf.setFillColor(HexColor("#080b11"))
    pdf.rect(0, 825, width, 17, fill=True, stroke=False)
    
    # Gold highlight line below band
    pdf.setFillColor(HexColor("#e5b842"))
    pdf.rect(0, 820, width, 5, fill=True, stroke=False)
    
    # Silver thin accent
    pdf.setFillColor(HexColor("#cbd5e1"))
    pdf.rect(0, 817, width, 3, fill=True, stroke=False)

    # ----------------------------------------------------
    # BRAND LOGO & COMPANY INFO (LETTERHEAD)
    # ----------------------------------------------------
    logo_path = "static/logo.jpg"
    if os.path.exists(logo_path):
        # Draw logo with a thin gold border frame
        pdf.drawImage(logo_path, 50, 735, width=60, height=60)
        pdf.setStrokeColor(HexColor("#e5b842"))
        pdf.setLineWidth(1)
        pdf.rect(50, 735, 60, 60, stroke=True, fill=False)

    # Brand Name and Slogan
    pdf.setFillColor(HexColor("#080b11"))
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(125, 770, "HORYZEN TECHNOLOGIES")
    
    pdf.setFillColor(HexColor("#e5b842"))
    pdf.setFont("Helvetica-Bold", 7.5)
    pdf.drawString(125, 755, "INNOVATING THE FUTURE THROUGH TECHNOLOGY")

    # Contact Info on Top Right
    pdf.setFillColor(HexColor("#64748b"))
    pdf.setFont("Helvetica", 9)
    pdf.drawRightString(width - 50, 780, "official@horyzen.in")
    pdf.drawRightString(width - 50, 765, "+91 8788492408")
    pdf.setFillColor(HexColor("#e5b842"))
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawRightString(width - 50, 750, "www.horyzen.in")

    # Sleek dividing border line
    pdf.setStrokeColor(HexColor("#e2e8f0"))
    pdf.setLineWidth(1)
    pdf.line(50, 715, width - 50, 715)

    # ----------------------------------------------------
    # DOCUMENT HEADER
    # ----------------------------------------------------
    pdf.setFillColor(HexColor("#080b11"))
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawCentredString(width / 2, 675, "LETTER OF INTERNSHIP APPOINTMENT")
    
    # Draw a small gold bar under the header
    pdf.setFillColor(HexColor("#e5b842"))
    pdf.rect(width/2 - 40, 665, 80, 2.5, fill=True, stroke=False)

    # ----------------------------------------------------
    # RECIPIENT & DATES
    # ----------------------------------------------------
    pdf.setFillColor(HexColor("#080b11"))
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(50, 620, "To,")
    
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 605, candidate[1].upper()) # Name
    
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(HexColor("#475569"))
    pdf.drawString(50, 590, candidate[3]) # College

    # Subject Line
    pdf.setFillColor(HexColor("#080b11"))
    pdf.setFont("Helvetica-Bold", 10.5)
    pdf.drawString(50, 550, f"Subject: Letter of Internship Appointment - {candidate[6]}")

    # ----------------------------------------------------
    # BODY TEXT
    # ----------------------------------------------------
    pdf.setFont("Helvetica", 10.5)
    pdf.setFillColor(HexColor("#1e293b"))
    
    y = 515
    line_height = 18
    
    salutation = f"Dear {candidate[1]},"
    pdf.drawString(50, y, salutation)
    y -= line_height * 1.5
    
    p1 = f"We are pleased to offer you the position of Intern at {candidate[6]} in the"
    pdf.drawString(50, y, p1)
    y -= line_height
    
    p1_sub = f"role of {candidate[4]}. Your skills and enthusiasm have impressed us,"
    pdf.drawString(50, y, p1_sub)
    y -= line_height
    
    p1_end = "and we are excited to have you join our technical team."
    pdf.drawString(50, y, p1_end)
    y -= line_height * 1.5
    
    # Format date nicely
    joining_date_str = candidate[5].strftime("%d %B %Y") if hasattr(candidate[5], 'strftime') else str(candidate[5])
    
    p2 = f"Your internship is scheduled to begin on {joining_date_str} for a duration of"
    pdf.drawString(50, y, p2)
    y -= line_height
    
    p2_sub = f"{candidate[8]}. During this training period, you will receive a monthly stipend of"
    pdf.drawString(50, y, p2_sub)
    y -= line_height
    
    p2_end = f"INR {candidate[7]}/- and you will gain practical, hands-on experience by working on"
    pdf.drawString(50, y, p2_end)
    y -= line_height
    
    p2_end2 = "industry-scale tasks and building domain-related skills."
    pdf.drawString(50, y, p2_end2)
    y -= line_height * 1.5
    
    p3 = "We value innovation, commitment, and collaboration. We are dedicated to providing"
    pdf.drawString(50, y, p3)
    y -= line_height
    
    p3_sub = "a productive learning environment where you can grow, contribute, and develop"
    pdf.drawString(50, y, p3_sub)
    y -= line_height
    
    p3_end = "foundational professional competencies."
    pdf.drawString(50, y, p3_end)
    y -= line_height * 1.5
    
    p4 = "Upon successful completion of the internship, you will receive a verified certificate"
    pdf.drawString(50, y, p4)
    y -= line_height
    
    p4_sub = "and may be considered for future opportunities based on your performance."
    pdf.drawString(50, y, p4_sub)

    # ----------------------------------------------------
    # CLOSING & SIGNATURE / SEALS
    # ----------------------------------------------------
    # Bottom Left - Unique IDs & Date
    bottom_y = 175
    pdf.setFillColor(HexColor("#475569"))
    pdf.setFont("Helvetica-Bold", 8.5)
    pdf.drawString(50, bottom_y, "UNIQUE IDENTIFIER:")
    pdf.setFont("Courier-Bold", 9)
    pdf.setFillColor(HexColor("#e5b842"))
    pdf.drawString(50, bottom_y - 13, certificate_id)
    
    pdf.setFillColor(HexColor("#475569"))
    pdf.setFont("Helvetica-Bold", 8.5)
    pdf.drawString(50, bottom_y - 35, "DATE OF ISSUE:")
    pdf.setFont("Helvetica", 9)
    pdf.setFillColor(HexColor("#1e293b"))
    
    import datetime
    current_date_str = datetime.datetime.now().strftime("%d %B %Y")
    pdf.drawString(50, bottom_y - 47, current_date_str)

    # Bottom Right - Signature & Seal
    pdf.setFillColor(HexColor("#080b11"))
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawRightString(width - 50, bottom_y, "Thank you,")
    pdf.setFont("Helvetica-Bold", 10.5)
    pdf.setFillColor(HexColor("#e5b842"))
    pdf.drawRightString(width - 50, bottom_y - 15, f"Team {candidate[6]}")
    
    # Hand-drawn styled Signature
    pdf.setFont("Times-BoldItalic", 15)
    pdf.setFillColor(HexColor("#1d4ed8")) # Royal Blue ink
    pdf.drawRightString(width - 65, bottom_y - 43, "Avishkar Kedar")
    
    # Stamp role
    pdf.setFont("Helvetica-Bold", 8.5)
    pdf.setFillColor(HexColor("#475569"))
    pdf.drawRightString(width - 50, bottom_y - 60, "Co-Founder & Director")


    # ----------------------------------------------------
    # FOOTER ACCENTS
    # ----------------------------------------------------
    # Bottom gold stripe
    pdf.setFillColor(HexColor("#e5b842"))
    pdf.rect(0, 15, width, 5, fill=True, stroke=False)
    # Bottom dark stripe
    pdf.setFillColor(HexColor("#080b11"))
    pdf.rect(0, 0, width, 15, fill=True, stroke=False)

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
    if not certificate_id:
        import datetime
        year = datetime.datetime.now().year
        certificate_id = f"CERT-{year}-{id:04d}"
        
        # Update database with auto-generated certificate_id
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE candidates SET certificate_id=%s WHERE id=%s",
            (certificate_id, id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        # Refresh candidate data
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM candidates WHERE id=%s",
            (id,)
        )
        candidate = cursor.fetchone()
        cursor.close()
        conn.close()

    verification_url = (
        f"http://127.0.0.1:5000/verify/{certificate_id}"
    )

    qr_path = get_file_path("qr_codes", f"{certificate_id}.png")

    qr = qrcode.make(verification_url)
    qr.save(qr_path)

    filename = get_file_path("certificates", f"Certificate_{candidate[1].replace(' ','_')}.pdf")

    from reportlab.lib.pagesizes import landscape
    # Initialize landscape A4 canvas
    pdf = canvas.Canvas(filename, pagesize=landscape(A4))
    width, height = landscape(A4) # 841.89, 595.27

    # ----------------------------------------------------
    # DUAL BORDER LAYOUT
    # ----------------------------------------------------
    # Outer dark slate border
    pdf.setStrokeColor(HexColor("#080b11"))
    pdf.setLineWidth(3)
    pdf.rect(20, 20, width - 40, height - 40, fill=False, stroke=True)

    # Inner gold border
    pdf.setStrokeColor(HexColor("#e5b842"))
    pdf.setLineWidth(1.25)
    pdf.rect(26, 26, width - 52, height - 52, fill=False, stroke=True)

    # Draw solid gold triangles in the 4 inner corners as elegant accents
    # Top-Left corner accent
    p = pdf.beginPath()
    p.moveTo(26, height - 26)
    p.lineTo(46, height - 26)
    p.lineTo(26, height - 46)
    p.close()
    pdf.setFillColor(HexColor("#e5b842"))
    pdf.drawPath(p, fill=True, stroke=False)
    
    # Top-Right corner accent
    p = pdf.beginPath()
    p.moveTo(width - 26, height - 26)
    p.lineTo(width - 46, height - 26)
    p.lineTo(width - 26, height - 46)
    p.close()
    pdf.drawPath(p, fill=True, stroke=False)
    
    # Bottom-Left corner accent
    p = pdf.beginPath()
    p.moveTo(26, 26)
    p.lineTo(46, 26)
    p.lineTo(26, 46)
    p.close()
    pdf.drawPath(p, fill=True, stroke=False)
    
    # Bottom-Right corner accent
    p = pdf.beginPath()
    p.moveTo(width - 26, 26)
    p.lineTo(width - 46, 26)
    p.lineTo(width - 26, 46)
    p.close()
    pdf.drawPath(p, fill=True, stroke=False)

    # ----------------------------------------------------
    # BRAND LOGO (CENTERED)
    # ----------------------------------------------------
    logo_path = "static/logo.jpg"
    if os.path.exists(logo_path):
        # Draw logo with a thin gold border frame
        pdf.drawImage(logo_path, width/2 - 27, 470, width=54, height=54)
        pdf.setStrokeColor(HexColor("#e5b842"))
        pdf.setLineWidth(1.25)
        pdf.circle(width/2, 497, 28, stroke=True, fill=False)

    # ----------------------------------------------------
    # CERTIFICATE HEADER
    # ----------------------------------------------------
    pdf.setFillColor(HexColor("#080b11"))
    pdf.setFont("Helvetica-Bold", 26)
    pdf.drawCentredString(width / 2, 427, "CERTIFICATE OF COMPLETION")

    # Decorative gold highlight ribbon under title
    pdf.setFillColor(HexColor("#e5b842"))
    pdf.rect(width/2 - 70, 415, 140, 2.5, fill=True, stroke=False)

    # ----------------------------------------------------
    # PRESENTATION CONTENT
    # ----------------------------------------------------
    pdf.setFont("Helvetica", 12.5)
    pdf.setFillColor(HexColor("#475569"))
    pdf.drawCentredString(width / 2, 377, "This is proudly presented to")

    # Candidate Name (bold, uppercase, Horyzen gold accent color)
    pdf.setFont("Helvetica-Bold", 24)
    pdf.setFillColor(HexColor("#e5b842"))
    pdf.drawCentredString(width / 2, 335, candidate[1].upper())
    
    # Decorative line under name
    pdf.setStrokeColor(HexColor("#cbd5e1"))
    pdf.setLineWidth(0.75)
    pdf.line(width/2 - 130, 320, width/2 + 130, 320)

    pdf.setFont("Helvetica", 12.5)
    pdf.setFillColor(HexColor("#475569"))
    pdf.drawCentredString(width / 2, 292, "for successfully completing their training program as an active")

    # Candidate Role Name
    pdf.setFont("Helvetica-Bold", 15.5)
    pdf.setFillColor(HexColor("#080b11"))
    pdf.drawCentredString(width / 2, 262, candidate[4])

    # Company name and duration
    pdf.setFont("Helvetica", 12.5)
    pdf.setFillColor(HexColor("#475569"))
    pdf.drawCentredString(width / 2, 234, f"at {candidate[6]}")

    joining_date_str = candidate[5].strftime("%d %B %Y") if hasattr(candidate[5], 'strftime') else str(candidate[5])
    pdf.drawCentredString(
        width / 2,
        206,
        f"for a duration of {candidate[8]} starting from {joining_date_str}."
    )

    # ----------------------------------------------------
    # FOOTER LOGS & SIGNATURES
    # ----------------------------------------------------
    # Bottom Left: ID details
    bottom_y = 125
    pdf.setFont("Helvetica-Bold", 8.5)
    pdf.setFillColor(HexColor("#475569"))
    pdf.drawString(60, bottom_y, "CERTIFICATE ID:")
    pdf.setFont("Courier-Bold", 9)
    pdf.setFillColor(HexColor("#e5b842"))
    pdf.drawString(60, bottom_y - 12, certificate_id)

    pdf.setFont("Helvetica-Bold", 8.5)
    pdf.setFillColor(HexColor("#475569"))
    pdf.drawString(60, bottom_y - 32, "DATE OF ISSUE:")
    pdf.setFont("Helvetica", 9)
    pdf.setFillColor(HexColor("#1e293b"))
    
    import datetime
    current_date_str = datetime.datetime.now().strftime("%d %B %Y")
    pdf.drawString(60, bottom_y - 44, current_date_str)

    # Bottom Center: Secure QR Code
    pdf.drawImage(qr_path, width/2 - 28, 70, width=56, height=56)
    pdf.setFont("Helvetica-Bold", 6.5)
    pdf.setFillColor(HexColor("#64748b"))
    pdf.drawCentredString(width/2, 60, "SECURE VERIFICATION QR")

    # Bottom Right: Seal & Signature Block
    # Signature line & text
    pdf.setStrokeColor(HexColor("#cbd5e1"))
    pdf.setLineWidth(1)
    pdf.line(width - 210, 110, width - 70, 110)
    
    # Hand-written signature script
    pdf.setFont("Times-BoldItalic", 14)
    pdf.setFillColor(HexColor("#1d4ed8")) # Blue ink
    pdf.drawCentredString(width - 140, 120, "Team HR")
    
    pdf.setFont("Helvetica-Bold", 8.5)
    pdf.setFillColor(HexColor("#475569"))
    pdf.drawCentredString(width - 140, 95, "HR Department")
    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(HexColor("#64748b"))
    pdf.drawCentredString(width - 140, 82, candidate[6])

    # Elegant Gold Seal on the left side of signature
    seal_x = width - 265
    seal_y = bottom_y - 35
    pdf.setStrokeColor(HexColor("#e5b84266"))
    pdf.setLineWidth(1)
    pdf.circle(seal_x, seal_y, 22, stroke=True, fill=False)
    pdf.circle(seal_x, seal_y, 19, stroke=True, fill=False)
    
    pdf.setFont("Helvetica-Bold", 3.5)
    pdf.setFillColor(HexColor("#e5b842"))
    pdf.drawCentredString(seal_x, seal_y + 7, "HORYZEN")
    pdf.drawCentredString(seal_x, seal_y + 2, "TECHNOLOGIES")
    pdf.setFont("Helvetica-Bold", 3)
    pdf.drawCentredString(seal_x, seal_y - 5, "* SECURE *")
    pdf.drawCentredString(seal_x, seal_y - 10, "SEAL")

    pdf.save()

    return send_file(
        filename,
        as_attachment=True
    )
    
    
#send email with attachment  
def send_email_with_attachment(
    recipient_email,
    subject,
    body_text,
    html_content,
    attachment_path
):

    sender_email = "avikedar04@gmail.com"
    app_password = "tqdj mlcz jktb kecw"

    msg = EmailMessage()

    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient_email

    # Plain text fallback
    msg.set_content(body_text)

    # HTML Content alternative
    msg.add_alternative(html_content, subtype="html")

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

    filename = get_file_path("offer_letters", f"Offer_Letter_{candidate[1].replace(' ','_')}.pdf")
    
    joining_date_str = candidate[5].strftime("%d %B %Y") if hasattr(candidate[5], 'strftime') else str(candidate[5])

    subject = f"Internship Offer Letter - {candidate[1]}"
    body_text = (
        f"Dear {candidate[1]},\n\n"
        f"Congratulations! We are pleased to offer you the position of Intern at {candidate[6]} "
        f"in the role of {candidate[4]}.\n\n"
        f"Please find your official offer letter attached to this email. It outlines the details of "
        f"your role, duration ({candidate[8]}), joining date ({joining_date_str}), and stipend (INR {candidate[7]}/mo).\n\n"
        f"We look forward to working with you.\n\n"
        f"Best regards,\n"
        f"HR Team\n"
        f"{candidate[6]}"
    )

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Internship Offer Letter</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f1f5f9; color: #1e293b; margin: 0; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);">
        <div style="background-color: #080b11; padding: 30px; text-align: center; border-bottom: 4px solid #e5b842;">
            <h1 style="color: #ffffff; margin: 0; font-size: 22px; font-weight: bold; letter-spacing: 1px;">HORYZEN TECHNOLOGIES</h1>
            <p style="color: #e5b842; margin: 5px 0 0 0; font-size: 10px; text-transform: uppercase; letter-spacing: 2px; font-weight: bold;">Innovating The Future Through Technology</p>
        </div>
        <div style="padding: 40px 30px; line-height: 1.6;">
            <h2 style="color: #080b11; font-size: 22px; margin-top: 0;">Congratulations, {candidate[1]}!</h2>
            <p>We are absolutely thrilled to extend our formal offer for your internship with <strong>{candidate[6]}</strong>. Based on your impressive profile and interview performance, we believe you will be a valuable addition to our engineering team.</p>
            
            <p>Please review the key details of your internship below:</p>
            
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #e5b842; border-radius: 8px; padding: 20px; margin: 25px 0;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 6px 0; font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600; width: 50%;">Role</td>
                        <td style="padding: 6px 0; font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600; width: 50%;">Joining Date</td>
                    </tr>
                    <tr>
                        <td style="padding: 0 0 12px 0; font-size: 14px; color: #0f172a; font-weight: bold;">{candidate[4]}</td>
                        <td style="padding: 0 0 12px 0; font-size: 14px; color: #0f172a; font-weight: bold;">{joining_date_str}</td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600;">Stipend</td>
                        <td style="padding: 6px 0; font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600;">Duration</td>
                    </tr>
                    <tr>
                        <td style="padding: 0; font-size: 14px; color: #e5b842; font-weight: bold;">INR {candidate[7]}/month</td>
                        <td style="padding: 0; font-size: 14px; color: #0f172a; font-weight: bold;">{candidate[8]}</td>
                    </tr>
                </table>
            </div>
            
            <p>Your official appointment letter is attached to this email. Please review the complete details, and feel free to reach out if you have any questions.</p>
            
            <p>We look forward to welcoming you on board and embarking on this exciting learning journey together.</p>
            
            <p style="margin-top: 30px; line-height: 1.4;">Best regards,<br><strong style="color: #080b11;">HR Department</strong><br><span style="color: #e5b842; font-weight: bold;">{candidate[6]}</span></p>
        </div>
        <div style="background-color: #f8fafc; padding: 20px 30px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0;">
            <p style="margin: 0 0 8px 0;">&copy; 2026 Horyzen Technologies. All rights reserved.</p>
            <p style="margin: 0;"><a href="mailto:official@horyzen.in" style="color: #e5b842; text-decoration: none; font-weight: bold;">official@horyzen.in</a> | +91 98350 51934 | <a href="https://www.horyzen.in" style="color: #e5b842; text-decoration: none; font-weight: bold;">www.horyzen.in</a></p>
        </div>
    </div>
</body>
</html>"""

    send_email_with_attachment(
        candidate[2],
        subject,
        body_text,
        html_content,
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