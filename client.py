import requests

# --- CONFIGURACIÓN ---
BASE_URL = "http://127.0.0.1:8000"
# Credenciales para las rutas protegidas. ¡Asegúrate de que coincidan con las del servidor!
API_AUTH = ("admin", "supersecret")


# --- FUNCIONES GET (No requieren autenticación) ---
def ver_todas():
    response = requests.get(f"{BASE_URL}/movies")
    if response.ok:
        print("\n--- PRIMERAS 10 PELÍCULAS ---")
        for movie in response.json()[:10]:
            print(f"- {movie['title']} ({movie['year']})")
    else:
        print("Error al obtener películas.")

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

def buscar_por_genero():
    genero = input("Ingrese el género: ")
    response = requests.get(f"{BASE_URL}/movies/genre/{genero}")
    if response.ok:
        movies = response.json()
        print(f"\n--- PELÍCULAS DEL GÉNERO '{genero.title()}' ---")
        for m in movies:
            print(f"- {m['title']} ({m['year']})")
    else:
        print("Error en la consulta.")

def buscar_por_anio():
    anio = input("Ingrese el año: ")
    response = requests.get(f"{BASE_URL}/movies/year/{anio}")
    if response.ok:
        print(f"\n--- PELÍCULAS DEL AÑO {anio} ---")
        for m in response.json():
            print(f"- {m['title']}")
    else:
        print("Error en la consulta.")

# --- FUNCIONES POST, PUT, DELETE (Requieren autenticación) ---

def agregar_pelicula():
    print("\n--- Ingrese los datos de la nueva película ---")
    title = input("Título: ")
    try:
        year = int(input("Año: "))
    except ValueError:
        print("Error: El año debe ser un número.")
        return
        
    cast = input("Actores (separados por coma): ").split(",")
    genres = input("Géneros (separados por coma): ").split(",")
    
    data = {
        "title": title.strip(), "year": year,
        "cast": [c.strip() for c in cast],
        "genres": [g.strip() for g in genres],
    }
    
    # MODIFICADO: Se añade 'auth=API_AUTH' para enviar las credenciales
    response = requests.post(f"{BASE_URL}/movies", json=data, auth=API_AUTH)

    if response.status_code == 201: # Éxito en la creación
        print("Película agregada con éxito.")
    elif response.status_code == 401:
        print("Error: Autenticación fallida. Revisa las credenciales.")
    else:
        # Muestra el error específico que devuelve la API (ej: "La película ya existe")
        print(f"Error ({response.status_code}): {response.json()['detail']}")


def actualizar_pelicula_parcial():
    title_a_actualizar = input("Ingrese el título de la película que desea actualizar: ")
    print("\n--- Ingrese los campos a modificar (deje en blanco para no cambiar) ---")

    update_data = {}
    nuevo_titulo = input(f"Nuevo Título: ")
    if nuevo_titulo:
        update_data["title"] = nuevo_titulo.strip()

    nuevo_anio = input(f"Nuevo Año: ")
    if nuevo_anio:
        try:
            update_data["year"] = int(nuevo_anio)
        except ValueError:
            print("Año inválido, se omitirá.")

    if not update_data:
        print("No se ingresaron datos para actualizar. Operación cancelada.")
        return

    # MODIFICADO: Se añade 'auth=API_AUTH' para enviar las credenciales
    response = requests.put(f"{BASE_URL}/movies/{title_a_actualizar}/partial", json=update_data, auth=API_AUTH)

    if response.ok:
        print("Película actualizada con éxito.")
    elif response.status_code == 401:
        print("Error: Autenticación fallida. Revisa las credenciales.")
    else:
        print(f"Error ({response.status_code}): {response.json()['detail']}")


def borrar_pelicula():
    title = input("Ingrese el título de la película a borrar: ")
    confirm = input(f"¿Está seguro de que desea borrar '{title}'? (s/n): ")
    if confirm.lower() != 's':
        print("Operación cancelada.")
        return

    # MODIFICADO: Se añade 'auth=API_AUTH' para enviar las credenciales
    response = requests.delete(f"{BASE_URL}/movies/{title}", auth=API_AUTH)
    
    if response.ok:
        print(response.json()["message"])
    elif response.status_code == 401:
        print("Error: Autenticación fallida. Revisa las credenciales.")
    else:
        print(f"Error ({response.status_code}): {response.json()['detail']}")

# --- MENÚ PRINCIPAL (Modificado para indicar las rutas protegidas) ---
def menu():
    while True:
        print("\n--- CLIENTE API DE PELÍCULAS ---")
        print("1. Ver primeras películas")
        print("2. Buscar por título")
        print("3. Buscar por género")
        print("4. Buscar por año")
        print("5. Agregar nueva película (requiere auth)")
        print("6. Actualizar película (parcial) (requiere auth)")
        print("7. Borrar película (requiere auth)")
        print("0. Salir")
        
        op = input("Opción: ")
        
        if op == "1": ver_todas()
        elif op == "2": buscar_por_titulo()
        elif op == "3": buscar_por_genero()
        elif op == "4": buscar_por_anio()
        elif op == "5": agregar_pelicula()
        elif op == "6": actualizar_pelicula_parcial()
        elif op == "7": borrar_pelicula()
        elif op == "0": break
        else: print("Opción no válida.")

if __name__ == "__main__":
    menu()