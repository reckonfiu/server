import os, utils, re, hashlib, time
from flask import Flask, json, request, session
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient(
    'db',
    27017)

db = client.fiudb

# Globals
db_users = client.userdb
PASS_MIN_LEN = 8
PASS_MAX_LEN = 32

ISSUER = "reconFIU_server"
EXP_TIME = 86400 # 1 day
# Secret key for JWT
SECRET_KEY = "RECON_FIU_CEN_4010"  # TODO: Should be Randomized and sent to Client Browser


def response(status_code, message, data=None):
    return json.jsonify(
        status = status_code,
        message = message,
        data = data
    )

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
        # setattr(response, "status_code", 400)
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
def allRecords(limit=100):
    cursor = db.courses.find().limit(limit)
    return autoResponse(lambda: utils.toArray(cursor) )

# performs a search by depending on what criterias are passed
# if not criteria is passed the returns getAll
@app.route("/api/searchBy", methods=["POST"])
def searchBy():
    params = request.get_json(force=True).get('query')
    if params is None:
        return allRecords()
    match = {}
    if "course" in params:
        match["course.number"] = params.get("course") 
    if "term" in params:
        match["term.term"] = params.get("term")
    if "prof" in params:
        match["instructor.name"] = { "$in" :  map(lambda x : re.compile(pattern=x, flags=re.IGNORECASE), params.get("prof").split() )  }
    
    pipeline_query[0]["$match"] = { "$and": [match] }
    cursor = db.courses.aggregate(pipeline_query)
    return autoResponse(lambda: utils.toArray(cursor))

pipeline_query = [
  { "$match": {} },
  { "$limit": 75000 },
  { "$sort": { 'date': 1, 'instructor.name': 1 } }
]


if __name__ == "__main__":
    # Secret key for sessions
    app.secret_key = os.urandom(24)
    app.run(host="0.0.0.0", debug=True)