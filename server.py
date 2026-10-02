import os
import smtplib
from email.mime.text import MIMEText
from urllib.parse import quote

from dotenv import load_dotenv
from flask import (
    Flask,
    Response,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

import database as db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")

WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "8613535824547")
CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "nyamejonathan9@gmail.com")
INSTAGRAM_URL = os.environ.get(
    "INSTAGRAM_URL", "https://www.instagram.com/the.jan.code"
)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

RATES = {
    "sea_per_cbm": 260,
    "air_per_kg": 19,
    "sea_days": "30–45 days",
    "air_days": "7–14 days",
}

COUNTRIES = [
    "Ghana",
    "Nigeria",
    "Kenya",
    "South Africa",
    "United Kingdom",
    "United States",
    "Canada",
    "Germany",
    "France",
    "Netherlands",
    "United Arab Emirates",
    "Other",
]


def whatsapp_link(text=None):
    if text:
        return f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(text)}"
    return f"https://wa.me/{WHATSAPP_NUMBER}"


@app.context_processor
def inject_globals():
    return {
        "whatsapp_number": WHATSAPP_NUMBER,
        "whatsapp_link": whatsapp_link(),
        "contact_email": CONTACT_EMAIL,
        "instagram_url": INSTAGRAM_URL,
        "rates": RATES,
        "is_admin": session.get("admin") is True,
    }


def clean(value, limit=800):
    return (value or "").strip()[:limit]


def is_spam():
    return bool(clean(request.form.get("website"), 80))


def send_email(subject, body, reply_to=None):
    host = os.environ.get("MAIL_SERVER")
    if not host:
        return False
    try:
        port = int(os.environ.get("MAIL_PORT", 587))
        user = os.environ.get("MAIL_USERNAME", "")
        password = os.environ.get("MAIL_PASSWORD", "")
        use_tls = os.environ.get("MAIL_USE_TLS", "1") != "0"
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = user or CONTACT_EMAIL
        msg["To"] = CONTACT_EMAIL
        if reply_to:
            msg["Reply-To"] = reply_to
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            if use_tls:
                smtp.starttls()
            if user:
                smtp.login(user, password)
            smtp.sendmail(msg["From"], [CONTACT_EMAIL], msg.as_string())
        return True
    except Exception:
        return False


def require_admin():
    if session.get("admin"):
        return None
    return redirect(url_for("office_login", next=request.path))


@app.before_request
def _init():
    db.init_db()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/buy-from-china")
def buy_from_china():
    return render_template("buy_from_china.html")


@app.route("/quote", methods=["GET", "POST"])
def quote():
    if request.method == "POST":
        if is_spam():
            return redirect(url_for("thanks", kind="quote"))
        name = clean(request.form.get("name"), 120)
        email = clean(request.form.get("email"), 180)
        phone = clean(request.form.get("phone"), 60)
        country = clean(request.form.get("country"), 80)
        product = clean(request.form.get("product"), 1200)
        quantity = clean(request.form.get("quantity"), 80)
        shipping_method = clean(request.form.get("shipping_method"), 40)
        budget = clean(request.form.get("budget"), 80)
        message = clean(request.form.get("message"), 1500)
        if not name or not email or not product:
            flash("Please fill in your name, email, and what you want to source.", "error")
            return render_template("quote.html", countries=COUNTRIES, form=request.form)
        db.save_lead(
            kind="quote",
            name=name,
            email=email,
            phone=phone,
            country=country,
            product=product,
            quantity=quantity,
            shipping_method=shipping_method,
            budget=budget,
            message=message,
        )
        body = (
            f"New sourcing quote\n\n"
            f"Name: {name}\n"
            f"Email: {email}\n"
            f"Phone: {phone or '—'}\n"
            f"Country: {country or '—'}\n"
            f"Product: {product}\n"
            f"Quantity: {quantity or '—'}\n"
            f"Shipping: {shipping_method or '—'}\n"
            f"Budget: {budget or '—'}\n"
            f"Notes: {message or '—'}\n"
        )
        send_email(f"Quote from {name}", body, reply_to=email)
        wa = (
            f"Hi, I want a sourcing quote from The Jan Code.\n\n"
            f"Name: {name}\n"
            f"Email: {email}\n"
            f"Phone: {phone or '—'}\n"
            f"Ship to: {country or '—'}\n"
            f"Product: {product}\n"
            f"Quantity: {quantity or '—'}\n"
            f"Shipping: {shipping_method or '—'}\n"
            f"Budget: {budget or '—'}\n"
            f"{message}"
        )
        return redirect(url_for("thanks", kind="quote", wa=wa))
    return render_template("quote.html", countries=COUNTRIES, form={})


