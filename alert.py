from flask import session, render_template
import os

class Alert:
    def __init__(self, app):
        self.app = app

    def getSavedAlerts(self):
        if session.get('alerts', []) != None:
            return session.get('alerts', [])
        else:
            return []
        
    def getColorFromType(self, alertType="default"):
        types = {
            "default": "#0676ed",
            "success": "#12c99b",
            "danger": "#f2a600",
            "error": "#e41749",
            "dark": "#151a30",
        }
        return types.get(alertType, types['default'])

    def addAlert(self, text, alertType="default", ms=5000):
        alertTypes = ["default", "success", "danger", "error", "dark"]
        if alertType not in alertTypes:
            raise ValueError("Invalid alert type. Expected one of: %s" % alertTypes)
        session_alerts = self.getSavedAlerts()
        newAlert = {"color": self.getColorFromType(alertType), "text": text, "time": ms}
        if not isinstance(session_alerts, list):
            session_alerts = []
        session_alerts.append(newAlert)
        session['alerts'] = session_alerts

    def getNextAlert(self):
        if len(self.getSavedAlerts()) > 0:
            session_alerts = self.getSavedAlerts()
            nextAlert = session_alerts[0]
           
            session_alerts.pop(0)
            session['alerts'] = session_alerts
            return nextAlert
        else:
            return ""