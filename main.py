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
import json

load_dotenv()
MONGO_DB_PASS=os.getenv("MONGO_DB_PASS")
MONGO_DB_USER_NAME=os.getenv("MONGO_DB_USER_NAME")
client = MongoClient("mongodb+srv://"+MONGO_DB_USER_NAME+":"+MONGO_DB_PASS+"@cluster0.byajfqq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db=client.bliss_bucket


collection_user = db["users"]
collection_book = db["books"]
collection_cart = db["cart"]


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
    user_id: str
    title: str
    img: str
    ratings: int
    reviews: int
    category_id: str
    lat: int
    long: int
    price: int

class Cart(BaseModel):
    user_id: str
    object_id: str


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
            "user_id": book.user_id,
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

@app.delete("/deleteBook")
async def delete_book():
    try:
        collection_book.delete_one({"title": 'Hdjdj'})
        return {"message": f"Book with title 'Hdjdj' deleted successfully"}
       
    except Exception as e:
        # Handle any errors that occur during the deletion process
        raise HTTPException(status_code=500, detail=f"Error deleting book: {str(e)}")
    


@app.post("/addCart")
async def add_cart(cart: Cart):
    try:
        collection_cart.insert_one({"user_id": cart.user_id, "object_id": cart.object_id})
        return {"message": f"Item {cart.object_id} added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inserting element: {str(e)}")
    

@app.get("/getCart/{user_id}")
async def get_cart(user_id: str):
    try:
        cart_items = collection_cart.find({"user_id": user_id})
        cart_list = []
        temp = []
        for item in cart_items:
            cart_book = collection_book.find_one({"_id": ObjectId(item["object_id"])})
            cart_book["_id"] = str(cart_book["_id"])
                # Convert the MongoDB document to JSON
            cart_book_json = json.dumps(cart_book)
            cart_list.append(cart_book_json)
        return {"cart": cart_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving cart items: {str(e)}")
    
@app.delete("/deleteCart")
async def delete_cart(user_id: str, object_id: str):
    try:
        result = collection_cart.delete_one({"user_id": user_id, "object_id": object_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail=f"No item found for user {user_id} with object ID {object_id}")
        return {"message": f"Successfully deleted the item from the cart for user {user_id} with object ID {object_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting cart item: {str(e)}")
    

@app.get("/checkCartItemInCart")
async def check_cart_item_in_cart(user_id: str, object_id: str):
    try:
        cart_item = collection_cart.find_one({"user_id": user_id, "object_id": object_id})
        if cart_item:
            return {"inCart": True}
        else:
            return {"inCart": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking item in cart: {str(e)}")

@app.delete("/emptyCart")
async def emptyCart(user_id: str):
    try:
        delete_result = collection_cart.delete_many({"user_id": user_id})
        if delete_result.deleted_count > 0:
            return {"message": f"{delete_result.deleted_count} items deleted successfully for user_id: {user_id}"}
        else:
            return {"message": f"No items found for user_id: {user_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting items: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

