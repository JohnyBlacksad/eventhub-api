from pydantic import BaseModel

class MongoDBClient(BaseModel):
    url: str
    db_name: str