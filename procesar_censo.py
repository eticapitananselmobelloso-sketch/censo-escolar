import imaplib
import email
import sqlite3
import re
import os
import smtplib
import hashlib
from datetime import datetime
from email.message import EmailMessage
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN ---
EMAIL_USUARIO = "e.t.icapitananselmobelloso@gmail.com"
EMAIL_PASS = "buhrsfbwqaagookt" 
ETIQUETA_GMAIL = "Nuevo Registro de Censo ETI"
CARPETA_ADJUNTOS = "adjuntos_censo"

if not os.path.exists(CARPETA_ADJUNTOS):
    os.makedirs(CARPETA_ADJUNTOS)

def enviar_aviso_duplicado(destinatario, nombre_rep, nombre_alum):
    """Envía un correo personalizado informando del duplicado."""
    if not destinatario or destinatario == "N/A" or "@" not in destinatario:
        return
    try:
        msg = EmailMessage()
        msg['Subject'] = "Aviso: Registro Duplicado en el Censo ETI"
        msg['From'] = EMAIL_USUARIO
        msg['To'] = destinatario
        
        cuerpo = (f"Estimado(a) {nombre_rep},\n\n"
                  f"Le informamos que ya existe un registro previo en nuestra base de datos "
                  f"para el alumno: {nombre_alum}.\n\n"
                  f"Si usted ya completó este proceso anteriormente, no es necesario realizar una nueva solicitud. "
                  f"Si cree que esto es un error, por favor comuníquese con la institución.\n\n"
                  f"Atentamente,\nEscuela Técnica Industrial Capitán Anselmo Belloso.")
        
        msg.set_content(cuerpo)
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_USUARIO, EMAIL_PASS)
            smtp.send_message(msg)
        print(f"📧 Aviso enviado a {destinatario} sobre el alumno: {nombre_alum}")
    except Exception as e:
        print(f"❌ Error al enviar correo de aviso: {e}")

def guardar_foto_unica(nombre_prefijo, contenido):
    """Calcula hash para evitar fotos duplicadas en disco."""
    file_hash = hashlib.md5(contenido).hexdigest()
    nombre_archivo = f"{nombre_prefijo}_{file_hash[:8]}.jpg"
    ruta = os.path.join(CARPETA_ADJUNTOS, nombre_archivo)
    if not os.path.exists(ruta):
        with open(ruta, 'wb') as f:
            f.write(contenido)
    return ruta

def procesar():
    print(f"🚀 Iniciando sincronización...")
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USUARIO, EMAIL_PASS)
        mail.select(f'"{ETIQUETA_GMAIL}"')
        
        _, msgs = mail.search(None, 'ALL')
        ids_correos = msgs[0].split()
        
        conn = sqlite3.connect('censo_belloso.db')
        cursor = conn.cursor()
        
        # Actualización segura de la estructura de la base de datos
        cols_nuevas = ['foto_rep_url', 'foto_alumno_url', 'fecha_registro']
        for col in cols_nuevas:
            try: cursor.execute(f"ALTER TABLE aspirantes ADD COLUMN {col} TEXT")
            except: pass

        campos = ["nombre_rep", "cedula_rep", "email_rep", "telefono_rep", 
                  "pais_origen", "estado_rep", "parroquia_rep", "nombre_alumno", 
                  "apellido_alumno", "edad_alumno", "cedula_alumno", "tipo_ingreso", "carrera_cursar"]

        for e_id in ids_correos:
            try:
                _, data = mail.fetch(e_id, "(RFC822)")
                msg = email.message_from_bytes(data[0][1])
                
                texto_raw = ""
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        texto_raw = part.get_payload(decode=True).decode('utf-8', 'ignore')
                    elif part.get_content_type() == "text/html":
                        texto_raw = BeautifulSoup(part.get_payload(decode=True).decode('utf-8', 'ignore'), 'html.parser').get_text(separator='\n')
                
                def b(etiqueta):
                    pattern = rf"{re.escape(etiqueta)}(.*?)(?={'|'.join([re.escape(c) for c in campos])}|$)"
                    match = re.search(pattern, texto_raw, re.IGNORECASE | re.DOTALL)
                    return match.group(1).strip(" :\n\r") if match else "N/A"

                nombre_rep = b("nombre_rep")
                nombre_alum_full = f"{b('nombre_alumno')} {b('apellido_alumno')}"
                cedula_al = b("cedula_alumno")
                email_form = b("email_rep")

                if cedula_al == "N/A": continue

                cursor.execute("SELECT 1 FROM aspirantes WHERE cedula_alumno = ?", (cedula_al,))
                if cursor.fetchone() is None:
                    # Procesamiento de fotos adjuntas
                    ruta_rep, ruta_alum = "N/A", "N/A"
                    for part in msg.walk():
                        if part.get_content_type().startswith("image/"):
                            contenido = part.get_payload(decode=True)
                            nombre_adj = part.get_filename() or ""
                            if "rep" in nombre_adj.lower(): ruta_rep = guardar_foto_unica("rep", contenido)
                            else: ruta_alum = guardar_foto_unica("alum", contenido)

                    fecha_ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    cursor.execute('''INSERT INTO aspirantes (nombre_rep, cedula_rep, correo_rep, 
                                    telefono_rep, pais_origen, estado_rep, parroquia_rep, nombre_alumno, 
                                    apellido_alumno, edad_alumno, cedula_alumno, tipo_ingreso, carrera_cursar,
                                    foto_rep_url, foto_alumno_url, fecha_registro) 
                                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                                    (nombre_rep, b("cedula_rep"), email_form, b("telefono_rep"), b("pais_origen"), 
                                     b("estado_rep"), b("parroquia_rep"), b("nombre_alumno"), b("apellido_alumno"), 
                                     b("edad_alumno"), cedula_al, b("tipo_ingreso"), b("carrera_cursar"),
                                     ruta_rep, ruta_alum, fecha_ahora))
                    conn.commit()
                    print(f"✅ Guardado: {nombre_alum_full}")
                else:
                    enviar_aviso_duplicado(email_form, nombre_rep, nombre_alum_full)

            except Exception as e:
                print(f"❌ Error en correo {e_id.decode()}: {e}")
        
        conn.close()
        mail.logout()
        print("🏁 Proceso finalizado.")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    procesar()
