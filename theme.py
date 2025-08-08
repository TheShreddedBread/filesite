from flask import session, render_template
import os
from alert import Alert
import json
class Theme:
    def __init__(self, app):
        self.app = app
        self.alert = Alert(app)

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

    def generateAlert(self):
        alert = self.alert.getNextAlert()
        if len(alert) > 0:
            return self.loadFileWithTheme("popup/alert.twig", color=alert['color'], text=alert['text'], ms=5000)
        else:
            return ""

    def loadFileWithTheme(self, file, alert="", **args):
        idealPath = f"{self.getUserTheme()}/{file}"
        if os.path.exists(os.path.join("templates",idealPath)):
            return render_template(idealPath, userTheme = self.getUserTheme(), alert=alert, **args)
        else:
            return render_template(f"{self.getDefaultTheme()}/{file}", userTheme = self.getDefaultTheme(), alert=alert, **args)
        
    def loadPage(self, file, **args):
        alertHTML = self.generateAlert()
        return self.loadFileWithTheme(file, alert=alertHTML, **args)
    