from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import db_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db_client.connect()
    yield
    await db_client.close()

app = FastAPI(lifespan=lifespan)

@app.get('/api/v1/health')
def help():
    return {'message': 'ok'}