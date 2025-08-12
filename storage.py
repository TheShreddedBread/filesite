
import hashlib
import os
import sqlite3
import time
from theme import Theme
from alert import Alert
from modules import Modules
import math
from flask import Flask, render_template, request, redirect, send_from_directory, url_for, session

class Storage:
    def __init__(self, app, acc):
        self.acc = acc
        self.app = app
        self.theme = Theme(self.app)
        self.alert = Alert(self.app)

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
        return "storage/shared/"

    def validatePath(self, givenpath):
        startPath = self.getDefaultStoragePath()
        if(givenpath.count(startPath) > 1):
            givenpath = givenpath[len(startPath):-1]
        if givenpath == "":
            return True
        folderpath = Modules.selectFromDB("SELECT id FROM files WHERE folder = ? AND uploadUserId = ? AND filehash = ?", ('1', self.acc.getUserId(), givenpath))
        if (len(folderpath) != 0):
            if (len(folderpath[0]) != 0):
                return True
            
        sharedPath = self.getDefaultSharedStoragePath()
        if(givenpath.count(sharedPath) > 1):
            givenpath = givenpath[len(sharedPath):-1]
        if givenpath == "":
            return True
        
        fileId = Modules.selectFromDB("SELECT id FROM usershare WHERE filehash = ? and reciver = ?", (givenpath, self.acc.getUserId()))
        if (len(fileId) != 0):
            if (len(fileId[0]) != 0):
                return True
        return False

    def getPathBack(self, givenpath):
        pathToHome = []
        currpath = givenpath
        while currpath != "":
            folderpath = Modules.selectFromDB("SELECT path, name FROM files WHERE folder = ? AND uploadUserId = ? AND filehash = ?", ('1', self.acc.getUserId(), currpath))
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
            fileId = Modules.selectFromDB("SELECT id, uploadUserId, share FROM files WHERE filehash = ? and folder = ?", (currpath, '1'))

            if (len(fileId) != 0):
                if (len(fileId[0]) != 0):
                    if (fileId[0][2] == 0): # If share = 0
                        currpath = targetPath
                        break
                    sharedpath = Modules.selectFromDB("SELECT id FROM usershare WHERE reciver = ? AND sender = ? AND fileId = ?", (self.acc.getUserId(), fileId[0][1], fileId[0][0]))

                    if (len(sharedpath) != 0):
                        if (len(sharedpath[0]) != 0):
                            folderpath = Modules.selectFromDB("SELECT path, name FROM files WHERE folder = ? AND uploadUserId = ? AND filehash = ?", ('1', fileId[0][1], currpath))
                            
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
        data['navbarHTML'] = self.theme.loadFileWithTheme("smalltemplate/navbar.twig", firstpage=(self.getLastPath()==""), path=self.getLastPath(), fileusedtext=self.getFileUsedText())
        data['popupHTML'] = ""
        data['files'] = ""
        return data

    def getFileUsedText(self):
        spaceText = self.convert_size(self.acc.getUserCurrentStorage()) + " / " + self.convert_size(self.acc.getUserMaxStorage()*1048576)
        progress = self.acc.getUserCurrentStorage()/(self.acc.getUserMaxStorage()*1048576)
        return self.theme.loadFileWithTheme("smalltemplate/progressbar.twig", text=spaceText, progress=math.ceil(progress*100))

    def splitFilename(self, filename):
        name, ext = os.path.splitext(filename)
        if ext in ['.gz', '.bz2']:
            ext = os.path.splitext(name)[1] + ext
        return [name,ext]
    
    def getFilesForPath(self, path = ""):
        filesHTML = ""
        clickpath = self.getLastPath()
        # id INTEGER, path TEXT, name TEXT, filehash TEXT, uploadUserId INTEGER, share BOOLEAN, folder BOOLEAN, filesize INTEGER
        foundFiles = Modules.selectFromDB("SELECT * FROM files WHERE uploadUserId = ? AND path= ?", (self.acc.getUserId(), path))
        for file in foundFiles:
            fancyname = self.splitFilename(file[2])[0][0:12]
            if (len(file[2]) > len(fancyname)):
                fancyname += "..."

            if file[6] == 1:
                clickpath = file[3]

            filesHTML += self.theme.loadFileWithTheme("smalltemplate/storageSquares.twig", data={"id":file[0], "folder": file[6], "name": file[2], "fancyname": fancyname, "size": self.convert_size(file[7]), "path": clickpath})
        if (len(filesHTML) == 0):
            filesHTML = self.theme.loadFileWithTheme("smalltemplate/nofilesuploaded.twig")
        return filesHTML

    def getSharedFilesForPath(self, path = "", shared = False):
        filesHTML = ""
        loadedSharedFiles = []
        clickpath = self.getLastPath()
        # id INTEGER, path TEXT, name TEXT, filehash TEXT, uploadUserId INTEGER, share BOOLEAN, folder BOOLEAN, filesize INTEGER, sharePath TEXT
        foundFiles = Modules.selectFromDB("SELECT * FROM usershare WHERE reciver = ?", (self.acc.getUserId(),))
        for file in foundFiles:
            targetFile = Modules.selectFromDB("SELECT * FROM files WHERE id = ? AND uploadUserId = ? AND share = ? AND sharePath = ?", (file[3], file[1], path))
            if (len(targetFile) != 1):
                continue
            targetFile = targetFile[0]
            fancyname = self.splitFilename(targetFile[2])[0][0:12]
            if (len(targetFile[2]) > len(fancyname)):
                fancyname += "..."

            if targetFile[6] == 1:
                clickpath = targetFile[3]
            loadedSharedFiles.append(file[3])
            filesHTML += self.theme.loadFileWithTheme("smalltemplate/storageSquares.twig", data={"id":targetFile[0], "folder": targetFile[6], "name": targetFile[2], "fancyname": fancyname, "size": self.convert_size(targetFile[7]), "path": clickpath, "shared": shared})
        session['loadedSharedFiles'] = loadedSharedFiles
        if (len(filesHTML) == 0):
            filesHTML = self.theme.loadFileWithTheme("smalltemplate/nosharedfiles.twig")
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
        data['navHelp'] = self.theme.loadFileWithTheme("smalltemplate/workpath.twig", paths=pathWay)

        if (len(pathWay) <= 1):
            ahrefpath = "storage/home"
        else:
            ahrefpath = "storage/home/" + pathWay[-2][0]
        
        if request.method == 'POST' and 'type' in request.form:   
            if request.form['type'] == "download":
                fileId = request.form['id']
                files = Modules.selectFromDB("SELECT path, filehash, name FROM files WHERE id = ? AND uploadUserId = ?", (fileId, self.acc.getUserId()))
                fileToDownload = files[0]
                instantPath = self.app.instance_path
                folderPath = "\\".join(instantPath.split("\\")[0:-1])
                userFilesPath = (os.path.join(folderPath ,"data", "userfiles", self.acc.getUserUniqueCode(), fileToDownload[0]))
                fileExt = self.splitFilename(fileToDownload[2])[1]
                return send_from_directory(userFilesPath, (fileToDownload[1] + fileExt), as_attachment=True, download_name=(fileToDownload[2]))

            elif request.form['type'] == "askfordelete":
                fileId = request.form['id'] 
                userFiles = Modules.selectFromDB("SELECT id, name, folder FROM files WHERE id = ? AND uploadUserId = ?", (fileId, self.acc.getUserId()))
                if (len(userFiles) >= 1):
                    fileDelHash = Modules.md5Hash(str(userFiles[0][0] * self.acc.getUserId()))
                    session['deleteFileHash'] = fileDelHash
                    session['deleteFileId'] = userFiles[0][0]
                    currPath = "storage/home"
                    if (len(path) != 0):
                        currPath += ("/" + path) 
                    itemText = "The file"
                    if str(userFiles[0][2]) == "1":
                        itemText = "The folder"
                    data['popupHTML'] = self.theme.loadFileWithTheme("popup/confirmdelete.twig", backpath=currPath, fileDeleteHash=fileDelHash, filename=userFiles[0][1], itemType=itemText)
            elif request.form['type'] == "sharemenu":
                fileId = request.form['id']
                files = Modules.selectFromDB("SELECT share, name FROM files WHERE id = ? AND uploadUserId = ?", (fileId, self.acc.getUserId()))
                if (len(files) == 1):
                    session['sharetargetId'] = fileId
                    shareFile = files[0]
                    currPath = "storage/home"
                    if (len(path) != 0):
                        currPath += ("/" + path) 

                    usersData = []
                    if (shareFile[0] == 1): 
                        users = Modules.selectFromDB("SELECT reciver FROM usershare WHERE sender = ? AND fileId = ?", (self.acc.getUserId(), fileId))
                        for user in users:
                            userInfo = Modules.selectFromDB("SELECT id, name, email FROM users WHERE id = ?", (user[0],))
                            if (len(userInfo) == 1):
                                if (userInfo[0][0] != self.acc.getUserId() and users[0][0] == userInfo[0][0]):
                                    usersData.append([userInfo[0][0], userInfo[0][1], userInfo[0][2]])
                    data['popupHTML'] = self.theme.loadFileWithTheme("popup/sharemenu.twig", backpath=currPath, checked=(shareFile[0]==1), filename=shareFile[1], users=usersData)
            
            elif request.form['type'] == "toggleshare":
                fileId = session['sharetargetId']
                val = request.form.getlist('sharestate')
                if (len(val) != 0):
                    self.alert.addAlert("Sharing enabled", "success")
                    if (val[0] == "allowed"):
                        if path == "":
                            Modules.executeIntoDB("UPDATE files SET share= ?, sharePath=? WHERE id = ? AND uploadUserId = ?", ('1', '', fileId, self.acc.getUserId()))
                        else:
                            sharedFolders = Modules.selectFromDB("SELECT id FROM files WHERE filehash = ? AND uploadUserId = ? AND folder = ? AND share = ?", (path, self.acc.getUserId(), '1', '1'))
                            if (len(sharedFolders) == 1):
                                Modules.executeIntoDB("UPDATE files SET share=?, sharePath = ? WHERE id = ? AND uploadUserId = ?", ('1', path, fileId, self.acc.getUserId())) # in shared folder
                            else:
                                Modules.executeIntoDB("UPDATE files SET share=?, sharePath='' WHERE id = ? AND uploadUserId = ?", ('1', '', fileId, self.acc.getUserId())) # not in shared folder
                else: 
                    self.alert.addAlert("Sharing disabled", "danger")
                    Modules.executeIntoDB("UPDATE files SET share=? WHERE id = ? AND uploadUserId = ?", ('0', fileId, self.acc.getUserId()))
            
            elif request.form['type'] == "updatesharedusers":
                fileId = session['sharetargetId']
                val = request.form.getlist('sharestate')
                if (len(val) != 0):
                    if (val[0] == "allowed"):
                        Modules.executeIntoDB("UPDATE files SET share = ? WHERE id = ? AND uploadUserId = ?", ('1', fileId, self.acc.getUserId()))
                else: 
                    Modules.executeIntoDB("UPDATE files SET share=? WHERE id = ? AND uploadUserId = ?", ('0', fileId, self.acc.getUserId()))
            
            elif request.form['type'] == "updateusers":
                fileId = session['sharetargetId']
                newMailList = request.form.getlist('addedmail')
                targetFile = Modules.selectFromDB("SELECT id, folder, filehash FROM files WHERE id = ? AND uploadUserId = ? AND share = ?", (fileId, self.acc.getUserId(), '1'))
                if len(targetFile) == 1:
                    allToBeAdded = []
                    for mail in newMailList:
                        correctMail = mail.strip()
                        result = Modules.selectFromDB("SELECT id, email FROM users WHERE email = ?", (correctMail))
                        if (len(result) == 1):
                            if (result[0][0] != self.acc.getUserId()):
                                allToBeAdded.append(result[0][0])
                                if (len(Modules.selectFromDB("SELECT id FROM usershare WHERE sender = ? AND reciver = ? AND fileId = ?"), (self.acc.getUserId(), result[0][0], targetFile[0][0])) == 0):
                                    Modules.executeIntoDB("INSERT INTO usershare (sender, reciver, fileId, folder, filehash) VALUES (?, ?, ?, ?, ?)", (self.acc.getUserId(), result[0][0], targetFile[0][0], targetFile[0][1], targetFile[0][2]))

                    currentShared = Modules.selectFromDB("SELECT reciver FROM usershare WHERE sender = ? AND fileId = ?", (self.acc.getUserId(), targetFile[0][0]))
                    if len(currentShared) >= 1:
                        for user in currentShared:
                            if (user[0] not in allToBeAdded):
                                Modules.executeIntoDB("DELETE FROM usershare WHERE sender = ? AND reciver = ? AND fileId = ?", (self.acc.getUserId(), user[0], targetFile[0][0]))
                    self.alert.addAlert("Users have been updated", "success")

            elif (session.get('deleteFileHash') != None):
                if (session.get('deleteFileHash') == request.form['type']):
                    fileData = Modules.selectFromDB("SELECT id, name, filehash, path, folder FROM files WHERE uploadUserId = ? AND id = ? LIMIT 1", (self.acc.getUserId(), session.get('deleteFileId')))
                    if len(fileData) == 1:
                        if (fileData[0][4] == 0):
                            self.alert.addAlert("File has been deleted", "error")
                            Modules.executeIntoDB("DELETE FROM files WHERE uploadUserId = ? AND id = ? AND filehash = ?", (self.acc.getUserId(), fileData[0][0], fileData[0][2]))
                            Modules.executeIntoDB("DELETE FROM usershare WHERE sender = ? AND fileId = ? AND filehash = ?", (self.acc.getUserId(), fileData[0][0], fileData[0][2]))
                            filePath = f"data/userfiles/{self.acc.getUserUniqueCode()}/{fileData[0][2]}{self.splitFilename(fileData[0][1])[1]}"
                            if (os.path.exists(filePath)):
                                os.remove(filePath)
                        else:
                            self.alert.addAlert("Folder has been deleted", "error")

                            allUserFiles = Modules.selectFromDB("SELECT id, path, folder, name, filehash FROM files WHERE uploadUserId = ?", (self.acc.getUserId(),))
                           
                            targetedPath = fileData[0][1] + "/"
                            if (len(fileData[0][3]) != 0):
                                targetedPath += fileData[0][3] + "/"

                            for uFile in allUserFiles:
                                if (uFile[1].startswith(targetedPath) or uFile[1] == targetedPath[0:-1] or uFile[4] == fileData[0][2]):
                                    Modules.executeIntoDB("DELETE FROM files WHERE uploadUserId = ? AND id = ?", (self.acc.getUserId(), uFile[0]))
                                    Modules.executeIntoDB("DELETE FROM usershare WHERE sender = ? AND fileId = ?", (self.acc.getUserId(), uFile[0]))
                                    filePath = f"data/userfiles/{self.acc.getUserUniqueCode()}/{uFile[4]}{self.splitFilename(uFile[3])[1]}"
                                    if (os.path.exists(filePath) and uFile[2] == 0):
                                        os.remove(filePath)

                        session['deleteFileHash'] = None
                        session['deleteFileId'] = None
                    
        data['files'] = self.getFilesForPath(path)
        data['navbarHTML'] = self.theme.loadFileWithTheme("smalltemplate/navbar.twig", firstpage=(self.getLastPath()==""), backpath=ahrefpath, fileusedtext=self.getFileUsedText())
        return self.theme.loadPage("storage/home.twig", data=data)
    

    def storageSharedPage(self, path=""):
        if(not self.acc.userIsLoggedIn() or self.validatePath(path) == False):
            return redirect("/")
        
        data = self.getDataDefault()

        session['lastStoragePath'] = path
        
        pathWay = self.getPathSharedBack(path)
        data['navHelp'] = self.theme.loadFileWithTheme("smalltemplate/workpath.twig", paths=pathWay, share=True)
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
                    files = Modules.selectFromDB("SELECT path, filehash, name, uploadUserId FROM files WHERE id = ? AND share = ?", (fileId, '1'))
                    if (len(files) == 1):
                        userDetails = Modules.selectFromDB("SELECT uniqueCode FROM users WHERE id = ?", (files[0][3], ))
                        if (len(userDetails) == 1):
                            fileToDownload = files[0]
                            instantPath = self.app.instance_path
                            folderPath = "\\".join(instantPath.split("\\")[0:-1])
                            userFilesPath = (os.path.join(folderPath ,"data", "userfiles", userDetails[0][0]))
                            fileExt = self.splitFilename(fileToDownload[2])[1]
                            return send_from_directory(userFilesPath, (fileToDownload[1] + fileExt), as_attachment=True, download_name=(fileToDownload[2]))
        data['files'] = self.getSharedFilesForPath(path, shared=True)
        data['navbarHTML'] = self.theme.loadFileWithTheme("smalltemplate/navbar.twig", firstpage=(self.getLastPath()==""), backpath=ahrefpath, fileusedtext=self.getFileUsedText())
        return self.theme.loadPage("storage/home.twig", data=data)
    

    def storageUploadPage(self):
        return self.storageUploadPathPage("")
    
    def storageUploadPathPage(self, path):
        if(not self.acc.userIsLoggedIn()):
            return redirect("/")
        data = {}
        data = self.getDataDefault()
        last = self.getLastPath()
        data['navHelp'] = self.theme.loadFileWithTheme("smalltemplate/workpath.twig", paths=self.getPathBack(last))
        data['files'] = self.getFilesForPath(last)
        if (last == ""):
            data['popupHTML'] = self.theme.loadFileWithTheme("popup/uploadfile.twig", exitpath = "/storage/home")
        else:
            data['popupHTML'] = self.theme.loadFileWithTheme("popup/uploadfile.twig", exitpath = ("/storage/home/" + last))
        data['navbarHTML'] = self.theme.loadFileWithTheme("smalltemplate/navbar.twig", firstpage=(last==""), path=last, fileusedtext=self.getFileUsedText())

        if request.method == 'POST':   
            storagepath = last
            f = request.files['file'] 
            
            userId = self.acc.getUserId()
            pathToUploadTo = f"data/userfiles/{self.acc.getUserUniqueCode()}/"
            filename = f.filename
            filedata = f.read()
            filesize = len(filedata)
            if (self.acc.getUserStorageLeft() - filesize < 0):
                self.alert.addAlert("Not enough space left", "error")
                return redirect("/storage/home")
            if (len(Modules.selectFromDB("SELECT * FROM files WHERE uploadUserId = ?", (self.acc.getUserId(),))) == 0 and not os.path.exists(pathToUploadTo)):
                os.mkdir(pathToUploadTo)
            filehash = Modules.getUniqueCode(filename)
            name,ext = self.splitFilename(filename)

            if (Modules.executeIntoDB("INSERT INTO files (path, name, filehash, uploadUserId, share, folder, filesize) VALUES (?, ?, ?, ?, false, false, ?)", (storagepath, filename, filehash, userId, filesize)) != None):
                with open(pathToUploadTo + filehash + ext, "wb") as binary_file:
                    binary_file.write(filedata)
                    uploadedPath = "/storage/home"
                    if (last != ""):
                        uploadedPath += ("/" + last)
                    self.alert.addAlert("File has been uploaded", "default")
                return redirect(uploadedPath)
            else:
                return redirect("/storage/upload")
        else:
            return self.theme.loadFileWithTheme("storage/home.twig", data=data)
    

    def storageDownloadFile(self, fileId, uploderId =-1):
        if(not self.acc.userIsLoggedIn()):
            return redirect("/")
        
        if(uploderId == -1):
            uploderId = self.acc.getUserId()
        
        files = Modules.selectFromDB("SELECT (path, filehash) FROM files WHERE id = ? AND uploadUserId = ?", (fileId, uploderId))
        fileToDownload = files[0]

        return send_from_directory(os.path.join("data", "userfiles", self.acc.getUserUniqueCode(), fileToDownload[0], fileToDownload[1]))

    def storageCreateFolderPathPage(self):
        if(not self.acc.userIsLoggedIn()):
            return redirect("/")
        
        data = self.getDataDefault()
        data['navHelp'] = self.theme.loadFileWithTheme("smalltemplate/workpath.twig", paths=self.getPathBack(self.getLastPath()))
        data['files'] = self.getFilesForPath(self.getLastPath())

        goBackPath = self.getLastPath()
        if (len(goBackPath) != 0):
            goBackPath = "/"  + goBackPath
            
        data['popupHTML'] = self.theme.loadFileWithTheme("popup/createfolder.twig", exitpath = goBackPath)
        if request.method == 'POST' and request.form['foldername'] != None:   
            if (len(request.form['foldername']) != 0):
                foldername = request.form['foldername']
                userId = self.acc.getUserId()

                filehash = Modules.getUniqueCode(foldername)
                storagepath = self.getLastPath()
                Modules.executeIntoDB("INSERT INTO files (path, name, filehash, uploadUserId, share, folder, filesize) VALUES (?, ?, ?, ?, false, true, ?)", (storagepath, foldername, filehash, userId, '0'))
                self.alert.addAlert("Folder has been created", "default")
                if (storagepath == ""):
                    return redirect("home")
                else:
                    return redirect("home/" + storagepath)

        return self.theme.loadFileWithTheme("storage/home.twig", data=data)
    

    def storageUserSettingsPage(self):
        res = Modules.selectFromDB("SELECT name, email FROM users WHERE id = ?", (self.acc.getUserId(), ))
        if (len(res) != 1):
            return redirect("logout")
        data = self.getDataDefault()
        allThemes = self.theme.getThemes()
        data['navbarHTML'] = self.theme.loadFileWithTheme("smalltemplate/navbar.twig", firstpage=True, path=self.getLastPath(), fileusedtext=self.getFileUsedText())
        if request.method == 'POST' and 'askforupdate' in request.form:
            if request.form['askforupdate'] == "updatetheme":
                try:
                    int(request.form['theme'])
                except:
                    return redirect('settings')
                self.theme.setUserTheme(allThemes[int(request.form['theme'])]['path'])
                return redirect('settings')
            else:
                updateitem = "email"
                text = "New email: "
                if request.form['askforupdate'] == "updatepsw":
                    updateitem = "password"
                    text = "New password: "
                data['popupHTML'] = self.theme.loadFileWithTheme("popup/askforupdate.twig", type=updateitem, text=text, backpath="storage/settings")
        elif request.method == "POST" and 'confpsw' in request.form:
            res2 = Modules.selectFromDB("SELECT password, email FROM users WHERE id = ?", (self.acc.getUserId(), ))
            hashpsw = Modules.hashPass(request.form['confpsw'])
            if (len(res2) != 1):
                return redirect("logout")
            if hashpsw == res2[0][0]:
                if request.form['type'] == "email":
                    self.acc.updateMail(request.form['newInfo'], res2[0][1], res2[0][0])
                    self.alert.addAlert("Password has been updated", "success")
                    return redirect("settings")
                if request.form['type'] == "password":
                    newPsw = Modules.hashPass(request.form['newInfo'])
                    self.alert.addAlert("Password has been updated", "default")
                    self.acc.updatePassword(newPsw, res2[0][1], res2[0][0])
                    return redirect("settings")
            else:
                self.alert.addAlert("Wrong password", "error")
        return self.theme.loadPage("storage/settings.twig", themes=allThemes, curTheme = self.theme.getUserTheme(), name=res[0][0], email=res[0][1], data=data)

    def storageOpenShareMenu(self):
        data = self.getDataDefault()
        data['navHelp'] = self.theme.loadFileWithTheme("smalltemplate/workpath.twig", firstpage=True, paths=self.getPathBack(self.getLastPath()))
        data['files'] = self.getFilesForPath(self.getLastPath())
        goBackPath = self.getLastPath()

        if (len(goBackPath) != 0):
            goBackPath = "/"  + goBackPath
            
        data['popupHTML'] = self.theme.loadFileWithTheme("popup/foldername.twig",theme=self.theme.getUserTheme(), exitpath = goBackPath)
        return self.theme.loadFileWithTheme("storage/home.twig", data=data)