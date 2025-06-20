# Módulos de FastAPI y relacionados
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.responses import JSONResponse

# Módulos de Pydantic para validación de datos
from pydantic import BaseModel, Field

# Módulos de Python estándar y de terceros
import secrets  # Para comparación segura de contraseñas
import json     # Para manejar archivos JSON
import os       # Para interactuar con el sistema operativo (ej. verificar si un archivo existe)
import requests # Para hacer peticiones HTTP (descargar el JSON inicial)
from contextlib import asynccontextmanager # Para el gestor de "lifespan" de FastAPI
from collections import deque              # Para una cola eficiente en el limitador de tasa
from datetime import datetime, timedelta   # Para manejar tiempos en el limitador de tasa
from typing import List, Optional, Dict, Deque # Para "type hints" (ayudas de tipado)



#  CONFIGURACIÓN Y VARIABLES GLOBALES 

# Aca definimos las constantes y variables que se van a usar en la aplicación.

# Configuración de archivos y URLs 
DATA_FILE = "movies.json"  # Nombre del archivo local que funcionará como base de datos.
REMOTE_URL = "https://raw.githubusercontent.com/prust/wikipedia-movie-data/master/movies.json" # URL para descargar los datos si no existen.

# Configuración del Limitador de Solicitudes (Rate Limiter) 
VENTANA_TIEMPO = timedelta(seconds=1)  # La ventana de tiempo para contar las peticiones (1 segundo).
MAX_PETICIONES = 10                    # Número máximo de peticiones permitidas dentro de la ventana de tiempo.

#"Bases de datos" en memoria 
USUARIOS_DB: Dict[str, str] = {"admin": "supersecret"} # Diccionario que simula una DB de usuarios para autenticación.
historial_peticiones: Dict[str, Deque[datetime]] = {}  # Diccionario para almacenar los timestamps de las peticiones de cada IP.
movies_db: List[Dict] = []                             # Lista que contendrá todas las películas una vez cargadas en memoria.



# GESTOR DE LIFESPAN Y APLICACIÓN FASTAPI 

