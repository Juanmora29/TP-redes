from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import secrets
import json
import os
import requests
from contextlib import asynccontextmanager
from collections import deque
from datetime import datetime, timedelta
from typing import Deque
from starlette.responses import JSONResponse

# --- CONFIGURACIÓN GLOBAL ---
DATA_FILE = "movies.json"
REMOTE_URL = "https://raw.githubusercontent.com/prust/wikipedia-movie-data/master/movies.json"
VENTANA_TIEMPO = timedelta(seconds=1)
MAX_PETICIONES = 10
historial_peticiones: Dict[str, Deque[datetime]] = {}
movies_db: List[Dict] = []

# --- GESTOR DE LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_data()
    yield

app = FastAPI(
    title="API de Películas",
    description=f"Una API para gestionar una colección de películas. Límite: {MAX_PETICIONES} solicitudes por segundo por IP.",
    lifespan=lifespan
)

# --- MIDDLEWARE DE LIMITACIÓN DE TASA ---
@app.middleware("http")
async def limitador_de_tasa(request: Request, call_next):
    ip = request.client.host
    ahora = datetime.utcnow()
    historial_ip = historial_peticiones.setdefault(ip, deque())

    while historial_ip and (ahora - historial_ip[0]) > VENTANA_TIEMPO:
        historial_ip.popleft()

    if len(historial_ip) >= MAX_PETICIONES:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Límite de solicitudes alcanzado ({MAX_PETICIONES} por segundo).",
        )

    historial_ip.append(ahora)
    response = await call_next(request)
    return response

# --- FUNCIONES AUXILIARES ---
def initialize_data():
    global movies_db
    if not os.path.exists(DATA_FILE):
        # El mensaje de descarga sí es útil, lo mantenemos.
        print("Descargando JSON desde la web...") 
        try:
            response = requests.get(REMOTE_URL)
            response.raise_for_status()
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(response.json(), f, indent=2, ensure_ascii=False)
        except requests.RequestException as e:
            raise Exception(f"No se pudo descargar el archivo de películas: {e}")
    
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        movies_db = json.load(f)
    
    # ▼▼▼ ¡CAMBIO AQUÍ! ▼▼▼
    # Simplemente hemos eliminado la siguiente línea:
    # print(f"✅ Datos cargados. {len(movies_db)} películas en memoria.")
    # ▲▲▲ ¡FIN DEL CAMBIO! ▲▲▲


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(movies_db, f, indent=2, ensure_ascii=False)

# --- MODELOS Y SEGURIDAD ---
class Movie(BaseModel):
    title: str = Field(..., min_length=1); year: int = Field(..., ge=0); cast: List[str]; genres: List[str]; href: Optional[str] = None; extract: Optional[str] = None; thumbnail: Optional[str] = None; thumbnail_width: Optional[int] = None; thumbnail_height: Optional[int] = None
class MovieUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1); year: Optional[int] = Field(None, ge=0); cast: Optional[List[str]] = None; genres: Optional[List[str]] = None
security = HTTPBasic()
USUARIOS_DB: Dict[str, str] = {"admin": "supersecret"}
def verificar_credenciales(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    if credentials.username not in USUARIOS_DB: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas", headers={"WWW-Authenticate": "Basic"})
    password_correcta = USUARIOS_DB.get(credentials.username)
    if not password_correcta or not secrets.compare_digest(credentials.password, password_correcta): raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas", headers={"WWW-Authenticate": "Basic"})
    return credentials.username

# --- ENDPOINTS ---
@app.get("/movies/count", tags=["Público"])
def get_movies_count():
    """Devuelve la cantidad total de películas en la base de datos."""
    return {"total_movies": len(movies_db)}

@app.get("/auth/test", tags=["Autenticación"])
def test_authentication(usuario: str = Depends(verificar_credenciales)):
    return {"status": "ok", "message": "Autenticación exitosa", "usuario": usuario}

@app.get("/movies", response_model=List[Movie], tags=["Público"])
def get_all_movies(year: Optional[int] = None):
    if year is None: return movies_db
    return [movie for movie in movies_db if movie.get("year") == year]

@app.get("/movies/{title}", response_model=Movie, tags=["Público"])
def get_movie_by_title(title: str):
    for movie in movies_db:
        if movie["title"].lower() == title.lower(): return movie
    raise HTTPException(status_code=404, detail="Película no encontrada")

@app.post("/movies", response_model=Movie, status_code=status.HTTP_201_CREATED, tags=["Protegido"])
def add_movie(new_movie: Movie, usuario: str = Depends(verificar_credenciales)):
    if any(movie["title"].lower() == new_movie.title.lower() for movie in movies_db): raise HTTPException(status_code=400, detail="La película ya existe")
    movies_db.append(new_movie.dict()); save_data()
    return new_movie

@app.delete("/movies/{title}", status_code=status.HTTP_200_OK, tags=["Protegido"])
def delete_movie(title: str, usuario: str = Depends(verificar_credenciales)):
    global movies_db
    original_count = len(movies_db)
    movies_db = [movie for movie in movies_db if movie["title"].lower() != title.lower()]
    if len(movies_db) == original_count: raise HTTPException(status_code=404, detail="Película no encontrada")
    save_data()
    return {"message": f"Película '{title}' eliminada exitosamente"}

@app.put("/movies/{title}/partial", response_model=Movie, tags=["Protegido"])
def update_movie_partial(title: str, movie_update: MovieUpdate, usuario: str = Depends(verificar_credenciales)):
    movie_to_update = None; movie_index = -1; original_title = None
    for i, movie in enumerate(movies_db):
        if movie["title"].lower() == title.lower():
            movie_to_update = movie; movie_index = i; original_title = movie["title"]; break
    if not movie_to_update: raise HTTPException(status_code=404, detail="Película no encontrada")
    update_data = movie_update.dict(exclude_unset=True)
    if not update_data: raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")
    if 'title' in update_data and any(m['title'].lower() == update_data['title'].lower() for m in movies_db if m['title'].lower() != original_title.lower()): raise HTTPException(status_code=400, detail="Ya existe otra película con ese nuevo título.")
    updated_movie_model = Movie(**{**movie_to_update, **update_data})
    movies_db[movie_index] = updated_movie_model.dict(); save_data()
    return movies_db[movie_index]