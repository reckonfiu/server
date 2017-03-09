import os
from flask import Flask, jsonify
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient(
    'db', 
    27017)

db = client.fiudb

@app.route('/')
def hello():
    return "Hello World"

@app.route('/getall')
def allRecords():
    cursor = db.courses.find().limit(100)
    results = []
    for document in cursor:
        results.append({'course': document['course'], 'data': document['data'], 'instructor': document['instructor'] })
    return jsonify({ 'count': cursor.count() , 'results': results})

# Things we need to implement
# search by
# store comments
# authenticate user
# add user
# delete user

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
    