@app.route("/shipping")
def shipping():
    return render_template("shipping.html")


@app.route("/faq")
def faq():
    return render_template("faq.html")


@app.route("/track", methods=["GET", "POST"])
def track():
    shipment = None
    query = ""
    searched = False
    if request.method == "POST":
        query = clean(request.form.get("tracking_id"), 40).upper()
        searched = True
        shipment = db.get_shipment(query)
    elif request.args.get("id"):
        query = clean(request.args.get("id"), 40).upper()
        searched = True
        shipment = db.get_shipment(query)
    return render_template(
        "track.html",
        shipment=shipment,
        query=query,
        searched=searched,
        statuses=db.SHIPMENT_STATUSES,
    )


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        if is_spam():
            return redirect(url_for("thanks", kind="contact"))
        name = clean(request.form.get("name"), 120)
        email = clean(request.form.get("email"), 180)
        message = clean(request.form.get("message"), 2000)
        if not name or not email or not message:
            flash("Please fill in your name, email, and message.", "error")
            return render_template("contact.html")
        db.save_lead(kind="contact", name=name, email=email, message=message)
        body = f"Contact message from {name} <{email}>\n\n{message}\n"
        send_email(f"Contact from {name}", body, reply_to=email)
        wa = f"Hi, this is {name} ({email}).\n\n{message}"
        return redirect(url_for("thanks", kind="contact", wa=wa))
    return render_template("contact.html")


@app.route("/thanks")
def thanks():
    kind = request.args.get("kind", "quote")
    wa_text = request.args.get("wa", "")
    return render_template(
        "thanks.html",
        kind=kind,
        wa_url=whatsapp_link(wa_text) if wa_text else whatsapp_link(),
    )


@app.route("/shop")
def shop():
    return render_template("shop.html")


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    return redirect(url_for("shop"))


@app.route("/login")
@app.route("/register")
@app.route("/logout")
@app.route("/cart")
@app.route("/checkout")
@app.route("/orders")
def old_pages():
    return redirect(url_for("contact"))


@app.route("/office/login", methods=["GET", "POST"])
def office_login():
    if session.get("admin"):
        return redirect(url_for("office"))
    error = None
    if request.method == "POST":
        password = request.form.get("password") or ""
        if ADMIN_PASSWORD and password == ADMIN_PASSWORD:
            session["admin"] = True
            nxt = request.args.get("next") or url_for("office")
            if not nxt.startswith("/"):
                nxt = url_for("office")
            return redirect(nxt)
        error = (
            "Wrong password."
            if ADMIN_PASSWORD
            else "Set ADMIN_PASSWORD in your environment first."
        )
    return render_template("office_login.html", error=error)


@app.route("/office/logout")
def office_logout():
    session.pop("admin", None)
    return redirect(url_for("home"))


@app.route("/office", methods=["GET", "POST"])
def office():
    gate = require_admin()
    if gate:
        return gate
    if request.method == "POST":
        action = request.form.get("action")
        if action == "save_shipment":
            tracking_id = db.upsert_shipment(
                tracking_id=clean(request.form.get("tracking_id"), 40),
                customer_name=clean(request.form.get("customer_name"), 120),
                destination=clean(request.form.get("destination"), 120),
                method=clean(request.form.get("method"), 40),
                status=clean(request.form.get("status"), 40) or "Received",
                note=clean(request.form.get("note"), 500),
            )
            flash(f"Saved {tracking_id}.", "success")
        elif action == "delete_shipment":
            db.delete_shipment(clean(request.form.get("tracking_id"), 40))
            flash("Shipment removed.", "success")
        return redirect(url_for("office"))
    return render_template(
        "office.html",
        leads=db.list_leads(),
        shipments=db.list_shipments(),
        statuses=db.SHIPMENT_STATUSES,
        next_id=db.next_tracking_id(),
    )


@app.route("/robots.txt")
def robots():
    body = f"User-agent: *\nAllow: /\nDisallow: /office\nSitemap: {request.url_root.rstrip('/')}/sitemap.xml\n"
    return Response(body, mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap():
    pages = [
        "home",
        "buy_from_china",
        "quote",
        "shipping",
        "faq",
        "track",
        "contact",
        "shop",
    ]
    loc = "".join(
        f"  <url><loc>{url_for(name, _external=True)}</loc></url>\n" for name in pages
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{loc}</urlset>\n"
    )
    return Response(xml, mimetype="application/xml")


if __name__ == "__main__":
    db.init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
