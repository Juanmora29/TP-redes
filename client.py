# IMPORTACIONES 


import requests # La librería principal para realizar peticiones HTTP a la API.
import sys      # Se usa para poder terminar el programa si no se proporciona una IP.



# CONFIGURACIÓN Y VARIABLES GLOBALES

# El usario va a remplazar este valor cuando inicia el script.
IP_DEL_SERVIDOR = "PON_AQUI_LA_IP_DE_TU_SERVIDOR"

# Variables globales que se llenarán durante la ejecución.
BASE_URL = None      # Almacenará la URL completa del servidor 
SESION_AUTH = None   # "Cache" para las credenciales.



# FUNCIONES DE CONFIGURACIÓN Y AUTENTICACIÓN 


def configurar_servidor():
    """
    Se ejecuta al inicio. Pide la IP del servidor si no está definida y
    realiza una prueba de conexión para verificar que el servidor es accesible.
    """
    global IP_DEL_SERVIDOR, BASE_URL
    
    # Si la IP no ha sido modificada en el código, la pide al usuario.
    if IP_DEL_SERVIDOR == "PON_AQUI_LA_IP_DE_TU_SERVIDOR":
        nueva_ip = input("Por favor, ingresa la dirección IP del servidor: ").strip()
        if not nueva_ip:
            print("\nError: No se ha proporcionado una dirección IP. El programa terminará.")
            sys.exit(1)
        IP_DEL_SERVIDOR = nueva_ip
        
    # Construye la URL base que usarán todas las demás funciones.
    BASE_URL = f"http://{IP_DEL_SERVIDOR}:8000"
    print(f"\n✅ Servidor configurado para conectarse a: {BASE_URL}")
    
    # Intenta hacer una pequeña petición para ver si el servidor responde.
    try:
        requests.get(f"{BASE_URL}/movies/count", timeout=3)
        print("✅ ¡Conexión con el servidor exitosa!")
    except requests.exceptions.RequestException:
        print("⚠️  AVISO: No se pudo establecer conexión inicial con el servidor.")
        print("   Asegúrate de que la IP es correcta y el servidor está en ejecución.")

def gestionar_autenticacion():
    """
    Maneja el login. Si ya hay una sesión válida, la devuelve.
    Si no, pide usuario/contraseña y los verifica contra el endpoint /auth/test.
    """
    global SESION_AUTH
    
    # Si ya nos hemos logueado antes, reutilizamos las credenciales.
    if SESION_AUTH:
        return SESION_AUTH
        
    print("\n--- Se requiere autenticación ---")
    username = input("Usuario: ")
    if not username:
        print("Autenticación cancelada.")
        return None
    password = input("Contraseña: ")
    credenciales_nuevas = (username.strip(), password.strip())
    
    print("Verificando credenciales...")
    try:
        # Llama al endpoint de prueba de la API para validar las credenciales.
        response = requests.get(f"{BASE_URL}/auth/test", auth=credenciales_nuevas, timeout=5)
        if response.status_code == 200:
            print("¡Autenticación exitosa!")
            SESION_AUTH = credenciales_nuevas  # Guarda las credenciales para futuras peticiones.
            return SESION_AUTH
        elif response.status_code == 401:
            print("\nError: Autenticación fallida. Revisa las credenciales.")
            return None
        else:
            print(f"\nError inesperado durante la autenticación ({response.status_code}).")
            return None
    except requests.exceptions.RequestException as e:
        print(f"\nError de conexión con el servidor: {e}")
        return None



# FUNCIONES DE INTERACCIÓN CON LA API 

# Cada una de estas funciones corresponde a una acción que el usuario puede realizar.

def ver_cantidad_peliculas():
    """Llama al endpoint /movies/count para obtener el total de películas."""
    try:
        response = requests.get(f"{BASE_URL}/movies/count")
        if response.ok:
            count = response.json().get("total_movies", "desconocido")
            print(f"\n📊 Total de películas en la base de datos: {count}")
        else:
            print(f"Error al obtener la cantidad ({response.status_code}).")
    except requests.exceptions.RequestException as e:
        print(f"\nError de conexión: {e}")

def buscar_por_titulo():
    """Pide un título al usuario y llama al endpoint /movies/{title} para buscarlo."""
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
        print(f"\nError de conexión: {e}")

def buscar_por_anio():
    """Pide un año y llama al endpoint /movies?year=... para filtrar."""
    print("\n--- Buscar películas por año ---")
    year_str = input("Ingrese el año a buscar: ")
    if not year_str.strip():
        print("Año no ingresado."); return
    try:
        year_val = int(year_str)
    except ValueError:
        print("Error: El año debe ser un número."); return
        
    try:
        response = requests.get(f"{BASE_URL}/movies", params={'year': year_val})
        if response.ok:
            movies = response.json()
            if not movies:
                print(f"\nNo se encontraron películas para el año {year_val}."); return
            print(f"\n--- PELÍCULAS DEL AÑO {year_val} ({len(movies)} encontradas) ---")
            for movie in movies:
                print(f"- {movie['title']}")
        else:
            print(f"Error en la búsqueda ({response.status_code}).")
    except requests.exceptions.RequestException as e:
        print(f"\nError de conexión: {e}")

