# Last updated on 19 Mar 16
from tkinter import *
import datetime
import sys
import json
import ast
from contextlib import redirect_stdout
from io import StringIO
import urllib
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree.ElementTree import Element, tostring
import threading
import time

class PlmGui(Frame):
    itemRetrieval = False # Class variable used by threads to communicate status
        
    def __init__(self, master):
        Frame.__init__(self, master)
        self.master = master
        self.text = None
        self.sessionUser = StringVar()
        self.sessionPwd = StringVar()
        self.dmsID = StringVar()
        self.sku = StringVar()
        self.flag = IntVar()
        self.sessionCookie = None
        self.cookie = True # Set sessionCookie using the setter @property
        self.options = []
        self.attrDict = {}
        self.itemDict = {}
        self.getOptions()
        self.initUserInterface()
            
    # Getter and Setter methods follow for user, password, and cookie. 
    @property
    def user(self):
        return self.sessionUser.get()
    
    @user.setter
    def user(self, uname):
        self.sessionUser.set(uname)
        
    @property
    def pwd(self):
        return self.sessionPwd.get()
    
    @pwd.setter
    def pwd(self, passWord):
        self.sessionPwd.set(passWord)
        
    @property
    def cookie(self):
        return self.sessionCookie
    
    @cookie.setter
    def cookie(self, needCookie):
        if needCookie:
            self.sessionCookie = self.getAuthCredentials()
        
    def dict2Xml(self, tag, d):
        elem = Element(tag)
        for k, v in d.items():
            child = Element(k)
            child.text = str(v)
            print(str(v))
        return elem
        
        
    def clearText(self):
        self.text.delete(1.0, END)
        
    def setText(self, posn, txt):
        self.text.insert(posn, txt)

       
    def displayItemXml(self):
        self.clearText()
        item = self.getItem(self.cookie, "json")
        buf = StringIO()
        jsonObject = json.loads(item)
        self.getItemAttributes(jsonObject, 0, False)
        updates = {"JDE_LONG_ITEM_NUMBER": "", "DESC_1": "", "INTEGRATION_COMPLETE": "True"}
        p = self.getJsonPayload(updates)
        xmlstr = tostring(self.dict2Xml("test", p))
        
        self.text.insert(1.0, xmlstr)
        #for k, v in self.attrDict.items():
            #print(k, "  ", v)
    
    def getOptions(self):
        ''' Returns a list of all SKUs that will be populated in a drop down box. '''
        self.getAllItems(self.cookie, "json")
        self.options = sorted([item for item in self.itemDict.keys()])
        self.sku.set(self.options[0])
        
    def displayAllItems(self):
        self.clearText()
        self.getAllItems(self.cookie, "json")
        buf = StringIO()
        self.text.insert(1.0, self.getItemString(self.itemDict, 0, buf, False))
        
    def waitForDisplayItem(self):
        PlmGui.itemRetrieval = False
        cnt = 0
        while PlmGui.itemRetrieval == False:
            time.sleep(1)
            # Obtain a lock to prevent any concurrency issues.
            lock = threading.Lock()
            # Using "with" ensures that a lock is released upon completion of the code block
            with lock:
                cnt += 1
                if cnt % 15 == 0: # Use modulus to include a newline every 15 seconds. 
                    self.setText(END, "%i\n " % cnt)
                else:
                    self.setText(END, " %i " % cnt)
                
    def getCurrentTime(self):
        t = time.localtime()
        return str(t.tm_mday) + "/" + str(t.tm_mon)  + "/" + str(t.tm_year) + ": " + str(t.tm_hour).zfill(2) + ":" + str(t.tm_min).zfill(2) + ":" + str(t.tm_sec).zfill(2)
            
    def displayItem(self):
        try:
            print("Thread started at %s" % self.getCurrentTime())
            item = self.getItem(self.cookie, "json")
            buf = StringIO()
            jsonObject = json.loads(item)
            if self.flag.get():
                plmdata = self.getItemString(jsonObject, 0, buf, False)
            else:
                self.getItemAttributes(jsonObject, 0, False)
                plmdata = self.getItemString(self.attrDict, 0, buf, False)
            
            print("Thread finished at %s" % self.getCurrentTime())
                
            self.clearText()
            self.text.insert(1.0, plmdata)
        # Ensure itemRetrieval is set to True; otherwise the other thread will block until another item is selected.
        finally: 
            lock = threading.Lock()
            with lock:
                PlmGui.itemRetrieval = True
            
    
    # Have this method invoked from the queryPLMbutton to have the displayItem method run in a separate thread  
    def runDisplayItemThread(self):
        try:
            self.clearText()
            t = threading.Thread(target = self.displayItem)#, daemon = True)
            t.start()
            t2 = threading.Thread(target = self.waitForDisplayItem)
            t2.start() 
            #t.join(5.0)
        except:
            exceptionType, error = sys.exc_info()[:2]
            retstr = "runDisplyItemThread method failed: " + str(error)
            self.text.insert(1.0, repr(exceptionType) + " " + str(error))

        

    def initUserInterface(self):
        self.master.title("PLM-360 Item Master Viewer  ")
        self.frameone = Frame(self.master)
        self.frameone.grid(row = 0, column = 0)
        self.plmlbl = Label(self.frameone, text = "  PLM-360 Item Master Viewer  ", background = "white", foreground = "blue", font = "Times 20", relief = "raised")
        self.plmlbl.grid(row = 0, column = 0, columnspan = 5)
        self.userlbl = Label(self.frameone, font = "Times 12", text = "User ID").grid(row = 1, column = 0, sticky = "w", padx = 0, pady = 20, ipadx = 0, ipady = 0)
        self.userentry = Entry(self.frameone, width = 30, textvariable = self.sessionUser).grid(row = 1, column = 0, sticky = "w",  padx = 80, pady = 0, ipadx = 0, ipady = 0)
        self.passlbl = Label(self.frameone, font = "Times 12", text = "Password").grid(row = 1, column = 1, sticky = "w", padx = 0, pady = 0, ipadx = 0, ipady = 0)
        self.passentry = Entry(self.frameone, show = "*", textvariable = self.sessionPwd).grid(row = 1, column = 1, sticky = "w",  padx = 85, pady = 0, ipadx = 0, ipady = 0)
        self.blanklbl = Label(self.frameone, text = "").grid(row = 3)
        #self.dmsIdlbl = Label(self.frameone, font = "Times 12", text = "DMS ID").grid(row = 2, column = 0, sticky = "w", padx = 0, pady = 0, ipadx = 0, ipady = 0)
        #self.dmsIdentry = Entry(self.frameone, textvariable = self.dmsID).grid(row = 2, column = 0, sticky = "w",  padx = 80, pady = 0, ipadx = 0, ipady = 0)
        self.skuOptionMenu = OptionMenu(self.frameone, self.sku, *self.options).grid(row = 2, column = 0, sticky = "w")
        self.flagcb = Checkbutton(self.frameone, font = "Times 12", text = "Display JSON Object", variable = self.flag).grid(row = 2, column = 0, padx = 120)
        self.queryPLMbutton = Button(self.frameone, background = "blue", foreground = "white", font = "Times 12", relief = "raised", text = "Get Data", command = self.runDisplayItemThread).grid(row = 2, column = 1, sticky = "w")
        
        self.frametwo = Frame(self.master)
        self.frametwo.grid(row = 1, column = 0)
        self.text = Text(self.frametwo, wrap = NONE)
        self.text.grid(row = 0, column = 0)
        self.text.insert(1.0, "Enter text here")
        scroll_y = Scrollbar(self.frametwo, orient = VERTICAL, command = self.text.yview)
        self.text.config(yscrollcommand = scroll_y.set)
        scroll_y.grid(row = 0, column = 1, sticky = 'ns')
        scroll_x = Scrollbar(self.frametwo, orient = HORIZONTAL, command = self.text.xview)
        self.text.config(xscrollcommand = scroll_x.set)
        scroll_x.grid(row = 1, column = 0, sticky = "ew")
        
        self.framethree = Frame(self.master)
        self.framethree.grid(row = 3 ,column = 0)
        self.clearbutton = Button(self.framethree, font = "Times 12", text = "Clear", command = self.clearText)
        self.clearbutton.grid(row = 2, column = 0, sticky = "w", pady = 20)
        self.quitbutton = Button(self.framethree, font = "Times 12", foreground = "red", text = "Quit", command = self.master.destroy)
        self.quitbutton.grid(row = 2, column = 1, sticky = "w", padx = 20, pady = 20)
 
    def getAuthCredentials(self):
        try:
            if (self.user == "" or self.pwd == ""):
                self.user = "david.brady@g3enterprises.com"
                self.pwd = "Kimber1y"
            
            authUrl="https://g3enterprises.autodeskplm360.net/rest/auth/1/login"
            headers = {"Content-Type" : "application/json", "Accept": "application/json", "userID" : self.user, "password" : self.pwd}
            data = urlencode(headers).encode("utf-8")
            req = Request(authUrl, data)
            response = urlopen(req)
            authDict = json.loads(response.read().decode("utf-8")) 
            token, sessionId = authDict['customerToken'], authDict['sessionid']
            cookie = str("customer=%s; JSESSIONID=%s" % (token, sessionId))
            return cookie
        except:
            exceptionType, error = sys.exc_info()[:2]
            errmsg = repr(exceptionType) + " " + str(error)
            print(errmsg)
     
    def getItem(self, cookie, contentType):
        try:
            self.dmsID.set(self.itemDict[self.sku.get()])
            print("DmsID is " + self.dmsID.get())
            url = "https://g3enterprises.autodeskplm360.net/api/rest/v1/workspaces/53/items/{0}".format(self.dmsID.get())
            opener = urllib.request.build_opener(urllib.request.HTTPHandler)
            request = Request(url, data = None)
            request.add_header("Content-Type", "application/" + contentType)
            request.add_header("Accept", "application/" + contentType)
            request.add_header("Cookie", cookie)
            r = opener.open(request)
            return r.read().decode("utf-8")
        except Exception:
            self.cookie = True # May have failed because cookie expired...try getting a new cookie.
            # Extract only the exception type and value from the tuple returned by sys.exc_info()
            exceptionType, error = sys.exc_info()[:2]
            retstr = "getItem failed: " + str(error)
            errStr = repr(exceptionType) + " " + str(error)
            self.cookie = True 
            self.clearText()
            self.text.insert(1.0, errStr)

            
    def getAllItems(self, cookie, contentType):
        try:
            host = "https://g3enterprises.autodeskplm360.net"
            getAllUrl = host + "/api/v2/workspaces/53/items/?page-size=10" 
            opener = urllib.request.build_opener(urllib.request.HTTPHandler)
            request = Request(getAllUrl, data = None)
            request.add_header("Content-Type", "application/" + contentType)
            request.add_header("Accept", "application/" + contentType)
            request.add_header("Cookie", cookie)
            r = opener.open(request)
            res = json.loads(r.read().decode("utf-8"))
            items = res["elements"]
            for item in items:
                #print(str(item["id"]) + " - " + item["itemDescriptor"])
                id = str(item["id"])
                getItemUrl = host + "/api/v2/workspaces/53/items/" + id   
                opener = urllib.request.build_opener(urllib.request.HTTPHandler)
                request = Request(getItemUrl, data = None)
                request.add_header("Content-Type", "application/" + contentType)
                request.add_header("Accept", "application/" + contentType)
                request.add_header("Cookie", cookie)
                r = opener.open(request)
                res = json.loads(r.read().decode("utf-8"))
                sku = res['fields']['JDE_LONG_ITEM_NUMBER']
                self.itemDict[sku] = id
            
            #for k, v in itemDict.items():
            #    print(str(k), v)    
        
        except Exception:
            # Extract only the exception type and value from the tuple returned by sys.exc_info()
            exceptionType, error = sys.exc_info()[:2]
            retstr = "getItem failed: " + str(error)
            print(repr(exceptionType) + " " + str(error))

    
    def getItemString(self, d, depth, buf, sortReverse):
        try:
            for k, v in sorted(d.items(), key = lambda x: x[0], reverse = sortReverse):
                if isinstance(v, dict):
                    with redirect_stdout(buf):
                        print((" " * depth) + ("%s" % k))
                    self.getItemString(v, depth + 4, buf, sortReverse)
                else:
                    with redirect_stdout(buf):
                        print((" " * depth) + "%s %s" % (k, v))
    
            return buf.getvalue()
        except:
            exceptionType, error = sys.exc_info()[:2]
            retstr = "Error in getItemString(): " + str(error)
            print(retstr)

    def getItemAttributes(self, d, depth, debug = False):
    #  The purpose of this method is to generate a dictionary containing the attributes of an item.
    #  This is accomplished by recursively invoking this method until all attributes have been returned.
    #  This method should be called before generating a new payload to update an item.

        try: 
            count = 0
            for k, v in sorted(d.items(), key = lambda x: x[0]):
                if isinstance(v, dict):
                    if debug:
                        print((" " * depth) + ("%s" % k))
                    if k == "details":
                        for detKey, detValue in v.items():
                            if detKey == "versionID":
                                self.attrDict[detKey] = detValue
                    self.getItemAttributes(v, depth + 2, debug)
                if k == "entry":
                    for element in v:
                        count += 1
                        try:
                            self.attrDict[element["key"]] = element["fieldData"]
                        except:
                            pass # No data in this attribute so continue on
                            
                    if debug:
                        print("There are " + str(count) + " entries")
            #return attrDict
        except:
            exceptionType, error = sys.exc_info()[:2]
            retstr = "Error in getItemAttributes(): " + str(error)
            print(retstr)

    def getJsonPayload(self, updates):
    # This method takes the data stored in the attribute dictionary (attrDict) created in
    # getItemAttributes and prepares the JSON payload needed to update an item.
        try:
            def lookup(key):
                # This method is used to determine if any changes were made to the original item information.
                try:
                    if len(updates[key]) > 1:
                        return True
                    else:
                        return False
                except KeyError:
                    return False
    
            def getMultiSelect(bpList):
                # This method is needed when an attribute has multiple selections possible (e.g. branch plant)
                try:
                    values = ""
                    for e in bpList:
                        if values == "":
                            values = e["value"]
                        else:
                            values = values + "," + e["value"]
                    return values
                except:
                    return ["3"]
                
            payload = {}
            entry = {}
            elements = []
            for k, v in self.attrDict.items():
                try:
                    if k == "versionID":
                        payload["versionID"] = str(v)
                    else:
                        try:
                            if lookup(k): # Means there is an update
                                elements.append({"key": k, "value": updates[k]})
                            else: # Keep the data that was returned from PLM
                                if v["dataType"] == "Multiple Selection":
                                    strAttr = getMultiSelect(v["selections"])
                                    elements.append({"key": k, "value": strAttr})
                                else:
                                    elements.append({"key": k, "value": v["value"]})
                        except:
                            print("No value set for " + k)
                            pass # There is no value to set so keep going
                except:
                    print(k + ": " + repr(v))
            entry["entry"] = elements
            payload["metaFields"] = entry
            return payload
        except:
            exceptionType, error = sys.exc_info()[:2]
            retDict = {exceptionType: error}

         
if __name__ == "__main__":
    root = Tk()
    try:
        plm = PlmGui(root)
    except:
        exceptionType, error = sys.exc_info()[:2]
        print(str(exceptionType) + ": " + str(error))
        
    root.mainloop()