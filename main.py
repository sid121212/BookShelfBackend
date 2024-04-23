from fastapi import FastAPI
from bson import ObjectId
from fastapi import FastAPI, File, UploadFile, HTTPException
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
collection_profile = db["profile_image"]
collection_orders = db["orders"]


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

class ProfileImage(BaseModel):
    user_id: str
    img_url: str


class Orders(BaseModel):
    user_id: str
    date_created: str
    time_created: str
    status: bool




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

@app.get("/userBooks/{user_id}")
async def userBooks(user_id: str):
    try:
        books = list(collection_book.find({"user_id": user_id}))
        for book in books:
            book['_id'] = str(book['_id'])

        return {"books": books}

    except Exception as e:
        return HTTPException(status_code=500, detail=f"Error getting books: {str(e)}")

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
    
@app.get("/getCartSummary/{user_id}")
async def get_cart_summary(user_id: str):
    try:
        cart_items = collection_cart.find({"user_id": user_id})
        total_items = 0
        total_price = 0.0
        for item in cart_items:
            cart_book = collection_book.find_one({"_id": ObjectId(item["object_id"])})
            cart_book["_id"] = str(cart_book["_id"])
            cart_book_json = json.dumps(cart_book)
            # print(cart_book_json)
            total_items+=1
            total_price+=cart_book["price"]
        return {"total_items": total_items,"total_price": total_price}
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


@app.post("/profileImage")
async def profileImage(profileImg: ProfileImage):
    try:
        img = collection_profile.insert_one({"user_id": profileImg.user_id,"img_url": profileImg.img_url})
        return {"message": "Image was successfully uploaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inserting profile image: {str(e)}")


@app.get("/profileImage/{user_id}")
async def get_profile_image(user_id: str):
    try:
        profile_img = collection_profile.find_one({"user_id": user_id})
        if profile_img:
            return {"img_url": profile_img.get("img_url")}
        else:
            raise HTTPException(status_code=404, detail="Profile image not found for the user")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching profile image: {str(e)}")

@app.post("/create_order")
async def create_order(orders: Orders):
    try:
        collection_orders.insert_one({"user_id": orders.user_id,"date_created": orders.date_created,"time_created": orders.time_created,"status": orders.status})
        return {"message": "Order object was created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")
    
@app.get("/getOrders/{user_id}")
async def get_orders(user_id: str):
    try:
        orders = list(collection_orders.find({"user_id": user_id}))
        for child in orders:
            child['_id']=str(child['_id'])
        return {'orders': orders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting orders: {str(e)}")

@app.delete("/userBooks/{book_id}")
async def userBooks(book_id: str):
    try:
        deleted_book = collection_book.delete_one({"_id": ObjectId(book_id)})
        return {"Book has been successfully deleted": str(deleted_book)}
    except Exception as e:
        return HTTPException(status_code=500, detail=f"Error deleting book: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

