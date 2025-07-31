import csv
import sqlite3
import os
import random

def migrar_desde_csv():
    """
    Lee datos desde un archivo CSV y los guarda en una nueva base de datos SQLite.
    Este método no necesita pyodbc y es a prueba de errores de drivers.
    """
    csv_path = 'contactos.csv'
    db_nueva_path = 'ppam.db'

    # --- 1. Verificar si existe el archivo CSV ---
    if not os.path.exists(csv_path):
        print(f"❌ ERROR: No se encontró el archivo '{csv_path}'.")
        print("Asegúrate de que esté en la misma carpeta que este script.")
        return

    # --- 2. Conectar a SQLite (se crea si no existe) ---
    print(f"🚀 Creando o conectando a la nueva base de datos en '{db_nueva_path}'...")
    conn_nueva = sqlite3.connect(db_nueva_path)
    cursor_nueva = conn_nueva.cursor()

    # --- 3. Crear las nuevas tablas en SQLite ---
    print("🏗️ Creando estructura de tablas (Congregaciones, Territorios, Contactos)...")
    cursor_nueva.execute("DROP TABLE IF EXISTS Territorios;")
    cursor_nueva.execute("DROP TABLE IF EXISTS Contactos;")
    cursor_nueva.execute("DROP TABLE IF EXISTS Congregaciones;")

    cursor_nueva.execute("""
        CREATE TABLE Congregaciones (
            CongregacionID INTEGER PRIMARY KEY AUTOINCREMENT,
            NombreCongregacion TEXT NOT NULL,
            Circuito TEXT NOT NULL
        );
    """)
    cursor_nueva.execute("""
        CREATE TABLE Territorios (
            TerritorioID INTEGER PRIMARY KEY AUTOINCREMENT,
            NombreTerritorio TEXT NOT NULL,
            CongregacionID_FK INTEGER NOT NULL,
            FOREIGN KEY (CongregacionID_FK) REFERENCES Congregaciones (CongregacionID)
        );
    """)
    cursor_nueva.execute("""
        CREATE TABLE Contactos (
            ContactoID INTEGER PRIMARY KEY AUTOINCREMENT,
            Nombre TEXT NOT NULL,
            Telefono TEXT,
            CongregacionID_FK INTEGER NOT NULL,
            FOREIGN KEY (CongregacionID_FK) REFERENCES Congregaciones (CongregacionID)
        );
    """)
    conn_nueva.commit()

    # --- 4. Leer los datos desde el archivo CSV ---
    print(f"📖 Leyendo datos de '{csv_path}'...")
    with open(csv_path, mode='r', encoding='latin-1') as file:
        csv_reader = csv.DictReader(file, delimiter=';')
        contactos_originales = list(csv_reader)
    print(f"✅ Se encontraron {len(contactos_originales)} registros en el CSV.")

    # --- 5. Poblar las nuevas tablas ---
    print("✍️  Escribiendo datos en la nueva base de datos...")
    
    congregaciones_unicas = sorted(list(set((row['Circuito'], row['Congregacion']) for row in contactos_originales if row['Congregacion'])))
    mapa_congregacion_id = {}
    for circuito, congregacion in congregaciones_unicas:
        cursor_nueva.execute("INSERT INTO Congregaciones (NombreCongregacion, Circuito) VALUES (?, ?)", (congregacion, circuito))
        mapa_congregacion_id[(circuito, congregacion)] = cursor_nueva.lastrowid
    conn_nueva.commit()

    for contacto in contactos_originales:
        cong_id = mapa_congregacion_id.get((contacto['Circuito'], contacto['Congregacion']))
        if cong_id:
            cursor_nueva.execute("INSERT INTO Contactos (Nombre, Telefono, CongregacionID_FK) VALUES (?, ?, ?)",
            (contacto['Nombre'], contacto['Telefono'], cong_id))
    conn_nueva.commit()
    
    nombres_territorios_pool = [
        "Los Guaritos", "La Pica", "El Furrial", "Boquerón", "Las Cocuizas", "San Simón", "Santa Inés", 
        "Alto de los Godos", "La Cruz", "Jusepín", "El Corozo", "San Vicente", "La Toscana", "Puertas del Sur",
        "Lomas del Viento", "El Paraíso", "La Floresta", "Costó Arriba", "Mercado Viejo", "Plaza Piar"
    ]
    for cong_id in mapa_congregacion_id.values():
        territorios_asignados = random.sample(nombres_territorios_pool, min(10, len(nombres_territorios_pool)))
        for territorio in territorios_asignados:
            cursor_nueva.execute("INSERT INTO Territorios (NombreTerritorio, CongregacionID_FK) VALUES (?, ?)", (territorio, cong_id))
    conn_nueva.commit()

    conn_nueva.close()
    print("\n🎉 ¡Migración completada con éxito! 🎉")
    print(f"El archivo '{db_nueva_path}' ha sido creado a partir de tu archivo CSV.")

if __name__ == '__main__':
    migrar_desde_csv()