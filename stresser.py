import asyncio
import httpx

# --- PARÁMETROS DE LA PRUEBA ---
URL_A_PROBAR = "http://127.0.0.1:8000/movies"
TOTAL_PETICIONES = 100  # Número total de peticiones a enviar en una ráfaga

async def main():
    """
    Lanza una ráfaga de peticiones y cuenta éxitos vs. rechazos.
    """
    print(f"Lanzando {TOTAL_PETICIONES} peticiones a {URL_A_PROBAR}...")

    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Prepara una lista de tareas de petición.
        tasks = [client.get(URL_A_PROBAR) for _ in range(TOTAL_PETICIONES)]
        
        # 2. Lanza todas las tareas concurrentemente y espera los resultados.
        responses = await asyncio.gather(*tasks, return_exceptions=True)

    # 3. Cuenta los resultados de forma simple.
    exitos = 0
    rechazos = 0

    for resp in responses:
        # Si la respuesta es un objeto Response y su código es 200, es un éxito.
        if isinstance(resp, httpx.Response) and resp.status_code == 200:
            exitos += 1
        else:
            # Cualquier otra cosa (otro código de estado o una excepción) es un rechazo.
            rechazos += 1

    print("\n--- Resultados ---")
    print(f"Peticiones Aceptadas (200 OK): {exitos}")
    print(f"Peticiones Rechazadas (Otros): {rechazos}")

if __name__ == "__main__":
    asyncio.run(main())