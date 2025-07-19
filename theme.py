from flask import session, render_template
import os
import json
class Theme:
    def __init__(self, app):
        self.app = app

    def setUserTheme(self, newTheme):
        session["theme"] = newTheme
    
    # THERE NEEDS TO BE ONE THEME WITH THE PATH: "default"
    def getDefaultTheme(self):
        return "default"
    
    def getUserTheme(self):
        return session.get('theme', self.getDefaultTheme())

    def getThemes(self):
        with open("config.json") as f:
            data = json.load(f)
            return data['themes']
        
    def loadFileWithTheme(self, file, **args):
        idealPath = f"{self.getUserTheme()}/{file}"
        print(idealPath)
        if os.path.exists(os.path.join("templates",idealPath)):
            print("OK")
            return render_template(idealPath, userTheme = self.getUserTheme(), **args)
        else:
            print("NOPE")
            return render_template(f"{self.getDefaultTheme()}/{file}", userTheme = self.getDefaultTheme(), **args)