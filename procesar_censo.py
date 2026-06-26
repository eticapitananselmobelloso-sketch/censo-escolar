import imaplib
import email
import os
import sqlite3
import re
from email.header import decode_header
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN DE CREDENCIALES OFICIALES ---
EMAIL_USUARIO = "e.t.icapitananselmobelloso@gmail.com"
EMAIL_PASSWORD = "buhrsfbwqaagookt"  # Clave de aplicación de 16 letras activada

# --- 1. INICIALIZAR BASE DE DATOS LOCAL (SQLite) ---
def inicializar_bd():
    conn = sqlite3.connect('censo_belloso.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS aspirantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_rep TEXT,
            cedula_rep TEXT,
            correo_rep TEXT,
            telefono_rep TEXT,
            nombre_alumno TEXT,
            apellido_alumno TEXT,
            cedula_alumno TEXT,
            edad_alumno INTEGER,
            tipo_ingreso TEXT,
            carrera_cursar TEXT,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("💾 Base de datos local 'censo_belloso.db' verificada y lista para operar.")

# --- 2. EXTRAER DATOS DEL HTML DEL CORREO ---
def extraer_datos_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    texto_plano = soup.get_text(separator=' ')
    
    datos = {}
    
    try:
        # Búsqueda exacta mediante expresiones regulares basadas en las etiquetas del formulario
        datos['nombre_rep'] = re.search(r'Nombres y Apellidos:\s*(.*?)\s*(Nacionalidad:|$)', texto_plano, re.IGNORECASE).group(1).strip()
        datos['cedula_rep'] = re.search(r'Cédula o Pasaporte:\s*(.*?)\s*(Adjuntar|$)', texto_plano, re.IGNORECASE).group(1).strip()
        datos['correo_rep'] = re.search(r'Correo Electrónico:\s*(.*?)\s*(Teléfono|$)', texto_plano, re.IGNORECASE).group(1).strip()
        datos['telefono_rep'] = re.search(r'Teléfono Móvil:\s*(.*?)\s*(País|$)', texto_plano, re.IGNORECASE).group(1).strip()
        
        # Datos del Alumno / Aspirante
        datos['nombre_alumno'] = re.search(r'Nombres del Alumno:\s*(.*?)\s*(Apellidos|$)', texto_plano, re.IGNORECASE).group(1).strip()
        datos['apellido_alumno'] = re.search(r'Apellidos del Alumno:\s*(.*?)\s*(Edad|$)', texto_plano, re.IGNORECASE).group(1).strip()
        datos['edad_alumno'] = int(re.search(r'Edad:\s*(\d+)', texto_plano, re.IGNORECASE).group(1).strip())
        datos['cedula_alumno'] = re.search(r'Cédula del Alumno.*:\s*(.*?)\s*(Adjuntar|$)', texto_plano, re.IGNORECASE).group(1).strip()
        datos['tipo_ingreso'] = re.search(r'Tipo de Ingreso:\s*(.*?)\s*(Carrera|$)', texto_plano, re.IGNORECASE).group(1).strip()
        datos['carrera_cursar'] = re.search(r'Mención a Cursar:\s*(.*?)\s*(Adjuntar|$)', texto_plano, re.IGNORECASE).group(1).strip()
        
    except AttributeError:
        # Si llega un correo con un formato distinto, se descarta limpiamente sin tumbar el script
        return None
        
    return datos

# --- 3. CONEXIÓN Y PROCESAMIENTO DE IMAP ---
def procesar_correos_censo():
    try:
        print("🔌 Conectando de manera segura al IMAP de Gmail del plantel...")
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USUARIO, EMAIL_PASSWORD)
        mail.select("inbox")

        # MODIFICACIÓN: Buscamos "Censo" en cualquier parte del correo para ampliar el criterio
        status, mensajes = mail.search(None, 'TEXT "Censo"')
        id_lista = mensajes[0].split()
        
        if not id_lista:
            print("📭 No se encontraron correos de censo en la bandeja.")
            return

        print(f"📥 Detectados {len(id_lista)} correos potenciales por procesar.")
        
        conn = sqlite3.connect('censo_belloso.db')
        cursor = conn.cursor()

        # Carpeta local para almacenar las fotos tipo carnet y documentos
        if not os.path.exists('documentos_censo'):
            os.makedirs('documentos_censo')

        for e_id in id_lista:
            res, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    cuerpo_html = ""
                    
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))
                            
                            if content_type == "text/html" and "attachment" not in content_disposition:
                                cuerpo_html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            
                            elif "attachment" in content_disposition:
                                nombre_archivo = part.get_filename()
                                if nombre_archivo:
                                    nombre_archivo, encoding = decode_header(nombre_archivo)[0]
                                    if isinstance(nombre_archivo, bytes):
                                        nombre_archivo = nombre_archivo.decode(encoding or "utf-8")
                                    
                                    # Descarga local del archivo binario
                                    ruta_archivo = os.path.join('documentos_censo', nombre_archivo)
                                    with open(ruta_archivo, "wb") as f:
                                        f.write(part.get_payload(decode=True))
                                    print(f"📸 Archivo adjunto guardado en local: {nombre_archivo}")

                    if cuerpo_html:
                        datos = extraer_datos_html(cuerpo_html)
                        if datos:
                            # Inserción limpia en SQLite
                            cursor.execute('''
                                INSERT INTO aspirantes (nombre_rep, cedula_rep, correo_rep, telefono_rep, nombre_alumno, apellido_alumno, cedula_alumno, edad_alumno, tipo_ingreso, carrera_cursar)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (datos['nombre_rep'], datos['cedula_rep'], datos['correo_rep'], datos['telefono_rep'], datos['nombre_alumno'], datos['apellido_alumno'], datos['cedula_alumno'], datos['edad_alumno'], datos['tipo_ingreso'], datos['carrera_cursar']))
                            
                            print(f"✅ Registro exitoso: Alumno {datos['nombre_alumno']} {datos['apellido_alumno']} indexado localmente.")
                            
                            # Marcamos como visto/leído para control interno
                            mail.store(e_id, '+FLAGS', '\\Seen')

        conn.commit()
        conn.close()
        mail.logout()
        print("🏁 Base de datos local actualizada correctamente. Respaldo en la nube preservado.")

    except Exception as e:
        print(f"❌ Error durante el procesamiento: {e}")

if __name__ == "__main__":
    inicializar_bd()
    procesar_correos_censo()
