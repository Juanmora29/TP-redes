from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import secrets
import json
import os
import requests
from contextlib import asynccontextmanager

# --- GESTOR DE LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_data()
    yield

app = FastAPI(
    title="API de Películas",
    description="Una API para gestionar una colección de películas.",
    lifespan=lifespan
)

DATA_FILE = "movies.json"
REMOTE_URL = "https://raw.githubusercontent.com/prust/wikipedia-movie-data/master/movies.json"

# --- 1. MODELOS DE DATOS ---
class Movie(BaseModel):
    title: str = Field(..., min_length=1, description="El título no puede estar vacío.")
    year: int = Field(..., ge=0, description="El año no puede ser negativo.")
    cast: List[str]
    genres: List[str]
    href: Optional[str] = None
    extract: Optional[str] = None
    thumbnail: Optional[str] = None
    thumbnail_width: Optional[int] = None
    thumbnail_height: Optional[int] = None

class MovieUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, description="El título no puede estar vacío.")
    year: Optional[int] = Field(None, ge=0, description="El año no puede ser negativo.")
    cast: Optional[List[str]] = None
    genres: Optional[List[str]] = None

# --- 2. CONFIGURACIÓN DE SEGURIDAD ---
security = HTTPBasic()
# ¡Asegúrate de que este usuario y contraseña coincidan con los que usas en el cliente!
USUARIOS_DB: Dict[str, str] = {"admin": "supersecret"} 

def verificar_credenciales(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    # Asegurarse de que el usuario existe antes de comparar la contraseña
    if credentials.username not in USUARIOS_DB:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    password_correcta = USUARIOS_DB.get(credentials.username)
    # Usar compare_digest para evitar ataques de temporización
    if not password_correcta or not secrets.compare_digest(credentials.password, password_correcta):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# --- 3. FUNCIONES AUXILIARES ---
def initialize_data():
    if not os.path.exists(DATA_FILE):
        print("Descargando JSON desde la web...")
        try:
            response = requests.get(REMOTE_URL)
            response.raise_for_status()
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(response.json(), f, indent=2, ensure_ascii=False)
        except requests.RequestException as e:
            raise Exception(f"No se pudo descargar el archivo de películas: {e}")

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(movies):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(movies, f, indent=2, ensure_ascii=False)

# --- 4. ENDPOINTS ---

# --- ¡ESTE ES EL ENDPOINT QUE FALTABA! ---
@app.get("/auth/test", tags=["Autenticación"])
def test_authentication(usuario: str = Depends(verificar_credenciales)):
    """
    Endpoint para que el cliente verifique las credenciales.
    Si las credenciales son válidas, la dependencia 'verificar_credenciales'
    se resolverá con éxito y se devolverá un 200 OK.
    
    Si son inválidas, la dependencia lanzará una excepción HTTP 401.
    """
    return {"status": "ok", "message": "Autenticación exitosa", "usuario": usuario}
# ----------------------------------------

@app.get("/movies", response_model=List[Movie], tags=["Público"])
def get_all_movies():
    return load_data()

@app.get("/movies/{title}", response_model=Movie, tags=["Público"])
def get_movie_by_title(title: str):
    movies = load_data()
    for movie in movies:
        if movie["title"].lower() == title.lower():
            return movie
    raise HTTPException(status_code=404, detail="Película no encontrada")

@app.post("/movies", response_model=Movie, status_code=status.HTTP_201_CREATED, tags=["Protegido"])
def add_movie(new_movie: Movie, usuario: str = Depends(verificar_credenciales)):
    # ... (código sin cambios)
    movies = load_data()
    if any(movie["title"].lower() == new_movie.title.lower() for movie in movies):
        raise HTTPException(status_code=400, detail="La película ya existe")
    movies.append(new_movie.dict())
    save_data(movies)
    print(f"Usuario '{usuario}' ha agregado la película '{new_movie.title}'.")
    return new_movie

@app.delete("/movies/{title}", status_code=status.HTTP_200_OK, tags=["Protegido"])
def delete_movie(title: str, usuario: str = Depends(verificar_credenciales)):
    # ... (código sin cambios)
    movies = load_data()
    movies_to_keep = [movie for movie in movies if movie["title"].lower() != title.lower()]
    if len(movies) == len(movies_to_keep):
        raise HTTPException(status_code=404, detail="Película no encontrada")
    save_data(movies_to_keep)
    print(f"Usuario '{usuario}' ha eliminado la película '{title}'.")
    return {"message": f"Película '{title}' eliminada exitosamente"}

@app.put("/movies/{title}/partial", response_model=Movie, tags=["Protegido"])
def update_movie_partial(
    title: str, 
    movie_update: MovieUpdate, 
    usuario: str = Depends(verificar_credenciales)
):
    # ... (código sin cambios)
    movies = load_data()
    movie_to_update = None
    movie_index = -1
    original_title = None
    for i, movie in enumerate(movies):
        if movie["title"].lower() == title.lower():
            movie_to_update = movie
            movie_index = i
            original_title = movie["title"]
            break
    if not movie_to_update:
        raise HTTPException(status_code=404, detail="Película no encontrada")
    update_data = movie_update.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")
    if 'title' in update_data and any(m['title'].lower() == update_data['title'].lower() for m in movies if m['title'].lower() != original_title.lower()):
        raise HTTPException(status_code=400, detail="Ya existe otra película con ese nuevo título.")
    updated_movie_model = Movie(**{**movie_to_update, **update_data})
    movies[movie_index] = updated_movie_model.dict()
    save_data(movies)
    print(f"Usuario '{usuario}' ha actualizado la película '{original_title}'.")
    return movies[movie_index]