import os
from accounts import Accounts
from storage import Storage
from modules import Modules
import random
import time

os.environ["FLASK_APP"] = str(__name__)

from flask import Flask, render_template, request, redirect, url_for, session
from apscheduler.schedulers.background import BackgroundScheduler
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
from werkzeug.middleware.proxy_fix import ProxyFix
import sqlite3

connection = sqlite3.connect("data/data.db")
cursor = connection.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT, name TEXT, filehash TEXT, uploadUserId INTEGER, share BOOLEAN, folder BOOLEAN, filesize INTEGER, linkshare BOOLEAN, sharePath TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, password TEXT, email TEXT, uniqueCode TEXT, uploadLimit INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS usershare (id INTEGER PRIMARY KEY AUTOINCREMENT, sender INTEGER, reciver INTEGER, fileId INTEGER, folder BOOLEAN)")
connection.close()

# -- WEBSITE --
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
if not os.path.exists("data"):
    os.makedirs("data")
if not os.path.exists("data/userfiles"):
    os.makedirs("data/userfiles")

if not os.path.exists("hash.env"):
    with open("hash.env", "w") as f:
        stamp1 = random.choice(time.monotonic_ns().split())
        stamp2 = random.choice(time.monotonic_ns().split())
        f.write(f"SECRET_KEY={Modules.getUniqueCode(str(stamp1))}{Modules.getUniqueCode(str(stamp2))}\n")

if os.path.exists("hash.env"):
    with open("hash.env", "r") as f:
        for line in f:
            if line.startswith("SECRET_KEY="):
                app.secret_key = line.split("=")[1].strip().encode("utf-8")

acc = Accounts(app)
app.add_url_rule('/logout', view_func=acc.logoutPage)
app.add_url_rule('/login', view_func=acc.loginPage, methods=['POST', 'GET'])
app.add_url_rule('/signup', view_func=acc.signupPage, methods=['POST', 'GET'])


storage = Storage(app,acc)
app.add_url_rule('/storage/home', view_func=storage.storageHomePage, methods=['GET', 'POST'])
app.add_url_rule('/storage/home/<path:path>', view_func=storage.storagePathPage, methods=['GET', 'POST'])
app.add_url_rule('/storage/upload', view_func=storage.storageUploadPage, methods=['GET', 'POST'])
#app.add_url_rule('/storage/upload/<path:path>', view_func=storage.storageUploadPathPage, methods=['GET', 'POST'])
app.add_url_rule('/storage/makefolder', view_func=storage.storageCreateFolderPathPage, methods=['GET', 'POST'])
app.add_url_rule('/storage/sharemenu', view_func=storage.storageOpenShareMenu, methods=['GET', 'POST'])
app.add_url_rule('/storage/shared', view_func=storage.storageSharedPage, methods=['GET', 'POST'])
app.add_url_rule('/storage/shared/<path:path>', view_func=storage.storageSharedPage, methods=['GET', 'POST'])
app.add_url_rule('/storage/download', view_func=storage.storageDownloadFile, methods=['GET', 'POST'])
app.add_url_rule('/storage/settings', view_func=storage.storageUserSettingsPage, methods=['GET', 'POST'])



@app.route('/')
def startPage():
    return render_template("start.twig", loggedIn=acc.userIsLoggedIn())
