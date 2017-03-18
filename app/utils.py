from bson import json_util

def toArray(cursor):
    json_docs = [json_util.dumps(doc) for doc in cursor]
    return json_docs