import requests
import sys

# --- CONFIGURACIÓN ---
# ▼▼▼ Ya no es obligatorio editar esta línea ▼▼▼
# El script ahora te preguntará la IP si no la encuentra aquí.
IP_DEL_SERVIDOR = "PON_AQUI_LA_IP_DE_TU_SERVIDOR"
# ▲▲▲ Ya no es obligatorio editar esta línea ▲▲▲

# <<< CAMBIO: Estas variables se definirán dinámicamente al inicio >>>
BASE_URL = None
SESION_AUTH = None # Guarda credenciales validadas

# <<< NUEVA FUNCIÓN para solicitar y configurar la IP del servidor >>>
def configurar_servidor():
    """
    Verifica si la IP del servidor está configurada. Si no, la solicita al usuario
    y establece la variable global BASE_URL.
    """
    global IP_DEL_SERVIDOR, BASE_URL

    # Si la IP sigue siendo el valor por defecto, se la pedimos al usuario.
    if IP_DEL_SERVIDOR == "PON_AQUI_LA_IP_DE_TU_SERVIDOR":
        print("--- Configuración del Cliente ---")
        nueva_ip = input("Por favor, ingresa la dirección IP del servidor: ").strip()
        
        # Si el usuario no ingresa nada, no podemos continuar.
        if not nueva_ip:
            print("\nError: No se ha proporcionado una dirección IP. El programa terminará.")
            sys.exit(1)
        
        IP_DEL_SERVIDOR = nueva_ip

    # Una vez que tenemos la IP (ya sea la pre-configurada o la recién ingresada),
    # construimos la URL base para que el resto del programa la use.
    BASE_URL = f"http://{IP_DEL_SERVIDOR}:8000"
    print(f"\n✅ Servidor configurado para conectarse a: {BASE_URL}")
    # Pequeña prueba de conexión para ver si el servidor está activo
    try:
        requests.get(BASE_URL, timeout=3)
        print("✅ ¡Conexión con el servidor exitosa!")
    except requests.exceptions.RequestException:
        print("⚠️  AVISO: No se pudo establecer conexión inicial con el servidor.")
        print("   Asegúrate de que la IP es correcta y el servidor está en ejecución.")


def gestionar_autenticacion():
    global SESION_AUTH
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
        response = requests.get(f"{BASE_URL}/auth/test", auth=credenciales_nuevas, timeout=5)
        
        if response.status_code == 200:
            print("¡Autenticación exitosa!")
            SESION_AUTH = credenciales_nuevas
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

def agregar_pelicula():
    auth_credenciales = gestionar_autenticacion()
    if not auth_credenciales:
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
    
    try:
        response = requests.post(f"{BASE_URL}/movies", json=data, auth=auth_credenciales)
        if response.status_code == 201:
            print("Película agregada con éxito.")
        else:
            print(f"Error ({response.status_code}): {response.json()['detail']}")
            if response.status_code == 401:
                global SESION_AUTH
                SESION_AUTH = None
    except requests.exceptions.RequestException as e:
        print(f"\nError de conexión con el servidor: {e}")

def actualizar_pelicula_parcial():
    auth_credenciales = gestionar_autenticacion()
    if not auth_credenciales:
        return

    title_a_actualizar = input("Ingrese el título de la película a actualizar: ")
    print("\n--- Ingrese los campos a modificar (deje en blanco para no cambiar) ---")
    update_data = {}
    nuevo_titulo = input("Nuevo Título: ")
    if nuevo_titulo:
        update_data["title"] = nuevo_titulo.strip()
    nuevo_anio = input("Nuevo Año: ")
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
    auth_credenciales = gestionar_autenticacion()
    if not auth_credenciales:
        return
        
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

def menu():
    # <<< CAMBIO: El bloque de error se ha eliminado de aquí >>>
    # La comprobación ahora se hace en la función configurar_servidor()
        
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
    # <<< CAMBIO: Primero configuramos el servidor y luego iniciamos el menú >>>
    configurar_servidor()
    menu()