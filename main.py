import os
from accounts import Accounts
from storage import Storage

os.environ["FLASK_APP"] = str(__name__)

from flask import Flask, render_template, request, redirect, url_for, session
from apscheduler.schedulers.background import BackgroundScheduler
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
from werkzeug.middleware.proxy_fix import ProxyFix
import sqlite3


reset = not os.path.exists("data/data.db")

connection = sqlite3.connect("data/data.db")
cursor = connection.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT, name TEXT, filehash TEXT, uploadUserId INTEGER, share BOOLEAN, folder BOOLEAN, filesize INTEGER, linkshare BOOLEAN)")
cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, password TEXT, email TEXT, uniqueCode TEXT, uploadLimit INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS usershare (id INTEGER PRIMARY KEY AUTOINCREMENT, sender INTEGER, reciver INTEGER, fileId INTEGER, folder BOOLEAN)")
connection.close()

# -- WEBSITE --
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
app.secret_key = b'f50d650a2dc3032fa7b12f36348857519a72695a3902049f5c4f68095d732120'

if (reset):
    session.clear()

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
