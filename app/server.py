import os, utils, re, hashlib, time, jwt
from flask import Flask, json, request, session
from pymongo import MongoClient
from flask_cors import CORS
from bson.objectid import ObjectId
from datetime import datetime


app = Flask(__name__)
CORS(app)


client = MongoClient(
    'db',
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

@app.route("/")
def initApp():
    return "Welcome to ReconFIU"

@app.route("/api/getall")
@app.route("/api/getall/<int:limit>")
def allRecords(limit=1000):
    cursor = db.courses.find().limit(limit)
    return autoResponse(lambda: utils.toArray(cursor) )

# performs a search by depending on what criteri is passed
# if no criteria is passed the returns first 1000 records
@app.route("/api/searchby", methods=["POST"])
def searchBy():
    params = request.get_json(force=True).get('query')
    if params is None:
        return allRecords()
    match = {}
    if "course" in params and params.get("course"):
        match["course.number"] = { "$regex" : re.compile(pattern=params.get("course"), flags=re.IGNORECASE) }
    if "term" in params and params.get("term"):
        match["term.term"] = params.get("term")
    if "prof" in params and params.get("prof"):
        match["instructor.name"] = { "$in" : list(map(lambda x : re.compile(pattern=x, flags=re.IGNORECASE), params.get("prof").split() ))  }
    
    pipeline_query[0]["$match"] = { "$and": [match] }
    cursor = db.courses.aggregate(pipeline_query)
    return autoResponse(lambda: utils.toArray(cursor))

pipeline_query = [
  { "$match": {} },
  { "$limit": 10000 },
  { "$sort": { "date": 1, "instructor.name": 1 } }
] 


# Show all documents in userdb
@app.route("/api/getallusers")
@app.route("/api/getallusers/<int:limit>")
def allUsers(limit = 100):
    cursor = db_users.users.find().limit(limit)
    return autoResponse(lambda: utils.toArray(cursor))


# Find a user in userdb, return token of this user
@app.route('/api/finduser', methods=["POST"])
def find_user():
    params = request.get_json(force=True).get('user')
    if params is None:
        return response(400, "Error: Bad Request")

    user = db_users.users.find_one({'username': params.get("username")})
    if user is None:
        return response(404, "Error: " + params.get("username") + " not found")
    else:
        return response(200, "User found", {'username': user['username']})


# Create a user document in userdb
@app.route('/api/adduser', methods=["POST"])
def add_user():
    params = request.get_json(force=True).get('user')
    username = params.get("username")
    password = params.get("password")
    if params is None:
        return response(400, "Error: Bad Request")
    elif username is None:
        return response(404, "Error: Missing username")
    elif password is None:
        return response(404, "Error: Missing password")

    user = db_users.users.find_one({'username': username})
    if user:
        return response(409, "Error: " + username + " already exists")
    else:  # User not found
        # Determine if legal password
        valid_pass, msg = is_valid_password(password)

        if valid_pass and is_valid_username(username):
            hash_password = hash_pass(password)
            new_user = {'username': username, 'password': hash_password}
            # Add to userdb
            db_users.users.insert(new_user)
            return response(201, "User: " + username + " has been created")
        else:
            return response(400, "Error: Invalid Password: " + msg)

# Delete a user document in userdb
@app.route('/api/deleteuser', methods=["POST"])
def delete_user():
    params = request.get_json(force=True).get('user')
    if params is None:
        return response(400, "Error: Bad Request")
    elif params.get("username") is None:
        return response(404, "Error: Missing username")
    user = db_users.users.remove({'username': params.get("username")})
    if user:
        return response(200, "Username: " + params.get("username") + " has been deleted.")
    return response(409, "Error: " + params.get("username") + " has already been deleted")

# Check if password is valid
def is_valid_password(password):
    if len(password) < 8:
        return False, "Too short, password needs to be at least " + str(PASS_MIN_LEN) + " characters long"
    elif len(password) > 32:
        return False, "Too long, password needs to be at most " + str(PASS_MAX_LEN) + " characters long"
    elif not password.isalnum():  # Check if alphanumeric
        return False, "Invalid char, password can only consist of alphanumeric characters"
    else:
        return True, "Password OK"

# check if username is valid
def is_valid_username(username):
    user = username.split("@")
    return user[1] == "fiu.edu" and user[0] and len(user) == 2

# Login user, authorization
@app.route('/api/login', methods=["POST"])
def login():
    params = request.get_json(force=True).get('user')
    if params is None:
        return response(400, "Error: Bad Request")
    elif params.get("username") is None:
        return response(404, "Error: Missing username")
    elif params.get("password") is None:
        return response(404, "Error: Missing password")

    username = params.get("username")
    user = db_users.users.find_one({'username': username})
    if user:
        if username in session:  # User already logged in
            return response(409, "Error: " + username + " is already logged in")
        else:
            # Determine if password is correct
            if hash_pass(params.get("password")) == user['password']:
                token = generate_token(username)
                # Store user in session
                session[username] = username
                return response(200, username + " has logged in", {'username': username, 'token': token})
            else:
                return response(403, "Error: Given password does not match with " + username)
    else:  # User not found
        return response(404, "Error: " + username + " not found")


# Logout user
@app.route('/api/logout', methods=["POST"])
def logout():
    # Receive username, token
    params = request.get_json(force=True).get('user')
    if params is None:
        return response(400, "Error: Bad Request")
    elif params.get("username") is None:
        return response(404, "Error: Missing username")
    elif params.get("token") is None:
        return response(404, "Error: Missing token")

    username = params.get("username")
    user = db_users.users.find_one({'username': username})
    if user:
        if not username in session:   # User already logged out
            return response(400, "Error: " + username + " is not logged in")
        else:
            if is_valid_token(params.get("token"), username):
                # Remove user from session
                session.pop(username, None)
                return response(200, username + " has been logged out")
            else:
                return response(409, "Error: Invalid token received")
    else:  # User not found
        return response(404, "Error: " + username + " not found")

# Adds a comment to the database
# Needs username, comment body, and course id
@app.route('/api/addcomment', methods=["POST"])
def add_comment():
    params = request.get_json(force=True).get('comment')
    if params is None:
        return response(400, "Error: Bad Request")
    # If the comment is empty
    elif params.get("body").strip("") is None:
        return response(400, "Error: Cannot add empty comments")
    elif params.get("username") is None:
        username = "Anonymous"
    else:
        username = params.get("username")
    db.courses.update({"_id": ObjectId(params.get("id"))},\
        {"$push": {"comments": {"username": username,\
        "body": params.get("body"), "time": datetime.now().strftime('%m-%d-%Y %H:%M:%S')}}})
    return response(200, "Comment has been added")

# Hash a given password using the sha1 hash function
def hash_pass(password):
    hash_obj = hashlib.sha1(password.encode('utf-8')).digest()
    hash_password = hashlib.sha1(hash_obj).hexdigest()
    return hash_password


# Generates a JSON Web Token for a given username
def generate_token(username):
    payload = {
        'iss': ISSUER,  # Issuer
        'sub': username,  # Subject
        'iat': time.time(),  # Issued at
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token


# Determines if a token is valid for a given username
def is_valid_token(token, username):
    try:
        token_vals = jwt.decode(token, SECRET_KEY, algorithm='HS256')
    except (jwt.DecodeError, jwt.InvalidTokenError) as e:
        return False
    if token_vals['iss'] != ISSUER or token_vals['sub'] != username:
        return False
    else:
        return True

if __name__ == "__main__":
    # Secret key for sessions
    app.secret_key = os.urandom(24)
    app.run(host="0.0.0.0", debug=True)
