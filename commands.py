import click
from flask.cli import with_appcontext
from core.models import db, User, Role, Privilegio, Congregacion
import csv
import os
import re

@click.command(name='seed')
@with_appcontext
def seed():
    """
    Comando para poblar la base de datos con los datos iniciales
    desde el archivo contactos.csv.
    """
    csv_path = 'contactos.csv'
    if not os.path.exists(csv_path):
        print(f"-> ERROR: No se encontró el archivo '{csv_path}'.")
        return

    print("-> ✍️  Poblando Roles y Privilegios...")
    roles_a_crear = ['admin', 'editor', 'analyst']
    for role_name in roles_a_crear:
        if not db.session.execute(db.select(Role).filter_by(name=role_name)).scalar_one_or_none():
            db.session.add(Role(name=role_name))
    
    privilegios_a_crear = [
        'Superintendente Viajante', 'Anciano', 'Siervo Ministerial', 
        'Precursor Especial', 'Precursor Regular', 'Precursor Auxiliar', 
        'Publicador', 'Betelita'
    ]
    for priv_name in privilegios_a_crear:
        if not db.session.execute(db.select(Privilegio).filter_by(nombre=priv_name)).scalar_one_or_none():
            db.session.add(Privilegio(nombre=priv_name))
    db.session.commit()

    print("-> 👤 Creando usuario 'admin'...")
    if not db.session.execute(db.select(User).filter_by(username='admin')).scalar_one_or_none():
        admin_role = db.session.execute(db.select(Role).filter_by(name='admin')).scalar_one()
        admin_user = User(username='admin', email='admin@ppam.com', nombre_completo='Administrador del Sistema', role=admin_role)
        admin_user.set_password('admin')
        db.session.add(admin_user)
        db.session.commit()

    # --- LÓGICA COMPLETA PARA MIGRAR CONTACTOS DESDE CSV ---
    with open(csv_path, mode='r', encoding='latin-1') as file:
        csv_reader = csv.DictReader(file, delimiter=';')
        contactos_csv = list(csv_reader)
    
    print(f"-> 🚀 Migrando {len(contactos_csv)} contactos a la tabla de Usuarios...")

    # Crear Congregaciones
    congregaciones_unicas = sorted(list(set((row['Circuito'], row['Congregacion']) for row in contactos_csv if row.get('Congregacion'))))
    mapa_congregacion_id = {}
    for circuito, congregacion_nombre in congregaciones_unicas:
        cong_obj = db.session.execute(db.select(Congregacion).filter_by(nombre=congregacion_nombre, circuito=circuito)).scalar_one_or_none()
        if not cong_obj:
            cong_obj = Congregacion(nombre=congregacion_nombre, circuito=circuito)
            db.session.add(cong_obj)
            db.session.commit()
        mapa_congregacion_id[(circuito, congregacion_nombre)] = cong_obj.id

    # Migrar cada contacto del CSV a la tabla User
    usuarios_creados = 0
    for i, contacto in enumerate(contactos_csv):
        nombre_completo = contacto.get('Nombre', '').strip()
        if not nombre_completo: continue
            
        username_base = re.sub(r'[^a-z0-9.]', '', nombre_completo.lower().replace(' ', '.'))
        username_unico = f"{username_base}.{i}"

        cong_id = mapa_congregacion_id.get((contacto.get('Circuito'), contacto.get('Congregacion')))
        if cong_id:
            if not db.session.execute(db.select(User).filter_by(username=username_unico)).scalar_one_or_none():
                editor_role = db.session.execute(db.select(Role).filter_by(name='editor')).scalar_one()
                nuevo_usuario = User(
                    nombre_completo=nombre_completo,
                    telefono=contacto.get('Telefono'),
                    congregacion_id=cong_id,
                    username=username_unico,
                    email=f"{username_unico}@example.com",
                    role_id=editor_role.id
                )
                nuevo_usuario.set_password('123456') # Contraseña por defecto para publicadores
                db.session.add(nuevo_usuario)
                usuarios_creados += 1
                
    db.session.commit()
    print(f"-> ✅ {usuarios_creados} nuevos publicadores migrados.")
    print("-> ✅ Base de datos poblada exitosamente.")