def agregar_pelicula():
    """Pide los datos de una nueva película y la envía al endpoint POST /movies."""
    auth = gestionar_autenticacion()
    if not auth: return # Si la autenticación falla o se cancela, no continúa.
    
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
        if response.status_code == 201:
            print("Película agregada con éxito.")
        else:
            print(f"Error ({response.status_code}): {response.json()['detail']}")
            if response.status_code == 401: global SESION_AUTH; SESION_AUTH = None
    except requests.exceptions.RequestException as e:
        print(f"\nError de conexión: {e}")

def actualizar_pelicula_parcial():
    """Pide nuevos datos y los envía al endpoint PUT /movies/{title}/partial."""
    auth = gestionar_autenticacion()
    if not auth: return
    
    title_a_actualizar = input("Título de la película a actualizar: ")
    print("\n--- Ingrese los campos a modificar (deje en blanco para no cambiar) ---")
    
    update_data = {}
    # El operador "walrus" (:=) permite asignar y comprobar en una misma línea.
    if (t := input("Nuevo Título: ")): update_data["title"] = t.strip()
    if (y := input("Nuevo Año: ")):
        try:
            update_data["year"] = int(y)
        except ValueError:
            print("Año inválido, se omitirá.")
    if (c := input("Nuevos Actores (separados por coma): ")): update_data["cast"] = [a.strip() for a in c.split(",")]
    if (g := input("Nuevos Géneros (separados por coma): ")): update_data["genres"] = [gn.strip() for gn in g.split(",")]
    
    if not update_data:
        print("No se ingresaron datos para actualizar."); return
        
    try:
        response = requests.put(f"{BASE_URL}/movies/{title_a_actualizar}/partial", json=update_data, auth=auth)
        if response.ok:
            print("Película actualizada con éxito.")
        else:
            print(f"Error ({response.status_code}): {response.json()['detail']}")
            if response.status_code == 401: global SESION_AUTH; SESION_AUTH = None
    except requests.exceptions.RequestException as e:
        print(f"\nError de conexión: {e}")

def borrar_pelicula():
    """Pide un título y lo envía al endpoint DELETE /movies/{title}."""
    auth = gestionar_autenticacion()
    if not auth: return
    
    title = input("Título de la película a borrar: ")
    if input(f"¿Seguro que desea borrar '{title}'? (s/n): ").lower() != 's':
        print("Operación cancelada."); return
        
    try:
        response = requests.delete(f"{BASE_URL}/movies/{title}", auth=auth)
        if response.ok:
            print(response.json()["message"])
        else:
            print(f"Error ({response.status_code}): {response.json()['detail']}")
            # Si las credenciales fallan, las borramos para que las pida de nuevo.
            if response.status_code == 401: global SESION_AUTH; SESION_AUTH = None
    except requests.exceptions.RequestException as e:
        print(f"\nError de conexión: {e}")



# MENÚ PRINCIPAL Y BUCLE DE EJECUCIÓN 


def menu():
    """
    Muestra el menú de opciones al usuario y gestiona la selección,
    ejecutando la función correspondiente en un bucle infinito.
    """
    # Un diccionario para mapear la entrada del usuario a funciones.
    actions = {
        "1": ver_cantidad_peliculas, 
        "2": buscar_por_titulo,
        "3": buscar_por_anio,
        "4": agregar_pelicula,
        "5": actualizar_pelicula_parcial,
        "6": borrar_pelicula
    }
    
    while True:
        print("\n--- CLIENTE API DE PELÍCULAS ---")
        print("1. Ver cantidad total de películas") 
        print("2. Buscar por título")
        print("3. Buscar por año")
        print("4. Agregar nueva película (auth)")
        print("5. Actualizar película (auth)")
        print("6. Borrar película (auth)")
        print("0. Salir")
        
        op = input("Opción: ")
        
        if op == "0":
            break # Sale del bucle while y termina el programa.
            
        # Busca la función correspondiente a la opción elegida en el diccionario.
        action = actions.get(op)
        if action:
            action() # Si la opción es válida, ejecuta la función.
        else:
            print("Opción no válida.")



# PUNTO DE ENTRADA DEL SCRIPT 

if __name__ == "__main__":
    """
    Este bloque solo se ejecuta cuando el script es llamado directamente.
    Primero configura la conexión y luego inicia el menú.
    """
    configurar_servidor()
    menu()