import requests

# --- CONFIGURACIÓN ---
BASE_URL = "http://127.0.0.1:8000"
# Esta variable guardará las credenciales VALIDADAS solo para la sesión actual
SESION_AUTH = None

### FUNCIÓN DE AUTENTICACIÓN MEJORADA ###
def gestionar_autenticacion():
    """
    Asegura que existan credenciales válidas en la sesión.
    1. Si ya hay credenciales en SESION_AUTH, las devuelve.
    2. Si no, las solicita al usuario.
    3. INMEDIATAMENTE después de solicitarlas, intenta validarlas contra el endpoint /auth/test.
    4. Si la validación es exitosa, guarda las credenciales y las devuelve.
    5. Si la validación falla, muestra un error y devuelve None.
    """
    global SESION_AUTH
    if SESION_AUTH:
        return SESION_AUTH
    
    print("\n--- Se requiere autenticación ---")
    username = input("Usuario: ")
    if not username:
        print("Autenticación cancelada.")
        return None
    password = input("Contraseña: ")
    
    # Preparamos las credenciales para la prueba
    credenciales_nuevas = (username.strip(), password.strip())
    
    # Hacemos la llamada de prueba para validar las credenciales
    print("Verificando credenciales...")
    try:
        response = requests.get(f"{BASE_URL}/auth/test", auth=credenciales_nuevas, timeout=5)
        
        if response.status_code == 200:
            print("¡Autenticación exitosa!")
            SESION_AUTH = credenciales_nuevas # Guardamos las credenciales válidas
            return SESION_AUTH
        elif response.status_code == 401:
            print("\nError: Autenticación fallida. Revisa las credenciales.")
            return None
        else:
            # Otro tipo de error (ej: 404 si el endpoint no existe, 500 en el servidor)
            print(f"\nError inesperado durante la autenticación ({response.status_code}).")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"\nError de conexión con el servidor: {e}")
        return None

# --- FUNCIONES GET (No requieren autenticación) ---
# (Estas funciones no cambian)
def ver_todas():
    try:
        response = requests.get(f"{BASE_URL}/movies")
        if response.ok:
            print("\n--- PRIMERAS 10 PELÍCULAS ---")
            for movie in response.json()[:10]:
                print(f"- {movie['title']} ({movie['year']})")
        else:
            print(f"Error al obtener películas ({response.status_code}).")
    except requests.exceptions.RequestException as e:
        print(f"\nError de conexión con el servidor: {e}")

def buscar_por_titulo():
    title = input("Ingrese el título de la película: ")
    try:
        response = requests.get(f"{BASE_URL}/movies/{title}")
        if response.ok:
            movie = response.json()
            print(f"\n--- {movie['title']} ({movie['year']}) ---")
            print(f"Géneros: {', '.join(movie['genres'])}")
            print(f"Actores: {', '.join(movie['cast'])}")
            print(f"Resumen: {movie.get('extract', 'No disponible')}")
        else:
            print("Película no encontrada.")
    except requests.exceptions.RequestException as e:
        print(f"\nError de conexión con el servidor: {e}")


# --- FUNCIONES POST, PUT, DELETE (Ahora más limpias) ---
def agregar_pelicula():
    # 1. Validar autenticación ANTES de pedir datos
    auth_credenciales = gestionar_autenticacion()
    if not auth_credenciales:
        # El mensaje de error ya se mostró dentro de gestionar_autenticacion()
        return

    # 2. Si la autenticación es correcta, AHORA SÍ pedimos los datos
    print("\n--- Ingrese los datos de la nueva película ---")
    title = input("Título: ")
    try:
        year = int(input("Año: "))
        if year < 0:
            print("Error: El año no puede ser negativo.")
            return
    except ValueError:
        print("Error: El año debe ser un número.")
        return
        
    cast = input("Actores (separados por coma): ").split(",")
    genres = input("Géneros (separados por coma): ").split(",")
    
    data = {"title": title.strip(), "year": year, "cast": [c.strip() for c in cast], "genres": [g.strip() for g in genres]}
    
    try:
        response = requests.post(f"{BASE_URL}/movies", json=data, auth=auth_credenciales)

        if response.status_code == 201:
            print("Película agregada con éxito.")
        else:
            # Aunque ya validamos, algo pudo cambiar (ej: permisos revocados). Es bueno mantener esto.
            print(f"Error ({response.status_code}): {response.json()['detail']}")
            if response.status_code == 401:
                global SESION_AUTH
                SESION_AUTH = None # Borramos las credenciales que ahora son inválidas
    except requests.exceptions.RequestException as e:
        print(f"\nError de conexión con el servidor: {e}")

