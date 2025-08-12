
import hashlib
import math
import sqlite3
from theme import Theme
from alert import Alert
from modules import Modules
from flask import Flask, render_template, request, redirect, url_for, session

class Accounts:
    def __init__(self, app):
        self.app = app
        self.theme = Theme(self.app)
        self.alert = Alert(self.app)


    def attemptLogin(self, user, psw):
        result = Modules.selectFromDB(f"SELECT id FROM users WHERE name = ? AND password = ?", (user, psw))
        print(result)
        if (len(result) == 0):
            return {"success": False, "id": -1}
        return {"success": True, "id": result[0][0]}
        

    def attemptSignup(self, user, email, psw):
        userCode = Modules.getUniqueCode()
        usersId = Modules.executeIntoDB(f"INSERT INTO users (`name`, `password`, `email`, `uniqueCode`, `uploadLimit`) VALUES (?, ?, ?, ?, ?)", (user, psw, email, userCode, '2048'))
        if (usersId == None):
            return {"success": False, "id": -1}
        return {"success": True, "id": usersId}
    

    def usernameIsTaken(self, name):
        names = Modules.selectFromDB("SELECT id FROM users WHERE name = ?", (name,))
        if (len(names) == 0):
            return False 
        return True
    

    def emailIsTaken(self, email):
        emails = Modules.selectFromDB(f"SELECT id FROM users WHERE email = ?", (email,))
        if (len(emails) == 0):
            return False 
        return True


    def getUserId(self):
        return session.get('userId')


    def getUserUniqueCode(self):
        try:
            return Modules.selectFromDB(f"SELECT uniqueCode FROM users WHERE id = ?", (self.getUserId(),))[0][0]
        except:
            return None


    def getUserMaxStorage(self):
        try:
            return Modules.selectFromDB(f"SELECT uploadLimit FROM users WHERE id = ?", (self.getUserId(),))[0][0]
        except:
            return None
        

    def bitToMB(self, bit):
        return bit/1048576
    
    def MBToBit(self, mb):
        return mb * 1048576
    

    def getUserCurrentStorage(self):
        totalSize = 0
        allUserFiles = Modules.selectFromDB("SELECT filesize FROM files WHERE uploadUserId = ?", (self.getUserId(),))
        for uFile in allUserFiles:
            totalSize += uFile[0]
        return math.ceil(totalSize)
    
    def getUserStorageLeft(self): 
        return self.MBToBit(self.getUserMaxStorage()) - self.getUserCurrentStorage() 


    def userIsLoggedIn(self):
        return self.getUserId() != None
    
    def updateMail(self, newMail, oldmail, hashpsw):
        Modules.executeIntoDB(f"UPDATE users SET email = ? WHERE id= ? AND email = ? AND password = ?", (newMail, self.getUserId(), oldmail, hashpsw))

    def updatePassword(self, newPsw, oldmail, hashpsw):
        Modules.executeIntoDB("UPDATE users SET password = ? WHERE id= ? AND email = ? AND password = ?", (newPsw, self.getUserId(), oldmail, hashpsw))


    def logoutPage(self):
        if(self.userIsLoggedIn()):
            session.pop("userId")
        return redirect(url_for("startPage"))

    def loginPage(self):
        data = {}
        if (request.form):
            if (len(request.form['username']) != 0 and len(request.form['password']) != 0):
                psw = Modules.hashPass(request.form['password'])
                name = request.form['username']
                status = self.attemptLogin(name, psw)

                if(status['success'] == False):
                    data['toggle'] = True
                    self.alert.addAlert("Password or/and username is wrong", "error", 10000)
                    return self.theme.loadPage("account/login.twig", data=data)
                
                else: 
                    session['userId'] = status['id']
                    return redirect(url_for("storageHomePage"))

        data['toggle'] = False
        return self.theme.loadFileWithTheme("account/login.twig", data=data)


    def signupPage(self):
        data = {}
        if (request.form):
            if (len(request.form['username']) != 0 and len(request.form['email']) != 0 and len(request.form['password']) != 0):
                name = request.form['username']
                email = request.form['email']
                if(self.usernameIsTaken(name)):
                    data['toggle'] = True
                    self.alert.addAlert("Username is already taken", "error", 7000)
                    return self.theme.loadPage("account/signup.twig", data=data)
                
                if(self.emailIsTaken(email)):
                    data['toggle'] = True
                    self.alert.addAlert("Email is already assigned to an account", "error", 7000)
                    return self.theme.loadPage("account/signup.twig", data=data)
                
                psw = Modules.hashPass(request.form['password'])
                status = self.attemptSignup(name, email, psw)

                if(status['success'] == False):
                    data['toggle'] = True
                    self.alert.addAlert("Something went wrong, please try again", "error", 7000)
                    return self.theme.loadPage("account/signup.twig", data=data)
                else: 
                    session['userId'] = status['id']
                    return redirect(url_for("storageHomePage"))

        data['toggle'] = False
        return self.theme.loadFileWithTheme("account/signup.twig", data=data)