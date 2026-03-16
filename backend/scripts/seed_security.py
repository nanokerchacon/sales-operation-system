from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.auth import ClientAssignment, Permission, Role, RolePermission, User, UserRole
from app.models.client import Client


ROLE_DEFINITIONS = {
    "direccion_general": "Dirección General",
    "comercial": "Comercial",
    "finanzas": "Finanzas",
    "admin": "Administrador",
}

PERMISSIONS = {
    "dashboard.view": ("dashboard", "view", "Access dashboard", False),
    "clients.view": ("clients", "view", "View clients", False),
    "clients.create": ("clients", "create", "Create clients", False),
    "orders.view": ("orders", "view", "View orders", False),
    "orders.create": ("orders", "create", "Create orders", False),
    "deliveries.view": ("deliveries", "view", "View deliveries", False),
    "deliveries.create": ("deliveries", "create", "Create deliveries", False),
    "invoices.view": ("invoices", "view", "View invoices", False),
    "invoices.create": ("invoices", "create", "Create invoices", False),
    "products.view": ("products", "view", "View products", False),
    "products.create": ("products", "create", "Create products", False),
    "incidents.view": ("incidents", "view", "View incidents", False),
    "admin.view": ("admin", "view", "View administration", False),
    "admin.manage_users": ("admin", "manage_users", "Manage users", True),
    "admin.manage_roles": ("admin", "manage_roles", "Manage roles", True),
    "admin.assign_clients": ("admin", "assign_clients", "Assign clients", True),
}

ROLE_PERMISSIONS = {
    "direccion_general": set(PERMISSIONS.keys()),
    "admin": set(PERMISSIONS.keys()),
    "comercial": {
        "dashboard.view",
        "clients.view",
        "clients.create",
        "orders.view",
        "orders.create",
        "deliveries.view",
        "invoices.view",
        "products.view",
        "incidents.view",
    },
    "finanzas": {
        "dashboard.view",
        "clients.view",
        "orders.view",
        "deliveries.view",
        "deliveries.create",
        "invoices.view",
        "invoices.create",
        "products.view",
        "incidents.view",
    },
}

TEST_USERS = [
    ("direccion@local", "Local123!", "Dirección General", "direccion_general"),
    ("comercial@local", "Local123!", "Comercial Demo", "comercial"),
    ("finanzas@local", "Local123!", "Finanzas Demo", "finanzas"),
    ("admin@local", "Local123!", "Administrador Demo", "admin"),
]


def main() -> None:
    db = SessionLocal()
    try:
        role_map = {}
        for code, name in ROLE_DEFINITIONS.items():
            role = db.query(Role).filter(Role.code == code).first()
            if role is None:
                role = Role(code=code, name=name, description=name)
                db.add(role)
                db.flush()
            role_map[code] = role

        permission_map = {}
        for code, (module, action, description, is_sensitive) in PERMISSIONS.items():
            permission = db.query(Permission).filter(Permission.code == code).first()
            if permission is None:
                permission = Permission(
                    code=code,
                    module=module,
                    action=action,
                    description=description,
                    is_sensitive=is_sensitive,
                )
                db.add(permission)
                db.flush()
            permission_map[code] = permission

        for role_code, permission_codes in ROLE_PERMISSIONS.items():
            role = role_map[role_code]
            for permission_code in permission_codes:
                permission = permission_map[permission_code]
                exists = (
                    db.query(RolePermission)
                    .filter(RolePermission.role_id == role.id, RolePermission.permission_id == permission.id)
                    .first()
                )
                if exists is None:
                    db.add(RolePermission(role_id=role.id, permission_id=permission.id))

        user_map = {}
        for email, password, full_name, default_role_code in TEST_USERS:
            user = db.query(User).filter(User.email == email).first()
            password_hash = hash_password(password)
            if user is None:
                user = User(
                    email=email,
                    password_hash=password_hash,
                    full_name=full_name,
                    default_role_code=default_role_code,
                    is_active=True,
                )
                db.add(user)
                db.flush()
            else:
                user.password_hash = password_hash
                user.full_name = full_name
                user.default_role_code = default_role_code
                user.is_active = True
                db.add(user)

            user_map[default_role_code] = user

            role = role_map[default_role_code]
            if (
                db.query(UserRole)
                .filter(UserRole.user_id == user.id, UserRole.role_id == role.id)
                .first()
                is None
            ):
                db.add(UserRole(user_id=user.id, role_id=role.id))

        commercial = user_map.get("comercial")
        if commercial is not None:
            client_ids = [row.id for row in db.query(Client.id).order_by(Client.id.asc()).limit(3).all()]
            for client_id in client_ids:
                exists = (
                    db.query(ClientAssignment)
                    .filter(ClientAssignment.client_id == client_id, ClientAssignment.user_id == commercial.id)
                    .first()
                )
                if exists is None:
                    db.add(ClientAssignment(client_id=client_id, user_id=commercial.id, assignment_role="account_owner"))

        db.commit()
        print("Security seed completed")
        for email, password, _, role_code in TEST_USERS:
            print(f"- {email} / {password} ({role_code})")
    finally:
        db.close()


if __name__ == "__main__":
    main()

