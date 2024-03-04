from fastapi import FastAPI
from bson import ObjectId
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv
import os
from pydantic import BaseModel
import base64
import uvicorn

load_dotenv()
MONGO_DB_PASS=os.getenv("MONGO_DB_PASS")
MONGO_DB_USER_NAME=os.getenv("MONGO_DB_USER_NAME")
client = MongoClient("mongodb+srv://"+MONGO_DB_USER_NAME+":"+MONGO_DB_PASS+"@cluster0.byajfqq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db=client.bliss_bucket


collection_user = db["users"]
collection_book = db["books"]



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class User(BaseModel):
    username: str
    password: str

class Book(BaseModel):
    title: str
    img: str
    ratings: int
    reviews: int
    category_id: str
    lat: int
    long: int
    price: int


@app.get("/")
def health_check():
    return "ok"


def encode_password(password: str) -> str:
    return base64.b64encode(password.encode()).decode()

def decode_password(encoded_password: str) -> str:
    return base64.b64decode(encoded_password.encode()).decode()

@app.post("/signup")
async def signup(user: User):
    # print(user)
    existing_user = collection_user.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    encoded_password = encode_password(user.password)
    user_doc = {
        "username": user.username,
        "password": encoded_password
    }
    result =  collection_user.insert_one(user_doc)
    user_id = str(result.inserted_id)
    response_data = {"username": user.username, "user_id": user_id}
    return response_data




@app.post("/login")
async def login(user: User):
    # print(user)
    user_db =  collection_user.find_one({"username": user.username})
    if not user_db:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    stored_password = decode_password(user_db["password"])
    if user.password != stored_password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"user_id": str(user_db['_id']),"username": str(user_db['username'])}


@app.post("/addBook")
async def create_book(book: Book):
    try:
        book_db = {
            "title": book.title,
            "img": book.img,
            "ratings": book.ratings,
            "reviews": book.reviews,
            "category": book.category_id,
            "latitude": book.lat,
            "longitude": book.long,
            "price": book.price
        }
        collection_book.insert_one(book_db)
        return {"message": "Book added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding book: {str(e)}")


@app.get("/allBooks")
async def getAllBooks():
    try:
        books = list(collection_book.find())
    
        for book in books:
            book['_id'] = str(book['_id'])

        return {"books": books}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting all books: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

