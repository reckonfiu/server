import os, utils, re
from flask import Flask, json, request
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient(
    "db", 
    27017)

db = client.fiudb


def autoResponse(function):
    try:
        result = function()
    except (BaseException, RuntimeError) as e:
        response = json.jsonify(
            status=400,
            message=e.message,
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

@app.route("/api/searchBy", methods=["POST"])
def searchBy():
    params = request.get_json(force=True).get('query')
    if params is None:
        return allRecords()
    match = {}
    if params.has_key("course"):
        match["course.number"] = params.get("course") 
    if params.has_key("term"):
        match["term.term"] = params.get("term")
    if params.has_key("prof"):
        match["instructor.name"] = { "$in" :  map(lambda x : re.compile(pattern=x, flags=re.IGNORECASE), params.get("prof").split() )  }
    
    pipeline_query[0]["$match"] = { "$and": [match] }
    
    print("Performing query: ", pipeline_query)    
    cursor = db.courses.aggregate(pipeline_query)
    return autoResponse(lambda: utils.toArray(cursor))

pipeline_query = [
  { "$match": {} },
  { "$limit": 75000 },
  { "$sort": { 'date': 1, 'instructor.name': 1 } }
]

# Things we need to implement
# search by
# store comments
# authenticate user
# add user
# delete user

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
    
