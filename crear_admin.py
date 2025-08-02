from app import app, db
from core.models import User, Role

def crear_usuario_admin():
    """
    Verifica si el rol 'admin' y el usuario 'admin' existen,
    y los crea si no es así.
    """
    print("🔧 Verificando usuario administrador...")

    # Buscamos si el rol 'admin' ya existe
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        print("-> Rol 'admin' no encontrado. Creándolo...")
        admin_role = Role(name='admin')
        db.session.add(admin_role)
        db.session.commit()

    # Buscamos si el usuario 'admin' ya existe
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        print("-> Usuario 'admin' no encontrado. Creándolo con la contraseña 'admin'...")
        admin_user = User(
            username='admin',
            email='admin@ppam.com',
            role=admin_role  # Asignamos el rol de administrador
        )
        admin_user.set_password('admin') # Establecemos la contraseña
        db.session.add(admin_user)
        db.session.commit()
        print("✅ ¡Usuario 'admin' creado exitosamente!")
    else:
        print("👍 El usuario 'admin' ya existe. No se necesita ninguna acción.")

# --- Ejecución del Script ---
if __name__ == '__main__':
    # Usamos el contexto de la aplicación para poder interactuar con la base de datos
    with app.app_context():
        crear_usuario_admin()