def actualizar_pelicula_parcial():
    # 1. Validar autenticación ANTES de pedir datos
    auth_credenciales = gestionar_autenticacion()
    if not auth_credenciales:
        return

    # 2. Si la autenticación es correcta, AHORA SÍ pedimos los datos
    title_a_actualizar = input("Ingrese el título de la película que desea actualizar: ")
    print("\n--- Ingrese los campos a modificar (deje en blanco para no cambiar) ---")
    update_data = {}
    nuevo_titulo = input(f"Nuevo Título: ")
    if nuevo_titulo:
        update_data["title"] = nuevo_titulo.strip()
    nuevo_anio = input(f"Nuevo Año: ")
    if nuevo_anio:
        try:
            year_val = int(nuevo_anio)
            if year_val < 0:
                print("Error: El año no puede ser negativo. Se omitirá este campo.")
            else:
                update_data["year"] = year_val
        except ValueError:
            print("Año inválido, se omitirá.")

    if not update_data:
        print("No se ingresaron datos para actualizar. Operación cancelada.")
        return

    try:
        response = requests.put(f"{BASE_URL}/movies/{title_a_actualizar}/partial", json=update_data, auth=auth_credenciales)

        if response.ok:
            print("Película actualizada con éxito.")
        else:
            print(f"Error ({response.status_code}): {response.json()['detail']}")
            if response.status_code == 401:
                global SESION_AUTH
                SESION_AUTH = None 
    except requests.exceptions.RequestException as e:
        print(f"\nError de conexión con el servidor: {e}")


def borrar_pelicula():
    # 1. Validar autenticación ANTES de pedir datos
    auth_credenciales = gestionar_autenticacion()
    if not auth_credenciales:
        return
        
    # 2. Si la autenticación es correcta, AHORA SÍ pedimos los datos
    title = input("Ingrese el título de la película a borrar: ")
    confirm = input(f"¿Está seguro de que desea borrar '{title}'? (s/n): ")
    if confirm.lower() != 's':
        print("Operación cancelada.")
        return

    try:
        response = requests.delete(f"{BASE_URL}/movies/{title}", auth=auth_credenciales)
        
        if response.ok:
            print(response.json()["message"])
        else:
            print(f"Error ({response.status_code}): {response.json()['detail']}")
            if response.status_code == 401:
                global SESION_AUTH
                SESION_AUTH = None
    except requests.exceptions.RequestException as e:
        print(f"\nError de conexión con el servidor: {e}")

# --- MENÚ PRINCIPAL (sin cambios) ---
def menu():
    while True:
        print("\n--- CLIENTE API DE PELÍCULAS ---")
        print("1. Ver primeras películas")
        print("2. Buscar por título")
        print("5. Agregar nueva película (requiere auth)")
        print("6. Actualizar película (parcial) (requiere auth)")
        print("7. Borrar película (requiere auth)")
        print("0. Salir")
        
        op = input("Opción: ")
        
        if op == "1": ver_todas()
        elif op == "2": buscar_por_titulo()
        elif op == "5": agregar_pelicula()
        elif op == "6": actualizar_pelicula_parcial()
        elif op == "7": borrar_pelicula()
        elif op == "0": break
        else: print("Opción no válida.")

if __name__ == "__main__":
    menu()