from bson import json_util

def toArray(cursor, sortBy="date"):
    json_docs = [json_util.dumps(doc) for doc in cursor.sort(sortBy, 1)]
    return json_docs
