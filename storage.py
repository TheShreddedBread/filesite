
import hashlib
import os
import sqlite3
import time
from modules import Modules
import math
from flask import Flask, render_template, request, redirect, send_from_directory, url_for, session

class Storage:
    def __init__(self, app, acc):
        self.acc = acc
        self.app = app

    def convert_size(self, size_bytes):
        if size_bytes == 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        size = round(size_bytes / p, 2)
        return "%s %s" % (size, size_name[i])

    def getLastPath(self):
        if (session.get('lastStoragePath') != None):
            return session['lastStoragePath']
        return ""

    def getCurrentPath(self):
        if (session.get('currentStoragePath') != None):
            return session['currentStoragePath']
        return ""

    def getDefaultStoragePath(self):
        return "storage/home/"

    def getDefaultSharedStoragePath(self):
        return "storage/home/"

    def validatePath(self, givenpath):
        startPath = self.getDefaultStoragePath()
        if(givenpath.count(startPath) > 1):
            givenpath = givenpath[len(startPath):-1]
        if givenpath == "":
            return True
        folderpath = Modules.selectFromDB(f"SELECT id FROM files WHERE folder = '1' AND uploadUserId = '{self.acc.getUserId()}' AND filehash = '{givenpath}'")
        if (len(folderpath) != 0):
            if (len(folderpath[0]) != 0):
                return True
    
        sharedPath = self.getDefaultSharedStoragePath()
        if(givenpath.count(sharedPath) > 1):
            givenpath = givenpath[len(sharedPath):-1]
        if givenpath == "":
            return True

        fileId = Modules.selectFromDB(f"SELECT id, uploadUserId FROM files WHERE filehash = '{givenpath}'")
        if (len(fileId) != 0):
            if (len(fileId[0]) != 0):
                folderpath = Modules.selectFromDB(f"SELECT id FROM usershare WHERE reciver = '{self.acc.getUserId()}' AND sender = '{fileId[0][1]}' AND fileId = '{fileId[0][1]}'")
                if (len(folderpath) != 0):
                    if (len(folderpath[0]) != 0):
                        return True
        return False

    def getPathBack(self, givenpath):
        pathToHome = []
        currpath = givenpath
        while currpath != "":
            folderpath = Modules.selectFromDB(f"SELECT path, name FROM files WHERE folder = '1' AND uploadUserId = '{self.acc.getUserId()}' AND filehash = '{currpath}'")
            if (len(folderpath) != 1):
                break
            if (len(folderpath[0]) != 2):
                break
            pathToHome.insert(0,[currpath, folderpath[0][1]])
            currpath = folderpath[0][0]
            
        return (pathToHome)

    def getPathSharedBack(self, givenpath, targetPath = ""):
        pathToHome = []
        currpath = givenpath
        while currpath != targetPath:
            fail = True
            fileId = Modules.selectFromDB(f"SELECT id, uploadUserId, share FROM files WHERE filehash = '{currpath}' and folder = '1'")

            if (len(fileId) != 0):
                if (len(fileId[0]) != 0):
                    if (fileId[0][2] == 0): # If share = 0
                        currpath = targetPath
                        break
                    sharedpath = Modules.selectFromDB(f"SELECT id FROM usershare WHERE reciver = '{self.acc.getUserId()}' AND sender = '{fileId[0][1]}' AND fileId = '{fileId[0][0]}'")

                    if (len(sharedpath) != 0):
                        if (len(sharedpath[0]) != 0):
                            folderpath = Modules.selectFromDB(f"SELECT path, name FROM files WHERE folder = '1' AND uploadUserId = '{fileId[0][1]}' AND filehash = '{currpath}'")
                            
                            if (len(folderpath) == 1):
                                if (len(folderpath[0]) == 2):
                                    fail = False
                                    pathToHome.insert(0,[currpath, folderpath[0][1]])
                                    currpath = folderpath[0][0]
            if (fail):
                break        
        return (pathToHome)
        
    def bitToMB(self, bit):
        return bit/1048576
    
    def getDataDefault(self):
        data = {}
        data['navbarHTML'] = render_template("smalltemplate/navbar.twig", firstpage=(self.getLastPath()==""), path=self.getLastPath(), fileusedtext=self.getFileUsedText())
        data['popupHTML'] = ""
        data['files'] = ""
        return data

    def getFileUsedText(self):
        spaceText = self.convert_size(self.acc.getUserCurrentStorage()) + " / " + self.convert_size(self.acc.getUserMaxStorage()*1048576)
        progress = self.acc.getUserCurrentStorage()/(self.acc.getUserMaxStorage()*1048576)
        return render_template("smalltemplate/progressbar.twig", text=spaceText, progress=math.ceil(progress*100))

    def splitFilename(self, filename):
        name, ext = os.path.splitext(filename)
        if ext in ['.gz', '.bz2']:
            ext = os.path.splitext(name)[1] + ext
        return [name,ext]
    
    def getFilesForPath(self, path = ""):
        filesHTML = ""
        clickpath = self.getLastPath()
        # id INTEGER, path TEXT, name TEXT, filehash TEXT, uploadUserId INTEGER, share BOOLEAN, folder BOOLEAN, filesize INTEGER
        foundFiles = Modules.selectFromDB(f"SELECT * FROM files WHERE uploadUserId = {self.acc.getUserId()} AND path='{path}'")
        for file in foundFiles:
            fancyname = self.splitFilename(file[2])[0][0:12]
            if (len(file[2]) > len(fancyname)):
                fancyname += "..."

            if file[6] == 1:
                clickpath = file[3]

            filesHTML += render_template("smalltemplate/storageSquares.twig", data={"id":file[0], "folder": file[6], "name": file[2], "fancyname": fancyname, "size": self.convert_size(file[7]), "path": clickpath})
        if (len(filesHTML) == 0):
            filesHTML = "<br><br><div style='color: white; border: 2px solid white; width: fit-content; padding: 2rem;'><h1>Start by uploading file</h1></div>"
        return filesHTML

    def getSharedFilesForPath(self, path = "", shared = False):
        filesHTML = ""
        loadedSharedFiles = []
        clickpath = self.getLastPath()
        # id INTEGER, path TEXT, name TEXT, filehash TEXT, uploadUserId INTEGER, share BOOLEAN, folder BOOLEAN, filesize INTEGER, sharePath TEXT
        foundFiles = Modules.selectFromDB(f"SELECT * FROM usershare WHERE reciver = {self.acc.getUserId()}")
        for file in foundFiles:
            targetFile = Modules.selectFromDB(f"SELECT * FROM files WHERE id = '{file[3]}' AND uploadUserId = '{file[1]}' AND share = '1' AND sharePath = '{path}'")
            if (len(targetFile) != 1):
                continue
            targetFile = targetFile[0]
            fancyname = self.splitFilename(targetFile[2])[0][0:12]
            if (len(targetFile[2]) > len(fancyname)):
                fancyname += "..."

            if targetFile[6] == 1:
                clickpath = targetFile[3]
            loadedSharedFiles.append(file[3])
            filesHTML += render_template("smalltemplate/storageSquares.twig", data={"id":targetFile[0], "folder": targetFile[6], "name": targetFile[2], "fancyname": fancyname, "size": self.convert_size(targetFile[7]), "path": clickpath, "shared": shared})
        session['loadedSharedFiles'] = loadedSharedFiles
        if (len(filesHTML) == 0):
            filesHTML = "<br><br><div style='color: white; border: 2px solid white; width: fit-content; padding: 2rem;'><h1>You have no files shared with you</h1></div>"
        return filesHTML

    def generateNavHelp(self, path):
        paths = []
        if len(path) > 0:
            splitedlatest = path.split("/")
            for i in range(0, len(splitedlatest), 1):
                print(i)
                apath = "/storage/home"
                if len(splitedlatest) > 0:
                    apath += "/" + "/".join(splitedlatest[0:i+1])
                paths.append([splitedlatest[i], apath])
        return paths
    
    def storageHomePage(self):
        return self.storagePathPage("")

    def storagePathPage(self, path):
        if(not self.acc.userIsLoggedIn() or self.validatePath(path) == False):
            return redirect("/")
        
        data = self.getDataDefault()

        session['lastStoragePath'] = path
        
        pathWay = self.getPathBack(path)
        data['navHelp'] = render_template("smalltemplate/workpath.twig", paths=pathWay)

        if (len(pathWay) <= 1):
            ahrefpath = "storage/home"
        else:
            ahrefpath = "storage/home/" + pathWay[-2][0]
        
        if request.method == 'POST' and 'type' in request.form:   
            if request.form['type'] == "download":
                fileId = request.form['id']
                files = Modules.selectFromDB(f"SELECT path, filehash, name FROM files WHERE id = '{fileId}' AND uploadUserId = '{self.acc.getUserId()}'")
                fileToDownload = files[0]
                instantPath = self.app.instance_path
                folderPath = "\\".join(instantPath.split("\\")[0:-1])
                userFilesPath = (os.path.join(folderPath ,"data", "userfiles", self.acc.getUserUniqueCode(), fileToDownload[0]))
                fileExt = self.splitFilename(fileToDownload[2])[1]
                return send_from_directory(userFilesPath, (fileToDownload[1] + fileExt), as_attachment=True, download_name=(fileToDownload[2]))

            elif request.form['type'] == "askfordelete":
                fileId = request.form['id'] 
                userFiles = Modules.selectFromDB(f"SELECT id, name FROM files WHERE id = '{fileId}' AND uploadUserId = '{self.acc.getUserId()}'")
                if (len(userFiles) >= 1):
                    fileDelHash = Modules.md5Hash(str(userFiles[0][0] * self.acc.getUserId()))
                    session['deleteFileHash'] = fileDelHash
                    session['deleteFileId'] = userFiles[0][0]
                    currPath = "storage/home"
                    if (len(path) != 0):
                        currPath += ("/" + path) 
                    data['popupHTML'] = render_template("popup/confirmdelete.twig", backpath=currPath, fileDeleteHash=fileDelHash, filename=userFiles[0][1])
            elif request.form['type'] == "sharemenu":
                fileId = request.form['id']
                files = Modules.selectFromDB(f"SELECT share, name FROM files WHERE id = '{fileId}' AND uploadUserId = '{self.acc.getUserId()}'")
                if (len(files) == 1):
                    session['sharetargetId'] = fileId
                    shareFile = files[0]
                    currPath = "storage/home"
                    if (len(path) != 0):
                        currPath += ("/" + path) 

                    usersData = []
                    if (shareFile[0] == 1): 
                        users = Modules.selectFromDB(f"SELECT reciver FROM usershare WHERE sender = '{self.acc.getUserId()}' AND fileId = '{fileId}'")
                        for user in users:
                            userInfo = Modules.selectFromDB(f"SELECT id, name, email FROM users WHERE id = '{user[0]}'")
                            if (len(userInfo) == 1):
                                if (userInfo[0][0] != self.acc.getUserId() and users[0][0] == userInfo[0][0]):
                                    usersData.append([userInfo[0][0], userInfo[0][1], userInfo[0][2]])
                    data['popupHTML'] = render_template("popup/sharemenu.twig", backpath=currPath, checked=(shareFile[0]==1), filename=shareFile[1], users=usersData)
            
            elif request.form['type'] == "toggleshare":
                fileId = session['sharetargetId']
                val = request.form.getlist('sharestate')
                if (len(val) != 0):
                    if (val[0] == "allowed"):
                        if path == "":
                            Modules.executeIntoDB(f"UPDATE files SET share='1', sharePath='' WHERE id = '{fileId}' AND uploadUserId = '{self.acc.getUserId()}'")
                        else:
                            sharedFolders = Modules.selectFromDB(f"SELECT id FROM files WHERE filehash = '{path}' AND uploadUserId = '{self.acc.getUserId()}' AND folder = '1' AND share = '1'")
                            if (len(sharedFolders) == 1):
                                print(path)
                                Modules.executeIntoDB(f"UPDATE files SET share='1', sharePath='{path}' WHERE id = '{fileId}' AND uploadUserId = '{self.acc.getUserId()}'") # in shared folder
                            else:
                                Modules.executeIntoDB(f"UPDATE files SET share='1', sharePath='' WHERE id = '{fileId}' AND uploadUserId = '{self.acc.getUserId()}'") # not in shared folder
                else: 
                    Modules.executeIntoDB(f"UPDATE files SET share='0' WHERE id = '{fileId}' AND uploadUserId = '{self.acc.getUserId()}'")
            
            elif request.form['type'] == "updatesharedusers":
                fileId = session['sharetargetId']
                val = request.form.getlist('sharestate')
                if (len(val) != 0):
                    if (val[0] == "allowed"):
                        Modules.executeIntoDB(f"UPDATE files SET share='1' WHERE id = '{fileId}' AND uploadUserId = '{self.acc.getUserId()}'")
                else: 
                    Modules.executeIntoDB(f"UPDATE files SET share='0' WHERE id = '{fileId}' AND uploadUserId = '{self.acc.getUserId()}'")
            
            elif request.form['type'] == "updateusers":
                fileId = session['sharetargetId']
                newMailList = request.form.getlist('addedmail')
                targetFile = Modules.selectFromDB(f"SELECT id, folder FROM files WHERE id = '{fileId}' AND uploadUserId = '{self.acc.getUserId()}' AND share = '1'")
                if len(targetFile) == 1:
                    allToBeAdded = []
                    for mail in newMailList:
                        correctMail = mail.strip()
                        print(correctMail)
                        result = Modules.selectFromDB(f"SELECT id, email FROM users WHERE email = '{correctMail}'")
                        print(result)
                        if (len(result) == 1):
                            print("got")
                            if (result[0][0] != self.acc.getUserId()):
                                allToBeAdded.append(result[0][0])
                                if (len(Modules.selectFromDB(f"SELECT id FROM usershare WHERE sender = '{self.acc.getUserId()}' AND reciver = '{result[0][0]}' AND fileId = '{targetFile[0][0]}'")) == 0):
                                    Modules.executeIntoDB(f"INSERT INTO usershare (sender, reciver, fileId, folder) VALUES ('{self.acc.getUserId()}', '{result[0][0]}', '{targetFile[0][0]}', '{targetFile[0][1]}')")

                    currentShared = Modules.selectFromDB(f"SELECT reciver FROM usershare WHERE sender = '{self.acc.getUserId()}' AND fileId = '{targetFile[0][0]}'")
                    if len(currentShared) >= 1:
                        for user in currentShared:
                            if (user[0] not in allToBeAdded):
                                Modules.executeIntoDB(f"DELETE FROM usershare WHERE sender = '{self.acc.getUserId()}' AND reciver = '{user[0]}' AND fileId = '{targetFile[0][0]}'")
                

            elif (session.get('deleteFileHash') != None):
                if (session.get('deleteFileHash') == request.form['type']):
                    fileData = Modules.selectFromDB(f"SELECT id, name, filehash, path, folder FROM files WHERE uploadUserId = '{self.acc.getUserId()}' AND id = '{session.get('deleteFileId')}' LIMIT 1")
                    if len(fileData) == 1:
                        if (fileData[0][4] == 0):
                            Modules.executeIntoDB(f"DELETE FROM files WHERE uploadUserId = '{self.acc.getUserId()}' AND id = '{fileData[0][0]}' AND filehash = '{fileData[0][2]}'")
                            filePath = f"data/userfiles/{self.acc.getUserUniqueCode()}/{fileData[0][2]}{self.splitFilename(fileData[0][1])[1]}"
                            if (os.path.exists(filePath)):
                                os.remove(filePath)
                        else:
                            allUserFiles = Modules.selectFromDB(f"SELECT id, path, folder, name, filehash FROM files WHERE uploadUserId = '{self.acc.getUserId()}'")
                           
                            targetedPath = fileData[0][1] + "/"
                            if (len(fileData[0][3]) != 0):
                                targetedPath += fileData[0][3] + "/"

                            for uFile in allUserFiles:
                                if (uFile[1].startswith(targetedPath) or uFile[1] == targetedPath[0:-1] or uFile[4] == fileData[0][2]):
                                    Modules.executeIntoDB(f"DELETE FROM files WHERE uploadUserId = '{self.acc.getUserId()}' AND id = '{uFile[0]}'")
                                    filePath = f"data/userfiles/{self.acc.getUserUniqueCode()}/{uFile[4]}{self.splitFilename(uFile[3])[1]}"
                                    print(filePath)
                                    if (os.path.exists(filePath) and uFile[2] == 0):
                                        os.remove(filePath)

                            print("FOLDER!!")
                        session['deleteFileHash'] = None
                        session['deleteFileId'] = None
                    
        data['files'] = self.getFilesForPath(path)
        data['navbarHTML'] = render_template("smalltemplate/navbar.twig", firstpage=(self.getLastPath()==""), backpath=ahrefpath, fileusedtext=self.getFileUsedText())
        return render_template("storage/home.twig", data=data)
    

    def storageSharedPage(self, path=""):
        if(not self.acc.userIsLoggedIn() or self.validatePath(path) == False):
            return redirect("/")
        
        data = self.getDataDefault()

        session['lastStoragePath'] = path
        
        pathWay = self.getPathSharedBack(path)
        data['navHelp'] = render_template("smalltemplate/workpath.twig", paths=pathWay, share=True)
        if (len(pathWay) <= 1):
            ahrefpath = "storage/shared"
        else:
            ahrefpath = "storage/shared/" + pathWay[-2][0]

        if request.method == 'POST' and 'type' in request.form:   
            if request.form['type'] == "download":
                fileId = request.form['id']
                if (session.get('loadedSharedFiles') != None):
                    loadedSharedFiles = session['loadedSharedFiles']
                else:
                    loadedSharedFiles = []
                
                try:
                    int(fileId)
                except:
                    return

                if (int(fileId) in loadedSharedFiles):
                    files = Modules.selectFromDB(f"SELECT path, filehash, name, uploadUserId FROM files WHERE id = '{fileId}' AND share = 1")
                    if (len(files) == 1):
                        userDetails = Modules.selectFromDB(f"SELECT uniqueCode FROM users WHERE id = '{files[0][3]}'")
                        if (len(userDetails) == 1):
                            fileToDownload = files[0]
                            instantPath = self.app.instance_path
                            folderPath = "\\".join(instantPath.split("\\")[0:-1])
                            userFilesPath = (os.path.join(folderPath ,"data", "userfiles", userDetails[0][0], fileToDownload[0]))
                            fileExt = self.splitFilename(fileToDownload[2])[1]
                            return send_from_directory(userFilesPath, (fileToDownload[1] + fileExt), as_attachment=True, download_name=(fileToDownload[2]))
        data['files'] = self.getSharedFilesForPath(path, shared=True)
        data['navbarHTML'] = render_template("smalltemplate/navbar.twig", firstpage=(self.getLastPath()==""), backpath=ahrefpath, fileusedtext=self.getFileUsedText())
        return render_template("storage/home.twig", data=data)
    

    def storageUploadPage(self):
        return self.storageUploadPathPage("")
    
    def storageUploadPathPage(self, path):
        if(not self.acc.userIsLoggedIn()):
            return redirect("/")
        data = {}
        last = self.getLastPath()
        data['navHelp'] = render_template("smalltemplate/workpath.twig", paths=self.getPathBack(last))
        data['files'] = self.getFilesForPath(last)
        if (last == ""):
            data['popupHTML'] = render_template("popup/uploadfile.twig", exitpath = "/storage/home")
        else:
            data['popupHTML'] = render_template("popup/uploadfile.twig", exitpath = ("/storage/home/" + last))
        data['navbarHTML'] = render_template("smalltemplate/navbar.twig", firstpage=(last==""), path=last, fileusedtext=self.getFileUsedText())

        if request.method == 'POST':   
            storagepath = last
            f = request.files['file'] 
            
            userId = self.acc.getUserId()
            pathToUploadTo = f"data/userfiles/{self.acc.getUserUniqueCode()}/"
            filename = f.filename
            filedata = f.read()
            filesize = len(filedata) #Kan behövas fixas mer: https://stackoverflow.com/questions/15772975/flask-get-the-size-of-request-files-object
            if (self.acc.getUserStorageLeft() - filesize < 0):
                print("Not enough space")
                return redirect("/storage/home")
            if (len(Modules.selectFromDB(f"SELECT * FROM files WHERE uploadUserId = {self.acc.getUserId()}")) == 0 and not os.path.exists(pathToUploadTo)):
                os.mkdir(pathToUploadTo)
            filehash = Modules.getUniqueCode(filename)
            name,ext = self.splitFilename(filename)

            if (Modules.executeIntoDB(f"INSERT INTO files (path, name, filehash, uploadUserId, share, folder, filesize) VALUES ('{storagepath}', '{filename}', '{filehash}', {userId}, false, false, {filesize})") != None):
                with open(pathToUploadTo + filehash + ext, "wb") as binary_file:
                    binary_file.write(filedata)
                    uploadedPath = "/storage/home"
                    if (last != ""):
                        uploadedPath += ("/" + last)
                return redirect(uploadedPath)
            else:
                return redirect("/storage/upload")
        else:
            return render_template("storage/home.twig", data=data)
    

    def storageDownloadFile(self, fileId, uploderId =-1):
        if(not self.acc.userIsLoggedIn()):
            return redirect("/")
        
        if(uploderId == -1):
            uploderId = self.acc.getUserId()
        
        files = Modules.selectFromDB(f"SELECT (path, filehash) FROM files WHERE id = '{fileId}' AND uploadUserId = '{uploderId}'")
        fileToDownload = files[0]

        return send_from_directory(os.path.join("data", "userfiles", self.acc.getUserUniqueCode(), fileToDownload[0], fileToDownload[1]))

    def storageCreateFolderPathPage(self):
        if(not self.acc.userIsLoggedIn()):
            return redirect("/")
        
        data = self.getDataDefault()
        data['navHelp'] = render_template("smalltemplate/workpath.twig", paths=self.getPathBack(self.getLastPath()))
        data['files'] = self.getFilesForPath(self.getLastPath())

        goBackPath = self.getLastPath()
        if (len(goBackPath) != 0):
            goBackPath = "/"  + goBackPath
            
        data['popupHTML'] = render_template("popup/foldername.twig", exitpath = goBackPath)
        if request.method == 'POST' and request.form['foldername'] != None:   
            if (len(request.form['foldername']) != 0):
                foldername = request.form['foldername']
                userId = self.acc.getUserId()

                filehash = Modules.getUniqueCode(foldername)
                storagepath = self.getLastPath()

                Modules.executeIntoDB(f"INSERT INTO files (path, name, filehash, uploadUserId, share, folder, filesize) VALUES ('{storagepath}', '{foldername}', '{filehash}', {userId}, false, true, {0})")
                if (storagepath == ""):
                    return redirect("home")
                else:
                    return redirect("home/" + storagepath)
        
        return render_template("storage/home.twig", data=data)
    

    def storageUserSettingsPage(self):
        res = Modules.selectFromDB(f"SELECT name, email FROM users WHERE id='{self.acc.getUserId()}'")
        if (len(res) != 1):
            return redirect("logout")
        data = self.getDataDefault()
        data['navbarHTML'] = render_template("smalltemplate/navbar.twig", firstpage=True, path=self.getLastPath(), fileusedtext=self.getFileUsedText())
        if request.method == 'POST' and 'askforupdate' in request.form:
            updateitem = "email"
            text = "New email: "
            if request.form['askforupdate'] == "updatepsw":
                updateitem = "password"
                text = "New password: "
            data['popupHTML'] = render_template("popup/askforupdate.twig", type=updateitem, text=text, backpath="storage/settings")
        elif request.method == "POST" and 'confpsw' in request.form:
            res2 = Modules.selectFromDB(f"SELECT password, email FROM users WHERE id='{self.acc.getUserId()}'")
            hashpsw = Modules.hashPass(request.form['confpsw'])
            if (len(res2) != 1):
                return redirect("logout")
            if hashpsw == res2[0][0]:
                if request.form['type'] == "email":
                    self.acc.updateMail(request.form['newInfo'], res2[0][1], res2[0][0])
                    return redirect("settings")
                if request.form['type'] == "password":
                    newPsw = Modules.hashPass(request.form['newInfo'])
                    self.acc.updatePassword(newPsw, res2[0][1], res2[0][0])
                    return redirect("settings")
        return render_template("storage/settings.twig", name=res[0][0], email=res[0][1], data=data)
    
    def storageOpenShareMenu(self):
        data = self.getDataDefault()
        data['navHelp'] = render_template("smalltemplate/workpath.twig", firstpage=True, paths=self.getPathBack(self.getLastPath()))
        data['files'] = self.getFilesForPath(self.getLastPath())
        goBackPath = self.getLastPath()

        if (len(goBackPath) != 0):
            goBackPath = "/"  + goBackPath
            
        data['popupHTML'] = render_template("popup/foldername.twig", exitpath = goBackPath)
        return render_template("storage/home.twig", data=data)
# TODO 
# Visa användt utrymme i navbar [KLART]
# Visa filsökvägen till mappen, typ under sök [KLART]
# Fixa så sök fungerar [KLART]
# Begränsa så man inte kan överstiga upload limit [KLART]
# Lägg till så man kan dela filer [KLART]
# Återställa lösen osv, kontohantering [Delvis]
# POPUP som typ "file upload success" och "Not enough space", använda sessions?
# Skapa userfiles mapp om den ej finns