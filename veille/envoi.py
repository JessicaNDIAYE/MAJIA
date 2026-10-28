"""Envoi du digest par e-mail via SMTP (Gmail par défaut)."""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def envoyer(sujet, texte, html):
    hote = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "465"))
    utilisateur = os.environ["SMTP_USER"]
    destinataires = [a.strip() for a in os.environ["EMAIL_TO"].split(",") if a.strip()]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = sujet
    msg["From"] = utilisateur
    msg["To"] = ", ".join(destinataires)
    msg.attach(MIMEText(texte, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP_SSL(hote, port, timeout=60) as smtp:
        smtp.login(utilisateur, os.environ["SMTP_PASSWORD"])
        smtp.sendmail(utilisateur, destinataires, msg.as_string())
