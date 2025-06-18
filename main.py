from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict
import secrets
import json
import os
import requests

app = FastAPI(title="API de Películas", description="Una API para gestionar una colección de películas.")

DATA_FILE = "movies.json"
REMOTE_URL = "https://raw.githubusercontent.com/prust/wikipedia-movie-data/master/movies.json"

# --- 1. MODELOS DE DATOS CORREGIDOS ---

# Modelo estricto para crear y mostrar películas. Los campos básicos son obligatorios.
class Movie(BaseModel):
    title: str
    year: int
    cast: List[str]
    genres: List[str]
    href: Optional[str] = None
    extract: Optional[str] = None
    thumbnail: Optional[str] = None
    thumbnail_width: Optional[int] = None
    thumbnail_height: Optional[int] = None

# Modelo flexible para actualizaciones parciales (todos los campos son opcionales).
class MovieUpdate(BaseModel):
    title: Optional[str] = None
    year: Optional[int] = None
    cast: Optional[List[str]] = None
    genres: Optional[List[str]] = None

# --- 2. CONFIGURACIÓN DE SEGURIDAD ---

security = HTTPBasic()

# Base de usuarios simulada
USUARIOS_DB: Dict[str, str] = {
    "admin": "supersecret"
}

def verificar_credenciales(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """Valida las credenciales del usuario y devuelve el nombre de usuario si son correctas."""
    password_correcta = USUARIOS_DB.get(credentials.username)
    if not password_correcta or not secrets.compare_digest(credentials.password, password_correcta):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# --- 3. FUNCIONES AUXILIARES (sin cambios) ---

def initialize_data():
    if not os.path.exists(DATA_FILE):
        print("Descargando JSON desde la web...")
        response = requests.get(REMOTE_URL)
        if response.status_code == 200:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(response.json(), f, indent=2, ensure_ascii=False)
        else:
            raise Exception("No se pudo descargar el archivo de películas.")

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(movies):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(movies, f, indent=2, ensure_ascii=False)

# --- 4. ENDPOINTS ---

@app.on_event("startup")
def startup_event():
    initialize_data()

# --- ENDPOINTS PÚBLICOS (GET y PUT) ---

@app.get("/movies", response_model=List[Movie])
def get_all_movies():
    return load_data()

@app.get("/movies/{title}", response_model=Movie)
def get_movie_by_title(title: str):
    movies = load_data()
    for movie in movies:
        if movie["title"].lower() == title.lower():
            return movie
    raise HTTPException(status_code=404, detail="Película no encontrada")

# --- ENDPOINTS PROTEGIDOS (POST y DELETE) ---

@app.post("/movies", response_model=Movie, status_code=status.HTTP_201_CREATED)
def add_movie(new_movie: Movie, usuario: str = Depends(verificar_credenciales)):
    # <-- CORREGIDO: Se añade la dependencia de seguridad
    movies = load_data()
    if any(movie["title"].lower() == new_movie.title.lower() for movie in movies):
        raise HTTPException(status_code=400, detail="La película ya existe")
    
    movies.append(new_movie.dict())
    save_data(movies)
    print(f"Usuario '{usuario}' ha agregado la película '{new_movie.title}'.")
    return new_movie

@app.delete("/movies/{title}", status_code=status.HTTP_200_OK)
def delete_movie(title: str, usuario: str = Depends(verificar_credenciales)):
    # <-- CORREGIDO: Se añade la dependencia de seguridad
    movies = load_data()
    movies_to_keep = [movie for movie in movies if movie["title"].lower() != title.lower()]
    
    if len(movies) == len(movies_to_keep):
        raise HTTPException(status_code=404, detail="Película no encontrada")
    
    save_data(movies_to_keep)
    print(f"Usuario '{usuario}' ha eliminado la película '{title}'.")
    return {"message": f"Película '{title}' eliminada exitosamente"}

# ... (el resto de tu código, como la función verificar_credenciales, debe estar antes)

# --- ENDPOINT PUT - ACTUALIZACIÓN PARCIAL (AHORA PROTEGIDO) ---
@app.put("/movies/{title}/partial", response_model=Movie)
def update_movie_partial(
    title: str, 
    movie_update: MovieUpdate, 
    usuario: str = Depends(verificar_credenciales) # <-- SE AÑADE LA AUTENTICACIÓN AQUÍ
):
    movies = load_data()
    movie_to_update = None
    original_title = None # Guardamos el título original por si se modifica

    for movie in movies:
        if movie["title"].lower() == title.lower():
            movie_to_update = movie
            original_title = movie["title"] # Guardamos el título antes de cualquier cambio
            break
            
    if not movie_to_update:
        raise HTTPException(status_code=404, detail="Película no encontrada")
        
    update_data = movie_update.dict(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")
        
    for key, value in update_data.items():
        movie_to_update[key] = value
        
    save_data(movies)
    
    # Mensaje de log en el servidor
    print(f"Usuario '{usuario}' ha actualizado la película '{original_title}'.")
    
    return movie_to_update