import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), 'ppam.db')

def verificar_tabla_usuarios():
    """
    Se conecta a la base de datos y cuenta cuántos usuarios hay.
    """
    print(f"🔍 Verificando la base de datos en: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        print("❌ ERROR: El archivo 'ppam.db' no existe. Por favor, ejecuta 'migracion.py' primero.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Contamos las filas en la tabla 'users'
        cursor.execute("SELECT count(*) FROM users")
        total_usuarios = cursor.fetchone()[0]

        print(f"\n✅ RESULTADO: Se encontraron {total_usuarios} usuarios en la base de datos.")

        if total_usuarios == 0:
            print("⚠️ ADVERTENCIA: La tabla está vacía. El problema está en el script 'migracion.py'.")
        else:
            print("👍 INFO: La base de datos tiene datos. El problema está en cómo la aplicación los lee.")

        conn.close()

    except sqlite3.OperationalError as e:
        print(f"❌ ERROR: {e}. La tabla 'users' no existe. La base de datos no se creó correctamente.")

if __name__ == '__main__':
    verificar_tabla_usuarios()