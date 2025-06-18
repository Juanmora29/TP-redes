import requests

# --- CONFIGURACIÓN ---
BASE_URL = "http://127.0.0.1:8000"
# Esta variable guardará las credenciales solo para la sesión actual
SESION_AUTH = None

### NUEVA FUNCIÓN: Se encarga de pedir y guardar las credenciales ###
def gestionar_autenticacion():
    """Verifica si ya hay credenciales en la sesión. Si no, las solicita."""
    global SESION_AUTH
    if SESION_AUTH:
        return SESION_AUTH
    
    print("\n--- Se requiere autenticación ---")
    username = input("Usuario: ")
    if not username:
        return None
    password = input("Contraseña: ")
    
    SESION_AUTH = (username.strip(), password.strip())
    return SESION_AUTH

# --- FUNCIONES GET (No requieren autenticación) ---
def ver_todas():
    response = requests.get(f"{BASE_URL}/movies")
    if response.ok:
        print("\n--- PRIMERAS 10 PELÍCULAS ---")
        for movie in response.json()[:10]:
            print(f"- {movie['title']} ({movie['year']})")
    else:
        print(f"Error al obtener películas ({response.status_code}).")

def buscar_por_titulo():
    title = input("Ingrese el título de la película: ")
    response = requests.get(f"{BASE_URL}/movies/{title}")
    if response.ok:
        movie = response.json()
        print(f"\n--- {movie['title']} ({movie['year']}) ---")
        print(f"Géneros: {', '.join(movie['genres'])}")
        print(f"Actores: {', '.join(movie['cast'])}")
        print(f"Resumen: {movie.get('extract', 'No disponible')}")
    else:
        print("Película no encontrada.")

# --- FUNCIONES POST, PUT, DELETE (Requieren autenticación) ---
def agregar_pelicula():
    auth_credenciales = gestionar_autenticacion()
    if not auth_credenciales:
        print("Operación cancelada. No se proporcionaron credenciales.")
        return

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
    
    response = requests.post(f"{BASE_URL}/movies", json=data, auth=auth_credenciales)

    if response.status_code == 201:
        print("Película agregada con éxito.")
    elif response.status_code == 401:
        print("Error: Autenticación fallida. Revisa las credenciales.")
        global SESION_AUTH
        SESION_AUTH = None # Borra las credenciales incorrectas
    else:
        print(f"Error ({response.status_code}): {response.json()['detail']}")

def actualizar_pelicula_parcial():
    auth_credenciales = gestionar_autenticacion()
    if not auth_credenciales:
        print("Operación cancelada. No se proporcionaron credenciales.")
        return

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

    response = requests.put(f"{BASE_URL}/movies/{title_a_actualizar}/partial", json=update_data, auth=auth_credenciales)

    if response.ok:
        print("Película actualizada con éxito.")
    elif response.status_code == 401:
        print("Error: Autenticación fallida. Revisa las credenciales.")
        global SESION_AUTH
        SESION_AUTH = None # Borra las credenciales incorrectas
    else:
        print(f"Error ({response.status_code}): {response.json()['detail']}")

def borrar_pelicula():
    auth_credenciales = gestionar_autenticacion()
    if not auth_credenciales:
        print("Operación cancelada. No se proporcionaron credenciales.")
        return
        
    title = input("Ingrese el título de la película a borrar: ")
    confirm = input(f"¿Está seguro de que desea borrar '{title}'? (s/n): ")
    if confirm.lower() != 's':
        print("Operación cancelada.")
        return

    response = requests.delete(f"{BASE_URL}/movies/{title}", auth=auth_credenciales)
    
    if response.ok:
        print(response.json()["message"])
    elif response.status_code == 401:
        print("Error: Autenticación fallida. Revisa las credenciales.")
        global SESION_AUTH
        SESION_AUTH = None # Borra las credenciales incorrectas
    else:
        print(f"Error ({response.status_code}): {response.json()['detail']}")

# --- MENÚ PRINCIPAL ---
def menu():
    # He eliminado las opciones 3 y 4 del menú ya que no estaban en tu último código
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