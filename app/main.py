from contextlib import asynccontextmanager
from fastapi import FastAPI, status, HTTPException
from app.database import db_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db_client.connect()
    yield
    await db_client.close()

app = FastAPI(
    title='EventHub API',
    version='0.1.0',
    lifespan=lifespan)

@app.get('/api/v1/health', tags=['System'])
async def health_check():
    try:
        await db_client._ping()
        return {
            'status': 'ok',
            'components': {
                'database': "connected",
            }
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail=f'Database is down: {e}')