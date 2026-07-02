import sqlite3

def preparar_sistema():
    # Conectamos a la base de datos (se creará si no existe)
    conn = sqlite3.connect('censo_belloso.db')
    cursor = conn.cursor()

    # 1. Crear la tabla de usuarios si no existe
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (id INTEGER PRIMARY KEY, usuario TEXT UNIQUE, password TEXT)''')

    # 2. Insertar el usuario administrador (admin/admin123)
    # Usamos "INSERT OR IGNORE" para no dar error si el usuario ya fue creado antes
    try:
        cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, password) VALUES (?, ?)", 
                       ('admin', 'admin123'))
        conn.commit()
        print("✅ Base de datos verificada y usuario 'admin' listo.")
    except Exception as e:
        print(f"❌ Ocurrió un error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    preparar_sistema()
