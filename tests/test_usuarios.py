from src.routers import auth as auth_module


# --- US-01: Inicio de sesión ---

def test_login_exitoso_redirige_al_inicio(client):
    response = client.post("/login", data={"email": "operador@logitrack.com", "password": "operador123"},
                           follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"


def test_login_con_password_incorrecta_retorna_error(client):
    response = client.post("/login", data={"email": "operador@logitrack.com", "password": "incorrecta"},
                           follow_redirects=True)
    assert response.status_code == 200
    assert "Usuario o contraseña incorrectos" in response.text


def test_login_con_usuario_no_registrado_retorna_error(client):
    response = client.post("/login", data={"email": "noexiste@logitrack.com", "password": "cualquiera"},
                           follow_redirects=True)
    assert response.status_code == 200
    assert "Usuario o contraseña incorrectos" in response.text


# --- US-02: Cierre de sesión ---

def test_logout_elimina_cookie_y_redirige_al_login(client):
    client.post("/login", data={"email": "operador@logitrack.com", "password": "operador123"})
    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


# --- US-03: Alta de usuario ---

def test_crear_usuario_nuevo_exitosamente(client_admin):
    cantidad_antes = len(auth_module.mock_usuarios)
    response = client_admin.post("/usuarios/nuevo", data={
        "nombre": "Nuevo Usuario",
        "email": "nuevo@logitrack.com",
        "password": "nuevo123",
        "rol_nuevo": "operador",
    }, follow_redirects=False)
    assert response.status_code == 303
    assert len(auth_module.mock_usuarios) == cantidad_antes + 1
    assert auth_module.mock_usuarios[-1].activo is True


def test_crear_usuario_con_email_duplicado_retorna_error(client_admin):
    response = client_admin.post("/usuarios/nuevo", data={
        "nombre": "Duplicado",
        "email": "operador@logitrack.com",
        "password": "pass123",
        "rol_nuevo": "operador",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert "Ya existe un usuario con ese email" in response.text


def test_crear_usuario_sin_ser_admin_redirige(client_operador):
    response = client_operador.post("/usuarios/nuevo", data={
        "nombre": "Test",
        "email": "test@logitrack.com",
        "password": "test123",
        "rol_nuevo": "operador",
    }, follow_redirects=False)
    assert response.status_code == 303


# --- US-04: Listado de usuarios (API) ---

def test_listar_usuarios_api_como_administrador(client):
    response = client.get("/api/usuarios/", headers={"x-rol": "administrador"})
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert "email" in response.json()[0]
    assert "rol" in response.json()[0]


def test_listar_usuarios_api_con_rol_invalido_retorna_403(client):
    response = client.get("/api/usuarios/", headers={"x-rol": "operador"})
    assert response.status_code == 403


# --- US-05: Editar usuario ---

def test_editar_usuario_api_actualiza_nombre_y_rol(client):
    response = client.patch(
        "/api/usuarios/operador@logitrack.com",
        json={"nombre": "Juan Editado", "rol": "supervisor"},
        headers={"x-rol": "administrador"}
    )
    assert response.status_code == 200
    data = response.json()["usuario"]
    assert data["nombre"] == "Juan Editado"
    assert data["rol"] == "supervisor"


def test_editar_usuario_api_con_rol_invalido_retorna_403(client):
    response = client.patch(
        "/api/usuarios/operador@logitrack.com",
        json={"nombre": "Test"},
        headers={"x-rol": "operador"}
    )
    assert response.status_code == 403


def test_editar_usuario_api_inexistente_retorna_404(client):
    response = client.patch(
        "/api/usuarios/noexiste@logitrack.com",
        json={"nombre": "Test"},
        headers={"x-rol": "administrador"}
    )
    assert response.status_code == 404


def test_editar_usuario_api_nombre_muy_corto_retorna_400(client):
    response = client.patch(
        "/api/usuarios/operador@logitrack.com",
        json={"nombre": "A"},
        headers={"x-rol": "administrador"}
    )
    assert response.status_code == 400


def test_editar_usuario_api_rol_invalido_retorna_400(client):
    response = client.patch(
        "/api/usuarios/operador@logitrack.com",
        json={"rol": "superusuario"},
        headers={"x-rol": "administrador"}
    )
    assert response.status_code == 400


def test_editar_usuario_form_admin_actualiza_datos(client_admin):
    response = client_admin.post("/usuarios/operador@logitrack.com/editar", data={
        "nombre": "Juan Modificado",
        "rol_nuevo": "supervisor",
    }, follow_redirects=False)
    assert response.status_code == 303
    u = next(u for u in auth_module.mock_usuarios if u.email == "operador@logitrack.com")
    assert u.nombre == "Juan Modificado"
    assert u.rol == "supervisor"


def test_editar_usuario_form_sin_ser_admin_redirige(client_operador):
    response = client_operador.post("/usuarios/operador@logitrack.com/editar", data={
        "nombre": "Intento",
        "rol_nuevo": "supervisor",
    }, follow_redirects=False)
    assert response.status_code == 303


def test_editar_usuario_form_nombre_corto_muestra_error(client_admin):
    response = client_admin.post("/usuarios/operador@logitrack.com/editar", data={
        "nombre": "A",
        "rol_nuevo": "operador",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert "al menos 2 caracteres" in response.text
