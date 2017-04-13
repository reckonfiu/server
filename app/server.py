import os, utils, re, hashlib, time, jwt
from flask import Flask, json, request, session
from pymongo import MongoClient
from flask_cors import CORS
from bson.objectid import ObjectId
from datetime import datetime


app = Flask(__name__)
CORS(app)


client = MongoClient(
    "db",
    27017)

# databases
db = client.fiudb
db_users = client.userdb

# Globals
PASS_MIN_LEN = 8
PASS_MAX_LEN = 32

ISSUER = "reconFIU_server"
EXP_TIME = 86400 # 1 day
# Secret key for JWT
SECRET_KEY = "RECON_FIU_CEN_4010"  # TODO: Should be Randomized and sent to Client Browser

# creates general response 
def response(status_code, message, data=None):
    return json.jsonify(
        status = status_code,
        message = message,
        data = data
    )

# creates response with data
def autoResponse(function):
    try:
        result = function()
    except (BaseException, RuntimeError) as e:
        response = json.jsonify(
            status=400,
            message=str(e),
            data=dict(),
            records=0
        )
        client.close()
        return response
    return json.jsonify(
        status=200,
        message="Success",
        data=result,
        records=len(result)
    )


@app.before_request
def require_token():
    if request.method == "POST" :
        body = request.get_json(force=True)
        token = body.get("token")
        user = body.get("user")
        username = user["username"]
        print(user)        
        if body is None:
            return response(400, "Error: Bad Request")
        if user is None or (not username in session and request.endpoint != "login"):
            return response(400, "Not logged in")
        if token is None or not (is_valid_token(token) and session[username] == token ):
            return response(400, "invalid token")

@app.route("/")
def initApp():
    return "Welcome to ReconFIU"

@app.route("/api/getall")
@app.route("/api/getall/<int:limit>", methods=["POST", "GET"])
def allRecords(limit=1000):
    cursor = db.courses.find().limit(limit)
    return autoResponse(lambda: utils.toArray(cursor) )

# performs a search by depending on what criteri is passed
# if no criteria is passed the returns first 1000 records
@app.route("/api/searchby", methods=["POST"])
def searchBy():
    params = request.get_json(force=True).get("query")
    if params is None:
        return allRecords()
    course =  params.get("course")
    term = params.get("term")
    prof =  params.get("prof")
    match = {}
    if "course" in params and course:
        match["course.number"] = { "$regex" : re.compile(pattern=course, flags=re.IGNORECASE) }
    if "term" in params and term:
        match["term.term"] = term
    if "prof" in params and prof:
        match["instructor.name"] = { "$in" : list(map(lambda x : re.compile(pattern=x, flags=re.IGNORECASE), prof.split() ))  }
    
    pipeline_query[0]["$match"] = { "$and": [match] }
    cursor = db.courses.aggregate(pipeline_query)
    return autoResponse(lambda: utils.toArray(cursor))

pipeline_query = [
  { "$match": {} },
  { "$limit": 10000 },
  { "$sort": { "date": 1, "instructor.name": 1 } }
] 


# Find a user in userdb, return token of this user
@app.route("/api/finduser", methods=["POST"])
def find_user():
    params = request.get_json(force=True).get("user")
    username =  params.get("username")
    user = db_users.users.find_one({"username": username})
    if user is None:
        return response(404, "Error: " + username + " not found")
    return response(200, "User found", {"username": user["username"]})


# Create a user document in userdb
@app.route("/api/adduser", methods=["POST"])
def add_user():
    params = request.get_json(force=True).get("user")
    username = params.get("username")
    password = params.get("password")
    user = db_users.users.find_one({"username": username})
    if user:
        return response(409, "Error: " + username + " already exists")

    # Determine if legal password
    valid_pass, msg = is_valid_password(password)

    if valid_pass and is_valid_username(username):
        hash_password = hash_pass(password)
        new_user = {"username": username, "password": hash_password}
        # Add to userdb
        db_users.users.insert(new_user)
        return response(201, "User: " + username + " has been created")
    return response(400, "Error: Invalid Password: " + msg)

# Delete a user document in userdb
@app.route("/api/deleteuser", methods=["POST"])
def delete_user():
    params = request.get_json(force=True).get("user")
    username = params.get("username")
    user = db_users.users.remove({"username": username})
    if user:
        return response(200, "Username: " + username + " has been deleted.")
    return response(409, username + " not found")

# Check if password is valid
def is_valid_password(password):
    if len(password) < 8:
        return False, "Too short, password needs to be at least " + str(PASS_MIN_LEN) + " characters long"
    if len(password) > 32:
        return False, "Too long, password needs to be at most " + str(PASS_MAX_LEN) + " characters long"
    if not password.isalnum():  # Check if alphanumeric
        return False, "Invalid char, password can only consist of alphanumeric characters"
    return True, "Password OK"

# check if username is valid
def is_valid_username(username):
    user = username.split("@")
    return user[1] == "fiu.edu" and user[0] and len(user) == 2

# Login user, authorization
@app.route("/api/login", methods=["POST"])
def login():
    params = request.get_json(force=True).get("user")
    username = params.get("username")
    password = params.get("password")
    
    user = db_users.users.find_one({"username": username})
    if user is None:
        return response(404,  username + " not found")
    if username in session:  # User already logged in
        return response(409,  username + " is already logged in")   
    # Determine if password is correct
    if hash_pass(password) != user["password"]:
        return response(403, "Error: Given password does not match with " + username)
    
    token = generate_token(username)
    # Store user in session
    session[username] = token
    return response(200, username + " has logged in", {"username": username, "token": token})
        


# Logout user
@app.route("/api/logout", methods=["POST"])
def logout():
    # Receive username, token
    params = request.get_json(force=True).get("user")
    username = params.get("username")   
    # Remove user from session
    session.pop(username, None)
    return response(200, username + " has been logged out")
           

# Adds a comment to the database
# Needs username, comment body, and course id
@app.route("/api/addcomment", methods=["POST"])
def add_comment():
    params = request.get_json(force=True).get("comment")
    username = params.get("username") or "Anonymous"
    body = params.get("body")
    if body.strip() is None:
        return response(400, "Error: Bad Request")
    
    db.courses.update({"_id": ObjectId(params.get("id"))},\
        {"$push": {"comments": {"username": username,\
        "body": params.get("body"), "time": datetime.now().strftime("%m-%d-%Y %H:%M:%S")}}})
    return response(200, "Comment has been added")

# Hash a given password using the sha1 hash function
def hash_pass(password):
    hash_obj = hashlib.sha1(password.encode("utf-8")).digest()
    hash_password = hashlib.sha1(hash_obj).hexdigest()
    return hash_password


# Generates a JSON Web Token for a given username
def generate_token(username):
    payload = {
        "iss": ISSUER,  # Issuer
        "sub": username,  # Subject
        "iat": time.time(),  # Issued at
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


# Determines if a token is valid for a given username
def is_valid_token(token, username):
    try:
        token_vals = jwt.decode(token, SECRET_KEY, algorithm="HS256")
    except (jwt.DecodeError, jwt.InvalidTokenError) as e:
        return False
    if token_vals["iss"] != ISSUER or token_vals["sub"] != username:
        return False
    else:
        return True

if __name__ == "__main__":
    # Secret key for sessions
    app.secret_key = os.urandom(24)
    app.run(host="0.0.0.0", debug=True)