# El "lifespan" es un gestor de eventos que ejecuta código al iniciar y al apagar el servidor.

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Función que se ejecuta al arrancar el servidor.
    Se encarga de llamar a `initialize_data` para cargar las películas en memoria.
    """
    initialize_data()
    yield  # El servidor se ejecuta mientras el código está en este punto.
    

# instancia principal de la aplicación FastAPI 
# se crea la aplicación y se le asigna un título, descripción y el gestor de lifespan.
app = FastAPI(
    title="API de Películas",
    description=f"Una API para gestionar una colección de películas. Límite: {MAX_PETICIONES} solicitudes por segundo por IP.",
    lifespan=lifespan
)



# MIDDLEWARE (Limitador de Solicitudes) 

# función que procesa CADA petición antes de que llegue al endpoint, y también procesa cada respuesta antes de ser enviada al cliente.

@app.middleware("http")
async def limitador_de_tasa(request: Request, call_next):
    """
    Este middleware revisa la IP de cada petición y comprueba si ha superado el límite.
    """
    ip = request.client.host
    ahora = datetime.utcnow()
    historial_ip = historial_peticiones.setdefault(ip, deque())

    # Elimina los timestamps de peticiones que ya son más antiguos que la ventana de tiempo.
    while historial_ip and (ahora - historial_ip[0]) > VENTANA_TIEMPO:
        historial_ip.popleft()

    # si el número de peticiones restantes es mayor o igual al máximo, deniega la petición.
    if len(historial_ip) >= MAX_PETICIONES:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": f"Límite de solicitudes alcanzado ({MAX_PETICIONES} por segundo)."},
        )

    # Si no se supera el límite, registra el timestamp de la petición actual.
    historial_ip.append(ahora)
    
    # Deja que la petición continúe su curso normal hacia el endpoint.
    response = await call_next(request)
    return response



# FUNCIONES AUXILIARES (Manejo de Datos) 


def initialize_data():
    """
    Carga los datos en la variable `movies_db`.
    Si el archivo `movies.json` no existe, lo descarga de la web.
    """
    global movies_db
    if not os.path.exists(DATA_FILE):
        print("Archivo de datos no encontrado. Descargando desde la web...") 
        try:
            response = requests.get(REMOTE_URL)
            response.raise_for_status() # Lanza un error si la descarga falló.
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(response.json(), f, indent=2, ensure_ascii=False)
        except requests.RequestException as e:
            raise Exception(f"CRÍTICO: No se pudo descargar el archivo de películas: {e}")
    
    # Carga el contenido del archivo JSON en la lista en memoria.
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        movies_db = json.load(f)
    print(f"✅ Datos cargados. {len(movies_db)} películas en memoria.")
    
def save_data():
    """
    Guarda el estado actual de la lista `movies_db` en el archivo `movies.json`.
    Se llama cada vez que hay una modificación (añadir, borrar, actualizar).
    """
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(movies_db, f, indent=2, ensure_ascii=False)



# MODELOS DE DATOS Y SEGURIDAD

# Se definen los modelos de Pydantic para la validación de los datos que entran
# y salen de la API, y la lógica de autenticación.

# Modelo para crear una película (todos los campos son obligatorios) 
class Movie(BaseModel):
    title: str = Field(..., min_length=1, description="Título de la película")
    year: int = Field(..., ge=0, description="Año de estreno")
    cast: List[str]
    genres: List[str]
    href: Optional[str] = None
    extract: Optional[str] = None
    thumbnail: Optional[str] = None
    thumbnail_width: Optional[int] = None
    thumbnail_height: Optional[int] = None

# Modelo para actualizar una película (todos los campos son opcionales) 
class MovieUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    year: Optional[int] = Field(None, ge=0)
    cast: Optional[List[str]] = None
    genres: Optional[List[str]] = None

# Configuración de Autenticación 
security = HTTPBasic() # Define que usaremos el esquema de autenticación HTTP Basic.

def verificar_credenciales(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """
    Función de dependencia que se encarga de validar el usuario y contraseña.
    Es usada en los endpoints protegidos.
    """
    # Busca el usuario en nuestra "base de datos"
    password_correcta = USUARIOS_DB.get(credentials.username)
    # Compara la contraseña de forma segura para evitar "timing attacks"
    if not password_correcta or not secrets.compare_digest(credentials.password, password_correcta):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Basic"}, # Para indicar al cliente que debe autenticarse
        )
    return credentials.username # Si es correcto, devuelve el nombre del usuario.



# ENDPOINTS DE LA API

### Endpoint para probar la autenticación (Protegido) ###
@app.get("/auth/test", tags=["Autenticación"])
def test_authentication(usuario: str = Depends(verificar_credenciales)):
    """Verifica si las credenciales proporcionadas son válidas."""
    return {"status": "ok", "message": "Autenticación exitosa", "usuario": usuario}

### Endpoint para obtener la cantidad total de películas (Público) ###
@app.get("/movies/count", tags=["Público"])
def get_movies_count():
    """Devuelve la cantidad total de películas en la base de datos."""
    return {"total_movies": len(movies_db)}

### Endpoint para obtener todas las películas o filtrar por año (Público) ###
@app.get("/movies", response_model=List[Movie], tags=["Público"])
def get_all_movies(year: Optional[int] = None):
    """Devuelve una lista de todas las películas. Opcionalmente, filtra por año de estreno."""
    if year is None:
        return movies_db
    return [movie for movie in movies_db if movie.get("year") == year]

### Endpoint para obtener una película por su título (Público) ###
@app.get("/movies/{title}", response_model=Movie, tags=["Público"])
def get_movie_by_title(title: str):
    """Busca y devuelve una única película por su título (no distingue mayúsculas/minúsculas)."""
    for movie in movies_db:
        if movie["title"].lower() == title.lower():
            return movie
    raise HTTPException(status_code=404, detail="Película no encontrada")

### Endpoint para añadir una nueva película (Protegido) ###
@app.post("/movies", response_model=Movie, status_code=status.HTTP_201_CREATED, tags=["Protegido"])
def add_movie(new_movie: Movie, usuario: str = Depends(verificar_credenciales)):
    """Añade una nueva película a la base de datos. Requiere autenticación."""
    if any(movie["title"].lower() == new_movie.title.lower() for movie in movies_db):
        raise HTTPException(status_code=400, detail="La película ya existe")
    movies_db.append(new_movie.dict())
    save_data()
    return new_movie

### Endpoint para borrar una película (Protegido) ###
@app.delete("/movies/{title}", status_code=status.HTTP_200_OK, tags=["Protegido"])
def delete_movie(title: str, usuario: str = Depends(verificar_credenciales)):
    """Elimina una película de la base de datos por su título. Requiere autenticación."""
    global movies_db
    original_count = len(movies_db)
    movies_db = [movie for movie in movies_db if movie["title"].lower() != title.lower()]
    if len(movies_db) == original_count:
        raise HTTPException(status_code=404, detail="Película no encontrada")
    save_data()
    return {"message": f"Película '{title}' eliminada exitosamente"}

### Endpoint para actualizar parcialmente una película (Protegido) ###
@app.put("/movies/{title}/partial", response_model=Movie, tags=["Protegido"])
def update_movie_partial(title: str, movie_update: MovieUpdate, usuario: str = Depends(verificar_credenciales)):
    """Actualiza uno o más campos de una película existente. Requiere autenticación."""
    movie_to_update = None
    movie_index = -1
    original_title = None

    for i, movie in enumerate(movies_db):
        if movie["title"].lower() == title.lower():
            movie_to_update = movie
            movie_index = i
            original_title = movie["title"]
            break
            
    if not movie_to_update:
        raise HTTPException(status_code=404, detail="Película no encontrada")

    update_data = movie_update.dict(exclude_unset=True) # Solo incluye los campos que el cliente envió.
    if not update_data:
        raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")
    
    # Si se cambia el título, verificar que no choque con otra película existente.
    if 'title' in update_data and any(m['title'].lower() == update_data['title'].lower() for m in movies_db if m['title'].lower() != original_title.lower()):
        raise HTTPException(status_code=400, detail="Ya existe otra película con ese nuevo título.")
        
    updated_movie_model = Movie(**{**movie_to_update, **update_data}) # Fusiona datos viejos y nuevos y valida.
    movies_db[movie_index] = updated_movie_model.dict()
    save_data()
    return movies_db[movie_index]