import hashlib
import sqlite3
import time
import uuid
from flask import session

class Modules:   

    def getUniqueCode(extra = ""):
        unique_code = str(uuid.uuid4()) + str(int(time.time())) + extra
        return hashlib.md5(unique_code.encode("utf-8")).hexdigest()
    
    def md5Hash(text):
        return hashlib.md5(text.encode("utf-8")).hexdigest()
    
    def hashPass(text):
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    
    def selectFromDB(query, enteredVars):
        connection = sqlite3.connect("data/data.db")
        cursor = connection.cursor()
        cursor.execute(query, enteredVars)
        result = cursor.fetchall()
        connection.close()
        return result
    
    def executeIntoDB(query, enteredVars):
        connection = sqlite3.connect("data/data.db")
        cursor = connection.cursor()
        cursor.execute(query, enteredVars)
        connection.commit()
        lastId = cursor.lastrowid
        connection.close()
        return lastId