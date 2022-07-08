# -*- coding: utf-8 -*-
"""
Created on Fri Mar 11 10:54:44 2022
@author: Amanda
"""
import requests, json
import time, sys
import datetime, os
import pandas as pd

class DemoChannel:
    
    def __init__(self):
        self._data = self._loadData()
        self.friendly_names = self._data["friendly_name"]
        
    def _loadData(self):
        with open(self.resource_path("data.json"), "r") as f:
            data = json.load(f)
        return data

    @staticmethod
    def resource_path(relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        # base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)
    
    def getDemos(self):
        messages = self.readMessages()
        if messages:
            all_data = []
            for n, message in enumerate(messages):
                data = message["text"].split("\n")
                mined_data = {}
                for i in data:
                    if message["subtype"] == "bot_message" and message["bot_id"] == self._data["ids"]["bot"]:
                        try:
                            if i.split(": ")[0] == "Email":
                                email = i.split(": ")[1].split("|")[1][:-1]
                                mined_data.update({i.split(": ")[0] : email})
                            elif i.split(": ")[0].strip() == "LocationID":
                                location = self._data["friendly_name"][i.split(": ")[1]]
                                mined_data.update({"friendly_name" : location})
                                mined_data.update({i.split(": ")[0] : i.split(": ")[1]})
                            else:
                                mined_data.update({i.split(": ")[0] : i.split(": ")[1]})
                        except:
                            pass
                if "LocationID" in mined_data.keys():
                    all_data.append(mined_data)
        return all_data
    
    def toDf(self):
        demos = self.getDemos()
        df = pd.DataFrame.from_records(demos)
        df["Date"] = datetime.date.today()
        df = df[["Date", "Username", "Email", "friendly_name"]]
        df.columns = ["Date", "Username", "Email", "Location"]
        return df
        
    def toExcel(self, path = "output.xlsx"):
        df = self.toDf()
        df.to_excel(self.resource_path(path))
    
    def locationCount(self):
        demos = self.getDemos()
        output = {}
        for demo in demos:
            if demo["LocationID"] in output.keys():
                output[demo["LocationID"]] += 1
            else:
                output.update({demo["LocationID"]: 1})
        return output

    def readMessages(self, days = 1):
        headers = {"Authorization": "Bearer {}".format(self._data["secret"])}
        body = {
                "channel": self._data["ids"]["channel"],
                "oldest": time.mktime((datetime.datetime.today() - datetime.timedelta(days = 1)).timetuple())
                }
        r = requests.get(self._data["urls"]["request"], params = body, headers = headers)
        if r.status_code == 200:
            messages = r.json()["messages"]
            return messages
        else:
            return r.json()
        
    def notify_channel(self, message, testing = False):
            """
            Posts to webhook that sends a message contents to the slack channel
            Parameters
            ----------
            message : Yesterday's Demo Count
            KEY: 5 = ValVista, 6 = Oceanside, 7 = Tempe, 8 = Peoria
            Returns
            -------
            None.
            """
            
            if message:
                url = self._data["urls"]["rht_demos"] if not testing else self._data["urls"]["messaging_test"]
                data = {"text": message}
                r = requests.post(url, data = json.dumps(data))
           
if __name__ == "__main__":
    
    demo = DemoChannel()
    demo.toExcel()
    # locations = demo.locationCount()
    # message = "*YESTERDAYS DEMO COUNT TOTAL:*\n"
    # for i in locations:
    #     message += "{}: {} ".format(demo.friendly_names[i], locations[i])
    # demo.notify_channel(message)