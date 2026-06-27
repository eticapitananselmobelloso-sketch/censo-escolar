import imaplib
import email
import sqlite3
import re
from bs4 import BeautifulSoup

def inicializar_bd():
    conn = sqlite3.connect('censo_belloso.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS aspirantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_rep TEXT, nacionalidad_rep TEXT, cedula_rep TEXT, correo_rep TEXT, 
            telefono_rep TEXT, pais_origen TEXT, estado_rep TEXT, parroquia_rep TEXT, 
            foto_rep_url TEXT, nombre_alumno TEXT, apellido_alumno TEXT, edad_alumno INTEGER, 
            cedula_alumno TEXT, tipo_ingreso TEXT, carrera_cursar TEXT, foto_alumno_url TEXT
        )
    ''')
    conn.commit()
    conn.close()

def procesar():
    inicializar_bd()
    print("💾 Base de datos lista. Conectando a Gmail...")
    
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login("e.t.icapitananselmobelloso@gmail.com", "buhrsfbwqaagookt")
    mail.select("inbox")
    
    _, msgs = mail.search(None, 'TEXT "Censo"')
    
    for e_id in msgs[0].split():
        _, data = mail.fetch(e_id, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])
        cuerpo = ""
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                cuerpo = part.get_payload(decode=True).decode('utf-8', 'ignore')
        
        if cuerpo:
            soup = BeautifulSoup(cuerpo, 'html.parser')
            texto = soup.get_text(separator=' ')
            
            def b(etiqueta):
                m = re.search(f"{etiqueta}:\s*(.*?)(?=\s*[A-Z][a-z]+:|$)", texto, re.IGNORECASE | re.DOTALL)
                return m.group(1).strip() if m else "N/A"

            nombre_al = b("Nombres del Alumno")
            
            if nombre_al != "N/A":
                conn = sqlite3.connect('censo_belloso.db')
                cursor = conn.cursor()
                cursor.execute('''INSERT INTO aspirantes VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                    (b("Nombres y Apellidos"), b("Nacionalidad"), b("Cédula o Pasaporte"), b("Correo Electrónico"), 
                     b("Teléfono Móvil"), b("País de Origen"), b("Estado"), b("Parroquia de Habitación"), 
                     b("foto_rep_url"), nombre_al, b("Apellidos del Alumno"), 
                     int(re.search(r'Edad:\s*(\d+)', texto).group(1)) if re.search(r'Edad:\s*(\d+)', texto) else 0,
                     b("Cédula del Alumno"), b("Tipo de Ingreso"), b("Carrera / Especialidad"), b("foto_alumno_url")))
                conn.commit()
                conn.close()
                print(f"✅ Procesado alumno: {nombre_al}")
        
        mail.store(e_id, '+FLAGS', '\\Seen')
    mail.logout()
    print("🏁 Proceso finalizado.")

if __name__ == "__main__":
    procesar()
