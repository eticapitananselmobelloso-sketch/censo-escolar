import imaplib
import email
import sqlite3
import re
import os
from bs4 import BeautifulSoup

# Configuración
ETIQUETA_GMAIL = "Nuevo Registro de Censo ETI"
CARPETA_ADJUNTOS = "adjuntos_censo"

# Asegurar que la carpeta de adjuntos exista
if not os.path.exists(CARPETA_ADJUNTOS):
    os.makedirs(CARPETA_ADJUNTOS)

def procesar():
    print(f"💾 Conectando a: {ETIQUETA_GMAIL}...")
    
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login("e.t.icapitananselmobelloso@gmail.com", "buhrsfbwqaagookt")
        mail.select(f'"{ETIQUETA_GMAIL}"')
        
        # Procesamos todos los correos
        _, msgs = mail.search(None, 'ALL')
        
        conn = sqlite3.connect('censo_belloso.db')
        cursor = conn.cursor()
        
        for e_id in msgs[0].split():
            _, data = mail.fetch(e_id, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            
            cuerpo = ""
            adjuntos = []
            
            # Recorrer partes del correo para buscar texto y adjuntos
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    cuerpo = part.get_payload(decode=True).decode('utf-8', 'ignore')
                elif part.get_content_disposition() == 'attachment':
                    adjuntos.append(part)
            
            if cuerpo:
                soup = BeautifulSoup(cuerpo, 'html.parser')
                texto = soup.get_text(separator=' ')
                
                def b(etiqueta):
                    patron = rf"{re.escape(etiqueta)}\s+(.*)"
                    m = re.search(patron, texto, re.IGNORECASE)
                    return m.group(1).strip() if m else "N/A"

                cedula_al = b("cedula_alumno")
                nombre_al = b("nombre_alumno")

                # Verificamos si la cédula ya existe
                cursor.execute("SELECT 1 FROM aspirantes WHERE cedula_alumno = ?", (cedula_al,))
                if cursor.fetchone() is None and nombre_al != "N/A":
                    
                    # Guardar adjuntos físicamente
                    rutas_adjuntos = {"foto_rep_url": "N/A", "foto_alumno_url": "N/A"}
                    for adj in adjuntos:
                        nombre_archivo = adj.get_filename()
                        if nombre_archivo:
                            # Creamos un nombre seguro para el archivo
                            ruta_final = os.path.join(CARPETA_ADJUNTOS, f"{cedula_al}_{nombre_archivo}")
                            with open(ruta_final, 'wb') as f:
                                f.write(adj.get_payload(decode=True))
                            
                            # Clasificar según el nombre del archivo
                            if "alumno" in nombre_archivo.lower():
                                rutas_adjuntos["foto_alumno_url"] = ruta_final
                            else:
                                rutas_adjuntos["foto_rep_url"] = ruta_final

                    edad = int(b("edad_alumno")) if b("edad_alumno").isdigit() else 0
                    
                    cursor.execute('''INSERT INTO aspirantes (nombre_rep, nacionalidad_rep, cedula_rep, correo_rep, 
                        telefono_rep, pais_origen, estado_rep, parroquia_rep, foto_rep_url, nombre_alumno, 
                        apellido_alumno, edad_alumno, cedula_alumno, tipo_ingreso, carrera_cursar, foto_alumno_url) 
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                        (b("nombre_rep"), b("nacionalidad_rep"), b("cedula_rep"), b("email_rep"), 
                         b("telefono_rep"), b("pais_origen"), b("estado_rep"), b("parroquia_rep"), 
                         rutas_adjuntos["foto_rep_url"], nombre_al, b("apellido_alumno"), edad,
                         cedula_al, b("tipo_ingreso"), b("carrera_cursar"), rutas_adjuntos["foto_alumno_url"]))
                    
                    conn.commit()
                    print(f"✅ Procesado y guardado: {nombre_al}")
                else:
                    print(f"ℹ️ Omitido (ya existe o incompleto): {nombre_al}")
        
        conn.close()
        mail.logout()
        print("\n🏁 Proceso finalizado.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    procesar()
