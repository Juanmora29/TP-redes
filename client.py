# --- CÓDIGO FINAL DEL CLIENTE (SIN FUNCIÓN DE PRUEBA) ---

import requests
import sys

IP_DEL_SERVIDOR = "PON_AQUI_LA_IP_DE_TU_SERVIDOR"
BASE_URL = None
SESION_AUTH = None

def configurar_servidor():
    global IP_DEL_SERVIDOR, BASE_URL
    if IP_DEL_SERVIDOR == "PON_AQUI_LA_IP_DE_TU_SERVIDOR":
        nueva_ip = input("Por favor, ingresa la dirección IP del servidor: ").strip()
        if not nueva_ip:
            print("\nError: No se ha proporcionado una dirección IP.")
            sys.exit(1)
        IP_DEL_SERVIDOR = nueva_ip
    BASE_URL = f"http://{IP_DEL_SERVIDOR}:8000"
    print(f"\n✅ Servidor configurado para conectarse a: {BASE_URL}")
    try:
        requests.get(f"{BASE_URL}/movies", timeout=3)
        print("✅ ¡Conexión con el servidor exitosa!")
    except requests.exceptions.RequestException:
        print("⚠️  AVISO: No se pudo establecer conexión inicial con el servidor.")

def gestionar_autenticacion():
    global SESION_AUTH
    if SESION_AUTH: return SESION_AUTH
    print("\n--- Se requiere autenticación ---")
    username = input("Usuario: ")
    if not username: print("Autenticación cancelada."); return None
    password = input("Contraseña: ")
    credenciales_nuevas = (username.strip(), password.strip())
    print("Verificando credenciales...")
    try:
        response = requests.get(f"{BASE_URL}/auth/test", auth=credenciales_nuevas, timeout=5)
        if response.status_code == 200:
            print("¡Autenticación exitosa!"); SESION_AUTH = credenciales_nuevas; return SESION_AUTH
        elif response.status_code == 401:
            print("\nError: Autenticación fallida. Revisa las credenciales."); return None
        else:
            print(f"\nError inesperado ({response.status_code})."); return None
    except requests.exceptions.RequestException as e:
        print(f"\nError de conexión con el servidor: {e}"); return None

def ver_todas():
    try:
        response = requests.get(f"{BASE_URL}/movies")
        if response.ok:
            print("\n--- PRIMERAS 10 PELÍCULAS ---")
            for movie in response.json()[:10]: print(f"- {movie['title']} ({movie['year']})")
        else: print(f"Error al obtener películas ({response.status_code}).")
    except requests.exceptions.RequestException as e: print(f"\nError de conexión: {e}")

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
        else: print("Película no encontrada.")
    except requests.exceptions.RequestException as e: print(f"\nError de conexión: {e}")

def buscar_por_anio():
    print("\n--- Buscar películas por año ---")
    year_str = input("Ingrese el año a buscar: ")
    if not year_str.strip(): print("Año no ingresado."); return
    try: year_val = int(year_str)
    except ValueError: print("Error: El año debe ser un número."); return
    try:
        response = requests.get(f"{BASE_URL}/movies", params={'year': year_val})
        if response.ok:
            movies = response.json()
            if not movies: print(f"\nNo se encontraron películas para el año {year_val}."); return
            print(f"\n--- PELÍCULAS DEL AÑO {year_val} ({len(movies)} encontradas) ---")
            for movie in movies: print(f"- {movie['title']}")
        else: print(f"Error en la búsqueda ({response.status_code}).")
    except requests.exceptions.RequestException as e: print(f"\nError de conexión: {e}")

def agregar_pelicula():
    auth = gestionar_autenticacion()
    if not auth: return
    print("\n--- Ingrese los datos de la nueva película ---")
    title = input("Título: ")
    try:
        year = int(input("Año: "))
        if year < 0: print("Error: El año no puede ser negativo."); return
    except ValueError: print("Error: El año debe ser un número."); return
    cast = [c.strip() for c in input("Actores (separados por coma): ").split(",")]
    genres = [g.strip() for g in input("Géneros (separados por coma): ").split(",")]
    data = {"title": title.strip(), "year": year, "cast": cast, "genres": genres}
    try:
        response = requests.post(f"{BASE_URL}/movies", json=data, auth=auth)
        if response.status_code == 201: print("Película agregada con éxito.")
        else:
            print(f"Error ({response.status_code}): {response.json()['detail']}")
            if response.status_code == 401: global SESION_AUTH; SESION_AUTH = None
    except requests.exceptions.RequestException as e: print(f"\nError de conexión: {e}")

def actualizar_pelicula_parcial():
    auth = gestionar_autenticacion()
    if not auth: return
    title_a_actualizar = input("Título de la película a actualizar: ")
    print("\n--- Ingrese los campos a modificar (deje en blanco para no cambiar) ---")
    update_data = {}
    if (t := input("Nuevo Título: ")): update_data["title"] = t.strip()
    if (y := input("Nuevo Año: ")):
        try: update_data["year"] = int(y)
        except ValueError: print("Año inválido, se omitirá.")
    if (c := input("Nuevos Actores (separados por coma): ")): update_data["cast"] = [a.strip() for a in c.split(",")]
    if (g := input("Nuevos Géneros (separados por coma): ")): update_data["genres"] = [gn.strip() for gn in g.split(",")]
    if not update_data: print("No se ingresaron datos."); return
    try:
        response = requests.put(f"{BASE_URL}/movies/{title_a_actualizar}/partial", json=update_data, auth=auth)
        if response.ok: print("Película actualizada.")
        else:
            print(f"Error ({response.status_code}): {response.json()['detail']}")
            if response.status_code == 401: global SESION_AUTH; SESION_AUTH = None
    except requests.exceptions.RequestException as e: print(f"\nError de conexión: {e}")

def borrar_pelicula():
    auth = gestionar_autenticacion()
    if not auth: return
    title = input("Título de la película a borrar: ")
    if input(f"¿Seguro que desea borrar '{title}'? (s/n): ").lower() != 's':
        print("Operación cancelada."); return
    try:
        response = requests.delete(f"{BASE_URL}/movies/{title}", auth=auth)
        if response.ok: print(response.json()["message"])
        else:
            print(f"Error ({response.status_code}): {response.json()['detail']}")
            if response.status_code == 401: global SESION_AUTH; SESION_AUTH = None
    except requests.exceptions.RequestException as e: print(f"\nError de conexión: {e}")

def menu():
    while True:
        print("\n--- CLIENTE API DE PELÍCULAS ---")
        print("1. Ver primeras películas")
        print("2. Buscar por título")
        print("3. Buscar por año")
        print("4. Agregar nueva película (auth)")
        print("5. Actualizar película (auth)")
        print("6. Borrar película (auth)")
        print("0. Salir")
        op = input("Opción: ")
        actions = {"1": ver_todas, "2": buscar_por_titulo, "3": buscar_por_anio,
                   "4": agregar_pelicula, "5": actualizar_pelicula_parcial, "6": borrar_pelicula}
        if op == "0": break
        action = actions.get(op)
        if action: action()
        else: print("Opción no válida.")

if __name__ == "__main__":
    configurar_servidor()
    menu()