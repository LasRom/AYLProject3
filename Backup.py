import smtplib
import os
import zipfile

import mimetypes
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(addr_to, msg_subj, msg_text, files):
    addr_from = "rlastuvka43@gmail.com"
    password = "LoLoLoshka12345"

    msg = MIMEMultipart()
    msg['From'] = addr_from
    msg['To'] = addr_to
    msg['Subject'] = msg_subj

    body = msg_text
    msg.attach(MIMEText(body, 'plain'))

    process_attachement(msg, files)
    server = smtplib.SMTP('smtp.gmail.com: 587')
    server.starttls()

    server.login(addr_from, password)
    server.send_message(msg)
    server.quit()


def process_attachement(msg, files):
    for f in files:
        if os.path.isfile(f):
            attach_file(msg, f)
        elif os.path.exists(f):
            dir = os.listdir(f)
            for file in dir:
                attach_file(msg, f + "/" + file)


def attach_file(msg, filepath):
    filename = os.path.basename(filepath)
    ctype, encoding = mimetypes.guess_type(filepath)
    if ctype is None or encoding is not None:
        ctype = 'application/octet-stream'
    maintype, subtype = ctype.split('/', 1)

    with open(filepath, 'rb') as fp:
        file = MIMEBase(maintype, subtype)
        file.set_payload(fp.read())
        fp.close()
        encoders.encode_base64(file)
    file.add_header('Content-Disposition', 'attachment', filename=filename)
    msg.attach(file)


def make_reserve_arc(source, dest):
    zip = zipfile.ZipFile(dest, 'w')
    for folder, subfolders, files in os.walk(source):

        for file in files:
            zip.write(os.path.join(folder, file),
                      os.path.relpath(os.path.join(folder, file), source),
                      compress_type=zipfile.ZIP_DEFLATED)

    zip.close()
