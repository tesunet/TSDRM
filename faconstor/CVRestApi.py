# -*- coding: utf-8 -*-

import sys
import os
import requests
import time
import copy
import subprocess
try: 
  import xml.etree.cElementTree as ET 
except ImportError: 
  import xml.etree.ElementTree as ET 
from xml.etree.ElementTree import Element  
import base64
try:
    import urllib.request  as urllib
except:
    import urllib
    
class CV_RestApi_Token(object):
    """
    Class documentation goes here.
    it is CV Rest API
            
    member
        init 
        login(credit) return None/token
        setAccess
    """    
    def __init__(self):
        """
        Constructor
        """
        #super().__init__()
        self.service = 'http://<<server>>:<<port>>/SearchSvc/CVWebService.svc/'
        self.credit = {"webaddr":"", "port":"", "username":"", "passwd":"", "token":"", "lastlogin":0}
        self.isLogin = False
        self.msg = ""
        self.sendText = ""
        self.receiveText = ""

    def login(self, credit):
        if self.isLogin == False:
            self.credit["token"] = None
            self.credit["lastlogin"] = 0
            
        try:
            self.credit["webaddr"] = credit["webaddr"]
            self.credit["port"] = credit["port"]
            self.credit["username"] = credit["username"]
            self.credit["passwd"] = credit["passwd"]
            self.credit["token"] = credit["token"]
            self.credit["lastlogin"] = credit["lastlogin"]
        except:
            self.msg = "login information is not correct"
            return None
            
        if self.credit["token"] != None:
            if self.credit["token"].count("QSDK") == 1:
                diff = time.time() - self.credit["lastlogin"] 
                if diff <= 550:
                    return self.credit["token"]
        
        self.isLogin = self._login(self.credit)
        return self.credit["token"]

    def _login(self, credit):
        """
        Constructor 
        login function
        """
        self.isLogin = False
        self.credit["token"] = None
        #print(credit)
        self.service = self.service.replace("<<server>>", self.credit["webaddr"])
        self.service = self.service.replace("<<port>>", self.credit["port"])
        
        password = base64.b64encode(self.credit["passwd"].encode(encoding="utf-8"))
        
        loginReq = '<DM2ContentIndexing_CheckCredentialReq mode="Webconsole" username="<<username>>" password="<<password>>" />'
        loginReq = loginReq.replace("<<username>>", self.credit["username"])      
        loginReq = loginReq.replace("<<password>>", password.decode())
        
        self.sendText = self.service + 'Login' + loginReq
        try:
            r = requests.post(self.service + 'Login', data=loginReq)
        except:
            self.msg = "Connect Failed: webaddr " + self.credit["webaddr"] + " port " + self.credit["port"]
            return False
        
        if r.status_code == 200:
            try:
                root = ET.fromstring(r.text)
            except:
                self.msg = "return string is not formatted"
                return False
                
            if 'token' in root.attrib:
                self.credit["token"] = root.attrib['token']
                if self.credit["token"].count("QSDK") == 1:
                    self.isLogin = True
                    self.credit["lastlogin"] = time.time()
                    self.msg = "Login Successful"
                    return True
                else:
                    self.msg = "Login Failed: username " + self.credit["username"] + " passwd " + self.credit["passwd"]
        else:
            self.msg = "Connect Failed: webaddr " + self.credit["webaddr"] + " port " + self.credit["port"]
        
        return False
    
    def checkLogin(self):
        return self.login(self.credit)

class CV_RestApi(object):
    """
    Class documentation goes here.
    it is CV Rest API
    Base Class for CV RestAPI
    attrib
        service is CV webaddr service string
        msg is error/success msg
        
    member
        init 
        login(credit) return None/token
        setAccess
    """    
    def __init__(self,token):
        """
        Constructor
        """
        super(CV_RestApi, self).__init__()
        self.service = 'http://<<server>>:<<port>>/SearchSvc/CVWebService.svc/'
        self.webaddr = token.credit["webaddr"]
        self.port = token.credit["port"]
        self.service = self.service.replace("<<server>>", token.credit["webaddr"])
        self.service = self.service.replace("<<port>>", token.credit["port"])
        #self.service = self.service.replace("<<server>>", webaddr)
        #self.service = self.service.replace("<<port>>", port)
        self.token = token
        self.msg = ""
        self.sendText = ""
        self.receiveText = ""

        
    def getCmd(self, command, updatecmd=""):
        """
        Constructor 
        get command function
        """
        token = self.token.checkLogin()
        if token == None:
            self.msg = "did not get token"
            return None
            
        clientPropsReq = self.service + command
        self.sendText = clientPropsReq
        
        update = updatecmd.encode(encoding="utf-8")
        
        headers = {'Cookie2': token}
        try:
            r = requests.get(clientPropsReq, data=update, headers=headers)
        except:
            self.msg = "Connect Failed: webaddr " + self.webaddr + " port " + self.port
            return None
            
        if r.status_code == 200:
            self.receiveText = r.text
        else:
            self.msg = "Connect Failed: webaddr " + self.webaddr + " port " + self.port
        
        if self.receiveText == None:
            self.msg = "No response string " + self.webaddr + " port " + self.port
            return None
        
        try:
            return ET.fromstring(self.receiveText)
        except:
            self.msg = "receive string is not XML format"
            return None
        
    def postCmd(self, command, updatecmd=""):        
        """
        Constructor 
        get command function
        """
        token = self.token.checkLogin()
        if token == None:
            self.msg = "did not get token"
            return None
        
        clientPropsReq = self.service + command
        self.sendText = clientPropsReq + updatecmd
        
        headers = {'Cookie2': token}
        update = updatecmd.encode(encoding="utf-8")
        
        try:
            r = requests.post(clientPropsReq, data=update, headers=headers)
        except:
            self.msg = "Connect Failed: webaddr " + self.webaddr + " port " + self.port
            return None
        
        if r.status_code == 200:
            self.receiveText = r.text
            return self.receiveText
        else:
            self.msg = "Connect Failed: webaddr " + self.webaddr + " port " + self.port
            return None
    
    def delCmd(self, command, updatecmd = ""):
        #DELETE <webservice>/Backupset/{backupsetId}
        token = self.token.checkLogin()
        if token == None:
            self.msg = "did not get token"
            return False
        
        clientPropsReq = self.service + command
        self.sendText = clientPropsReq + updatecmd
        
        headers = {'Cookie2': token}
        update = updatecmd.encode(encoding="utf-8")
        
        try:
            r = requests.delete(clientPropsReq, data=update, headers=headers)
        except:
            self.msg = "Connect Failed: webaddr " + self.webaddr + " port " + self.port
            return False
        
        if r.status_code == 200:
            self.receiveText = r.text
        else:
            self.msg = "Connect Failed: webaddr " + self.webaddr + " port " + self.port
            return False

        try:
            resp = ET.fromstring(self.receiveText)
        except:
            self.msg = "receive string is not XML format: " + self.receiveText
            return False
            
        respEle = resp.findall(".//response")
        errorCode = ""        
        for node in respEle:
            errorCode = node.attrib["errorCode"]
        if errorCode == "0":
            # self.msg = "Properties set successfully"
            return True
        else:
            try:
                errString = node.attrib["errorString"]
                self.msg = " errorString: " + errString
            except:
                self.msg = "unknown error: " + self.receiveText
                
            return False    

    def putCmd(self, command, updatecmd = ""):
        #DELETE <webservice>/Backupset/{backupsetId}
        token = self.token.checkLogin()
        if token == None:
            self.msg = "did not get token"
            return None
        
        clientPropsReq = self.service + command
        self.sendText = clientPropsReq + updatecmd
        
        headers = {'Cookie2': token}
        update = updatecmd.encode(encoding="utf-8")
        
        try:
            r = requests.put(clientPropsReq, data=update, headers=headers)
        except:
            self.msg = "Connect Failed: webaddr " + self.webaddr + " port " + self.port
            return None
        
        if r.status_code == 200:
            self.receiveText = r.text
            return self.receiveText
        else:
            self.msg = "Connect Failed: webaddr " + self.webaddr + " port " + self.port
            return None
    
        return None

        
    def qCmd(self, command, param=""):
        """
        Constructor 
        get command function
        """
        token = self.token.checkLogin()
        if token == None:
            self.msg = "did not get token"
            return None
        
        clientPropsReq = command + " " + param + " -tk " + token[5:]
        self.sendText = clientPropsReq
        s = subprocess.Popen(str(clientPropsReq), stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        (stdoutinfo, stderrinfo) = s.communicate()
        #print("ret: ", s.returncode)
        #print("stdout", stdoutinfo)
        #print("stderror", stderrinfo)
        
        if s.returncode == 0:
            self.receiveText = stdoutinfo
            return True
        else:
            self.receiveText = stderrinfo
            return False
        return
    
class CV_GetAllInformation(CV_RestApi):	
    """
    class CV_getAllInformation is get total information class 
    include client, subclient, storagePolice, schdule, joblist
    spList = {"storagePolicyId", "storagePolicyName"}
    schduleList = {"taskName", "associatedObjects", "taskType", "runUserId", "taskId", "ownerId", "description", "ownerName", "policyType", "GUID", "alertId"}
    clientList = {"clientId", "clientName", "_type_"}
    
    getSPlist return storage Police list
    getSchduleList return schdule List
    getClientList return client List
    
    """
    def __init__(self, token):
        """
        Constructor
        """
        super(CV_GetAllInformation, self).__init__(token)
        self.SPList = []
        self.SchduleList = []
        self.clientList = []
        self.clientListByAgent = []
        self.backupset = []
        self.subclient = []
        self.jobList = []
        self.vmDCName = []
        self.vmESXHost = []
        self.vmDataStore = []
        self.vmList = []
        
    def getAllSPList(self):    
        del self.SPList[:]
        client = self.getCmd('StoragePolicy')
        if client == None:
            return None
            
        activePhysicalNode = client.findall(".//policies")
        #print(activePhysicalNode)
        
        for node in activePhysicalNode:
            if node.attrib["storagePolicyId"] <= "2":
                continue
            if "System Create" in node.attrib["storagePolicyName"]:
                continue
            self.SPList.append(node.attrib)
        
        #self.msg  = "Client List Num is: " + self.clientList.count()
        return self.SPList

    def getAllSchduleList(self):    
        del self.SchduleList[:]
        client = self.getCmd('SchedulePolicy')
        if client == None:
            return None
            
        activePhysicalNode = client.findall(".//task")
        #print(activePhysicalNode)
        
        for node in activePhysicalNode:
            if "System Created " in node.attrib["taskName"]:
                continue
            self.SchduleList.append(node.attrib)
        
        #self.msg  = "Client List Num is: " + self.clientList.count()
        return self.SchduleList
    
    def getClientList(self):
        del self.clientList[:]

        #print (time.asctime())
        client = self.getCmd('/Client')
        if client == None:
            return None
        #print (time.asctime())
            
        activePhysicalNode = client.findall(".//clientEntity")
        for node in activePhysicalNode:
            self.clientList.append(node.attrib)
        return self.clientList
    
	
    def getClientListByAgentType(self, agentType):
        self.getClientList()
        for node in self.clientList():
            clientId = node["clientId"]
            command = "Agent?clientId=<<clientId>>"
            command = command.replace("<<clientId>>", self.clientId)
            resp = self.getCmd(command)
            try:
                activePhysicalNode = resp.findall(".//idaEntity")
                for node in activePhysicalNode:
                    self.agentType.append(node.attrib)
            except:
                self.msg = "error get agent type"
        
		
	
    def getJobList(self, clientId, type = "backup", appTypeName=None, backupsetName = None, subclientName = None, start = None, end = None):
        statusList = {"Running":"运行", "Waiting":"等待", "Pending":"阻塞", "Suspend":"终止", "commpleted":"完成", "Failed":"失败", "Failed to Start":"启动失败", "Killed":"杀掉"}
        '''
        Running
        Waiting
        Pending
        Suspend
        Kill Pending
        Interrupt Pending
        Interrupted
        QueuedCompleted
        Completed w/ one or more errors
        Completed w/ one or more warnings
        Committed
        Failed
        Failed to Start
        Killed
        '''
        del self.jobList[:]
        command = "/Job?clientId=<<clientId>>"
        param = ""
        if type != None:
            param = "&jobFilter=<<type>>"
        cmd = command + param
        cmd = cmd.replace("<<clientId>>", clientId)
        cmd = cmd.replace("<<type>>", type)
        client = self.getCmd(cmd)
        
        if client == None:
            return None
            
        #print(self.receiveText)
        activePhysicalNode = client.findall(".//jobs/jobSummary")
        for node in activePhysicalNode:
            #if start != None:
            #if end != None:
            #print(node.attrib)
            if appTypeName != None:
                if node.attrib["appTypeName"] != appTypeName:
                    continue;
            if backupsetName != None:
                if node.attrib["backupSetName"] != backupsetName:
                    continue;
            if subclientName != None:
                if node.attrib["subclientName"] != subclientName:
                    continue;
            status = node.attrib["status"]
            try:
                node.attrib["status"] = statusList[status]
            except:
                node.attrib["status"] = status
            self.jobList.append(node.attrib)
            
        return self.jobList
        
    def checkRunningJob(self, clientName, appType , backupsetName , instanceName ):
        command = "QCommand/qlist job -c <<clientName>> -format xml"
        command = command.replace("<<clientName>>", clientName)
        retString = self.postCmd(command)
        try:
            resp = ET.fromstring(retString)
        except:
            self.msg = "qlist job xml format is error"
            return False

        #print(clientName, appType, backupsetName, instanceName)
        jobitems = resp.findall(".//jobs")
        for node in jobitems:
            attrib = node.attrib
            #print(attrib, clientName, appType, backupsetName, instanceName)
            if attrib["clientName"] == clientName:
                #if attrib["appName"] == appType:
                if attrib["backupSetName"] == backupsetName:
                    if attrib["instanceName"] == instanceName:
                        return True
            
        return False
    
    def discoverVM(self, clientId,  path = None):
        cmd = 'VMBrowse?PseudoClientId=<<clientId>>&inventoryPath=%5CNONE%3AVMs'
        cmd = cmd.replace("<<clientId>>", clientId)
        if path != None:
            param = '%5Cdatacenter%3A<<path>>'
            param = param.replace("<<path>>", path)
            cmd = cmd + param
        else:
            del self.vmList[:]
            
        resp = self.getCmd(cmd)
        #print(self.sendText)
        #print(self.receiveText)
        if resp == None:
            return False
        activePhysicalNode = resp.findall(".//inventoryInfo")
        for node in activePhysicalNode:
            attrib = node.attrib
            #print(attrib)
            if attrib["type"] == '4':
                self.discoverVM(clientId, attrib["name"])
            if attrib["type"] == '9':
                self.vmList.append(attrib)
        return True
       
    def discoverVCInfo(self, clientId):
        #VSBrowse/4787/INVENTORY?requestType=INVENTORY
        del self.vmDCName[:]
        del self.vmESXHost[:]
        del self.vmDataStore[:]
        
        cmd = 'VSBrowse/<<clientId>>/INVENTORY?requestType=INVENTORY'
        cmd = cmd.replace("<<clientId>>", clientId)

        resp = self.getCmd(cmd)
        if resp == None:
            return False
        activePhysicalNode = resp.findall("inventoryInfo")
        for node in activePhysicalNode:
            attribDC = node.attrib
            #print(attribDC)
            if attribDC["type"] == '4':
                self.vmDCName.append(attribDC)
            hostnodes = node.findall(".//inventoryInfo")
            for hostnode in hostnodes:
                attribHost = hostnode.attrib
                #print(attribHost)
                if attribHost["type"] == '1':
                    attribHost["dcname"] = attribDC["name"]
                    attribHost["dcstrGUID"] = attribDC["strGUID"]
                    self.vmESXHost.append(attribHost)
                    
                    datastoreCmd = 'VSBrowse/<<clientId>>/<<esxHost>>?requestType=DATASTORES_ON_HOST'
                    datastoreCmd = datastoreCmd.replace("<<clientId>>", clientId)
                    datastoreCmd = datastoreCmd.replace("<<esxHost>>", attribHost["name"])
                    dsResp = self.getCmd(datastoreCmd)
                    datastoreList = dsResp.findall(".//dataStore")
                    for dsnode in datastoreList:
                        attribDatastore = dsnode.attrib
                        #print(attribDatastore)
                        attribDatastore["esxhost"] = attribHost["name"]
                        attribDatastore["esxstrGUID"] = attribHost["strGUID"]
                        self.vmDataStore.append(attribDatastore)
        return True

class CV_Client(CV_GetAllInformation):
    """
    Class documentation goes here.
    sub Class from CV_RestApi
    this Class for Client Operator
    
    attrib
        osinfo 
        platform {"WINX64", ""}
        agentType = {"clientId", "apptype"}
        subclientList = {'backupsetName', 'clientName', 'instanceName', 'appName', 'backupSetID', 'clientId', 'subclientId', 'subclientName', 'backupsetName', 'instanceName'}
    member 
        getClientAgentType(client) return agentType
        getClient return client node 
        getClientId return clientId 
        getSubClientList(client) return subclientList
        
        postClientPorertiesCmd()
    """
    appList = ("Exchange Database", "File System", "MySQL", "Oracle", "Oracle RAC", "SQL Server", "Virtual Server", "Sybase Database", "PostgreSQL")

    def __init__(self, token, client):
        """
        Constructor
        """
        super(CV_Client, self).__init__(token)
        self.client = client
        self.isFindClient = False
        
        self.agentType = []
        self.osinfo = ""
        self.platform = ""
        self.clientId = None
        self.clientName = None
        self.hostName = None
        self.backupsetList = []
        self.subClientList = []
        self.getClientInfo(client)

    def _getClient(self, client):
        node = {}
        if isinstance(client, (int)):
            command = "Client/<<client>>"
            command = command.replace("<<client>>", str(client))
            resp = self.getCmd(command)
            if resp == None:
                return None
            clientInfo = resp.findall(".//clientEntity")
            if clientInfo == [] or clientInfo == None:
                return None
            node["clientId"] = clientInfo[0].attrib["clientId"]
            node["clientName"] = clientInfo[0].attrib["clientName"]
            node["_type_"] =  ""
        else:
            command = "GetId?clientName=<<client>>"
            command = command.replace("<<client>>", client)
            resp = self.getCmd(command)
            if resp == None:
                return None
            node["clientId"] = resp.attrib["clientId"]
            node["clientName"] = resp.attrib["clientName"]
            node["_type_"] =  resp.attrib["_type_"]
        
        return node
    
    def checkClient(self, client):
        self.getClientList()
        for node in self.clientList:
            if node["clientName"].lower() == client.lower():
                return node
            if node["clientId"] == client:
                return node
        self.msg = "did not find this client: " + client
        return None
    
    def getBackupSetList(self):
        self.getSubClientList()
        flag = 0
        del self.backupsetList[:]
        bs = {"clientId":None, "applicationId":None, "appName":None, "backupsetId":None, "backupsetName":None, "instanceName":None, "instanceId":None}
        for node in self.subClientList:
            flag = 0
            for item in self.backupsetList:
                if node["backupsetId"] == item["backupsetId"]:
                    flag = 1
                    break
            if flag == 1:
                continue
            backupset = copy.deepcopy(bs)
            backupset["clientId"] = node["clientId"]
            backupset["applicationId"] = node["applicationId"]
            backupset["appName"] = node["appName"]
            backupset["backupsetId"] = node["backupsetId"]
            backupset["backupsetName"] = node["backupsetName"]
            backupset["instanceName"] = node["instanceName"]
            backupset["instanceId"] = node["instanceId"]
            self.backupsetList.append(backupset)
    
    def getClientAgentType(self):
        del self.agentType[:]
        if self.clientId == None:
            return None
        command = "Agent?clientId=<<clientId>>"
        command = command.replace("<<clientId>>", self.clientId)
        resp = self.getCmd(command)
        
        try:
            activePhysicalNode = resp.findall(".//idaEntity")
            for node in activePhysicalNode:
                self.agentType.append(node.attrib)
        except:
            self.msg = "error get agent type"
        
    def getClientOSInfo(self):
        if self.clientId == None:
            return None
        command = "Client/<<clientId>>"
        command = command.replace("<<clientId>>", self.clientId)
        resp = self.getCmd(command)
        
        try:
            osinfo = resp.findall(".//OsDisplayInfo")
            self.osinfo = osinfo[0].attrib["OSName"]
            self.platform = osinfo[0].attrib["ProcessorType"]
        
            hostnames = resp.findall(".//clientEntity")
            self.hostName = hostnames[0].attrib["hostName"]
        except:
            self.msg = "error get client info"
        
    def getClientInfo(self, client = None):
        self.isFindClient = False
        self.clientId = None
        self.clientName = None
        self.hostName = None
        if self.token.isLogin == False:
            return False
        if client != None:
            self.client = client
        else:
            return False
        '''    
        if isinstance(client, (int)):
            node = self._getClient(client)
        else:    
            node = self.checkClient(client)
        '''
        node = self._getClient(client)
        #print(node)
        if node == None:
            return False
        self.isFindClient = True
        self.clientId = node["clientId"]
        self.clientName = node["clientName"]
        self.getClientAgentType()
        self.getClientOSInfo()
        #self.getSubClientList()
        self.getBackupSetList()
        #self.getAllSPList()
        #self.getAllSchduleList()
        return True        
        
    def getSubClientList(self):
        subList = self.subClientList
        del subList[:]
        if self.clientId == None:
            return None
        cmd = 'Subclient?clientId=<<clientId>>';
        cmd = cmd.replace("<<clientId>>", self.clientId)
        
        subclient = self.getCmd(cmd)
        if subclient == None:
            return None
        activePhysicalNode = subclient.findall(".//subClientEntity")
        for node in activePhysicalNode:
            self.subClientList.append(node.attrib)
            
        return self.subClientList
        
    def checkVSAClient(self, vsaClient):
        cmd = 'Client/VMPseudoClient'
        clientList = self.getCmd(cmd)
        activePhysicalNode = clientList.findall(".//client")
        for node in activePhysicalNode:
            if node.attrib["clientName"] == vsaClient:
                return True
        return False
    
    def _vsaProxy(self, parent, proxylist):
        flag = 0
        for proxy in proxylist:            
            flag = 1
            a = ET.SubElement(parent, 'memberServers')
            b = ET.SubElement(a, 'client')
            c = ET.SubElement(b, 'clientName')
            c.text = proxy
        if flag == 0:
            a = ET.SubElement(parent, 'memberServers')
            b = ET.SubElement(a, 'client')
            c = ET.SubElement(b, 'clientName')
            c.text = ""
        return
    
    def addVSAClient(self, vsaClientInfo):
        try:
            vsaInstanceType = vsaClientInfo["vsType"]
            vsaClientName = vsaClientInfo["vsClientName"]
            vsaHost = vsaClientInfo["vsHost"]
            vsaProxyList = vsaClientInfo["vsProxy"]            
            vsaUserName = vsaClientInfo["userName"]
            vsaPasswd = vsaClientInfo["passwd"]
        except:
            self.msg = "vsa client info is wrong"
            return False
            
        self.client = vsaClientName
        if self.checkVSAClient(vsaClientName):
            self.msg = "there is same VM Client"
            return False

        input = os.getcwd()+"/template/vmcreate.xml"
        output = os.getcwd()+"/script/vmcreate-" + vsaClientInfo["vsClientName"]+".xml"

        try: 
            tree = ET.parse(input)
            root = tree.getroot()
        except: 
            self.msg =  "Error:parse file: " +input
            return False
        
        try:
            path = root.findall(".//associatedClients")
            path[0].clear()
            self._vsaProxy(path[0], vsaProxyList)
        except:
            self.msg = "Error: it is not VSA xml file" + input 
            return False 
        
        try: 
            tree.write(output)
        except : 
            self.msg =  "Error:write file: " +  output
            return False 
        
        cmd = "qoperation execute -af " + output
        param = " -vcenterHostName <<hostName>> -userName <<userName>> -password <<passwd>> -entity/clientName <<clientName>> "
        param = param.replace("<<clientName>>", vsaClientName)
        param = param.replace("<<hostName>>", vsaHost)
        param = param.replace("<<userName>>", vsaUserName)
        param = param.replace("<<passwd>>", vsaPasswd)
        
        self.qCmd(cmd, param)
        try:
            root = ET.fromstring(self.receiveText)
        except:
            self.msg = "unknown error: " + self.receiveText
            return False
            
        nodes = root.findall(".//errorCode")
        for node in nodes:
            if node.text == '0':
                self.msg = "add VSA Client success"
            else:
                errnodes = root.findall(".//errorString")
                for errnode in errnodes:
                    self.msg = errnode.text
                    return False
                self.msg = "unknown error:" + self.receiveText
                return False
        return True
        
    def delVSAClient(self, vsaClient):
        cmd = 'qdelete client -c <<client>> -a Q_VIRTUAL_SERVER -deconfigure - y'
        cmd = cmd.replace("<<client>>", vsaClient)
        
        self.qCmd(cmd, " ")
        try:
            root = ET.fromstring(self.receiveText)
        except:
            self.msg = "unknown error: " + self.receiveText
            return False
            
        nodes = root.findall(".//errorCode")
        for node in nodes:
            if node.text == '0':
                self.msg = "add VSA Client success"
            else:
                errnodes = root.findall(".//errorString")
                for errnode in errnodes:
                    self.msg = errnode.text
                    return False
                self.msg = "unknown error: " + self.receiveText
                return False
        return True

    def addRACClient(self, racClientInfo):
        self.getClientList()
        clientList = self.clientList
        for node in clientList:
            if node["clientName"] == racClientInfo["racClient"]:
                self.msg = "there is same rac client " + node["clientName"]
                return False
            
        #cmd = "qoperation execute -af "  qoperation execute -af racCreat.xml -clientInfo/clientType 'RAC' -entity/clientName "ractest"
        #param = " raccreate.xml -client/clientName <<ProxyclientName>> -vcenterHostName <<hostName>> -userName <<userName>> -password <<passwd>> -entity/clientName <<clientName>> "
        racClientName = racClientInfo["racClient"]
        racDB = racClientInfo["racDB"]
        
        self.qCmd(cmd, param)
        try:
            root = ET.fromstring(self.receiveText)
        except:
            self.msg = "unknown error: " + self.receiveText
            return False
            
        nodes = root.findall(".//errorCode")
        for node in nodes:
            if node.text == '0':
                self.msg = "add RAC Client success"
            else:
                errnodes = root.findall(".//errorString")
                for errnode in errnodes:
                    self.msg = errnode.text
                    return False
                self.msg = "unknown error: " + self.receiveText
                return False

        return True
        
    def postClientPorertiesCmd(self, cmd, updateClientProps = ""):
        resp = self.postCmd(cmd, updateClientProps)
        if resp == None:
            return False
        respRoot = ET.fromstring(resp)
        respEle = respRoot.findall(".//response")
        errorCode = ""        
        for node in respEle:
            errorCode = node.attrib["errorCode"]
        if errorCode == "0":
            # self.msg = "Properties set successfully"
            return True
        else:
            self.msg = "command " + cmd + " xml format" + updateClientProps + " Error Code: " + errorCode + " receive text is " + self.receiveText
            return False    

class CV_Backupset(CV_Client):
    """
    Class documentation goes here.
    sub Class from CV_RestApi
    this Class for Client Operator
    
    attrib
        appList = ("Exchange Database", "File System", "MySQL", "Oracle", "Oracle RAC", "SQL Server", "Virtual Server", "Sybase Database", "PostgreSQL")
        subclientList = {'backupsetName', 'clientName', 'instanceName', 'appName', 'backupSetID', 'clientId', 'subclientId', 'subclientName', 'backupsetName', 'instanceName'}
    member 
        getClientAgentType(client) return agentType
        getClient return client node 
        getClientId return clientId 
        getSubClientList(client) return subclientList
        
        postClientPorertiesCmd()
    """
    def __init__(self, token, client, agentType, backupsetName = None):
        """
        Constructor
        """
        super(CV_Backupset, self).__init__(token, client)
        self.curBackupSet = None
        self.agentType = agentType
        self.content = None
        self.credit = None
        self.getBackupSet(agentType, backupsetName)
        
        self.schduleList = []

        
    def getBackupSet(self, agentType, backupsetName = None):
        self.curBackupSet = None
        for node in self.backupsetList:
            if node["appName"]  == agentType:
                if backupsetName == None:
                    self.curBackupSet = node
                    return True                        
                if node["backupsetName"] == backupsetName:
                    self.curBackupSet = node
                    return True
        return False

    def _createOracleInstance(self, credit = None):
        if credit == None:
            self.msg = "create oracle instance info is None"
            return False
        input = "template/oraCreate.xml"
        output = "script/oraCreat-" + credit["Server"] + ".xml"
        
        OHOME = credit["ORACLE-HOME"]
        SP = credit["SPName"]
        try:
            tree = ET.parse(input)
            root = tree.getroot()
            homenodes = root.findall(".//oracleHome")
            for node in homenodes:
                node.text = OHOME
                break
            spnodes = root.findall(".//storagePolicyName")
            for node in spnodes:
                node.text = SP
        except:
            self.msg = "the file format is wrong: " + input
            return False
        
        try:
            tree.write(output)
        except:
            self.msg = "error write config file: " + output
            return False
        
        cmd = "qoperation execute -af " + output
        if "Win" in self.platform:
            param = " -ClientName <<clientName>> -instanceName <<instanceName>> -oracleUser/domainName <<Server>> -oracleUser/password <<passwd>> -oracleUser/userName <<userName>> "
        else:
            param = " -ClientName <<clientName>> -instanceName <<instanceName>> -oracleUser/userName <<userName>> "
        param = param.replace("<<clientName>>", self.clientName)
        param = param.replace("<<instanceName>>", credit["instanceName"])
        param = param.replace("<<Server>>", credit["Server"])
        param = param.replace("<<userName>>", credit["userName"])
        param = param.replace("<<passwd>>", credit["passwd"])

        self.qCmd(cmd, param)
        try:
            root = ET.fromstring(self.receiveText)
        except:
            self.msg = "unknown error: " + self.receiveText
            return False
            
        nodes = root.findall(".//errorCode")
        for node in nodes:
            if node.text == '0':
                self.msg = "add oracle instance success"
            else:
                errnodes = root.findall(".//errorString")
                for errnode in errnodes:
                    self.msg = errnode.text
                    return False
                self.msg = "unknown error: " + self.receiveText
                return False

        return True

    def _createMSSQLInstance(self, credit):
        if credit == None:
            self.msg = "create mssql instance info is None"
            return False
        input = "template/sqlCreate.xml"
        output = "script/sqlCreat-" + credit["instanceName"] + ".xml"
        
        instanceName = credit["instanceName"]
        SPName = credit["SPName"]
        useVss = credit["useVss"]
        try:
            tree = ET.parse(input)
            root = tree.getroot()
            clientnodes = root.findall(".//instance/clientName")
            for node in clientnodes:
                node.text = self.clientName
                break
            instancenodes = root.findall(".//instance/instanceName")
            for node in instancenodes:
                node.text = instanceName
                break
            spnodes = root.findall(".//storagePolicyName")
            for node in spnodes:
                node.text = SPName
            vssnodes = root.findall(".//useVss")
            for node in vssnodes:
                node.text = useVss
                
        except:
            self.msg = "the file format is wrong: " + input
            return False
        
        try:
            tree.write(output)
        except:
            self.msg = "error write config file: " + output
            return False
        
        cmd = "qoperation execute -af " + output
        self.qCmd(cmd, "")
        print(self.receiveText)
        try:
            root = ET.fromstring(self.receiveText)
        except:
            self.msg = "unknown error: " + self.receiveText
            return False
            
        nodes = root.findall(".//errorCode")
        for node in nodes:
            if node.text == '0':
                self.msg = "add MS SQL instance success"
            else:
                errnodes = root.findall(".//errorString")
                for errnode in errnodes:
                    self.msg = errnode.text
                    return False
                self.msg = "unknown error: " + self.receiveText
                return False

        return True

    def _createInstance(self, credit):
        if self.curBackupSet != None:
            self.msg = "there is have an instance"
            return False

        if credit["appName"] == "Oracle Database":
            return self._createOracleInstance(credit)
            
        if credit["appName"] == "MS SQL":
            return self._createMSSQLInstance(credit)
    
    def _modifyOracleInstance(self, credit = None):
        if credit == None:
            return True
        input = "template/oraModify.xml"
        output = "script/oraModi-" + credit["Server"] + ".xml"
        
        OHOME = credit["ORACLE-HOME"]
        SP = credit["SPName"]
        try:
            tree = ET.parse(input)
            root = tree.getroot()
            homenodes = root.findall(".//oracleHome")
            for node in homenodes:
                node.text = OHOME
                break
            spnodes = root.findall(".//storagePolicyName")
            for node in spnodes:
                node.text = SP
        except:
            self.msg = "the file format is wrong: " + input
            return False
        
        try:
            tree.write(output)
        except:
            self.msg = "error write config file: " + output
            return False
        
        cmd = "qoperation execute -af " + output
        if "Win" in self.platform:
            param = " -ClientName <<clientName>> -instanceName <<instanceName>> -oracleUser/domainName <<Server>> -oracleUser/password <<passwd>> -oracleUser/userName <<userName>> "
        else:
            param = " -ClientName <<clientName>> -instanceName <<instanceName>> -oracleUser/userName <<userName>> "
        
        param = param.replace("<<clientName>>", self.clientName)
        param = param.replace("<<instanceName>>", credit["instanceName"])
        param = param.replace("<<Server>>", credit["Server"])
        param = param.replace("<<userName>>", credit["userName"])
        param = param.replace("<<passwd>>", credit["passwd"])

        self.qCmd(cmd, param)
        #print(self.receiveText)
        try:
            root = ET.fromstring(self.receiveText)
        except:
            self.msg = "unknown error" + self.receiveText
            return False
            
        nodes = root.findall(".//errorCode")
        for node in nodes:
            if node.text == '0':
                self.msg = "modify oracle instance success"
            else:
                errnodes = root.findall(".//errorString")
                for errnode in errnodes:
                    self.msg = errnode.text
                    return False
                self.msg = "unknown error:" + self.receiveText
                return False

        return True

    def _modifyInstance(self, credit):
        if self.curBackupSet == None:
            self.msg = "there is not the instance"
            return False
    
        if credit["appName"] == "Oracle Database":
            return self._modifyOracleInstance(credit)
        
    def _setSPBySubId(self, subclientId, spname = None):
        if spname == None:
            return True
        cmd = 'Subclient/<<subclientId>>';
        cmd = cmd.replace("<<subclientId>>", subclientId)
        updateClientProps = """<App_UpdateSubClientPropertiesRequest><subClientProperties><contentOperationType>OVERWRITE</contentOperationType>
                            <commonProperties>
                                <storageDevice>
                                    <dataBackupStoragePolicy>
                                        <storagePolicyName><<spname>></storagePolicyName>
                                    </dataBackupStoragePolicy>
                                </storageDevice>
                            </commonProperties>
                        </subClientProperties>
                    </App_UpdateSubClientPropertiesRequest> 
                    """
        updateClientProps = updateClientProps.replace("<<spname>>", spname)
        
        return self.postClientPorertiesCmd(cmd, updateClientProps)

    def _getSchduleBySubId(self, subclientId):
        del self.schduleList[:]
        
        cmd = "Schedules?subclientId=<<subclientId>>"
        cmd = cmd.replace("<<subclientId>>", subclientId)
        client = self.getCmd(cmd)
        if client == None:
            return None
        try:
            activePhysicalNode = client.findall(".//task")
            for node in activePhysicalNode:
                self.schduleList.append(node.attrib)
                
        except:
            self.msg = "did not get Task"
            
        return self.schduleList

    def _setSchdulist(self, subclientId, subclientName, schduleName = None):
        if "command line" in subclientName:
            return True
        if schduleName == None:
            return True
        curBackupSet = self.curBackupSet
        delCmd = 'qmodify schedulepolicy -o remove -scp \'<<oldschdule>>\' '
        addCmd = 'qmodify schedulepolicy -o add -scp \'<<newschdule>>\' '        
        qcommand  = ""
        
        if curBackupSet["appName"] == "Oracle Database":
            qcommand = ' -c <<clientName>> -a Q_ORACLE -i <<instanceName>> -s <<subclientName>> '
        if curBackupSet["appName"] == "Windows File System":
            qcommand = ' -c <<clientName>> -a Q_FILESYSTEM -b <<backupsetName>> -s <<subclientName>> '
        if curBackupSet["appName"] == "SQL Server":
            qcommand = ' -c <<clientName>> -a Q_MSSQL -i <<instanceName>> -s <<subclientName>> '
        if curBackupSet["appName"] == "Virtual Server":
            qcommand = ' -c <<clientName>> -a Q_VIRTUAL_SERVER -i <<instanceName>> -b <<backupsetName>> -s <<subclientName>> '
            
        
        if qcommand == "":
            self.msg = "did not support this agent type " + curBackupSet["appName"]
            return False
            
        qcommand = qcommand.replace("<<clientName>>", self.clientName)
        qcommand = qcommand.replace("<<instanceName>>", self.curBackupSet["instanceName"])
        qcommand = qcommand.replace("<<backupsetName>>", self.curBackupSet["backupsetName"])
        qcommand = qcommand.replace("<<subclientName>>", subclientName)
        
        oldList = self._getSchduleBySubId(subclientId)
        #print("111", time.asctime())
        for node in oldList:
            delCmd = delCmd.replace("<<oldschdule>>", node["taskName"])
            command = delCmd + qcommand
            retCode = self.qCmd(command, "")
        #print("222", time.asctime())
        
        addCmd = addCmd.replace("<<newschdule>>", schduleName)
        command = addCmd + qcommand
        retCode = self.qCmd(command, "")
        #print("333", time.asctime())
        #print("ret:  ", retCode)
        #print("msg", self.receiveText)
        return retCode
        
    def _setDataBaseBackup(self, credit, content):
        #print ("DB Setup: ", time.asctime())
        if credit != None:
            if self._modifyInstance(credit) == False:
                self.msg += " modi instance error "
                return False

        #print ("step modi instance finish: ", time.asctime())
        for node in self.subClientList:
            if node["backupsetId"] == self.curBackupSet["backupsetId"]:
                #print ("step schdule: ", time.asctime() + " - " + node["subclientName"])
                if content["Schdule"] != None:
                    retCode = self._setSchdulist(node["subclientId"], node["subclientName"], content["Schdule"])
                    if retCode == False:
                        self.msg += " update schdule error " + node["subclientName"] + " " + content["Schdule"]
                        return False
                    else:
                        self.msg += " update schdule success "
                        
                if content["SPName"] != None:
                    retCode = self._setSPBySubId(node["subclientId"], content["SPName"])
                    if retCode == False:
                        self.msg += " update storagePolice error "
                        return False
                    else:
                        self.msg += " update storagePolice success "
                
        #print ("DB setup finish: ", time.asctime())
        return True

    def _setFSSystemState(self, subclientId, systemstates = None):
        if systemstates == None:
            return True
        cmd = 'Subclient/<<subclientId>>';
        cmd = cmd.replace("<<subclientId>>", subclientId)
        if systemstates == True:
            if "Win" in self.platform:
                updateClientProps = '''<App_UpdateSubClientPropertiesRequest><subClientProperties><contentOperationType>OVERWRITE</contentOperationType>
                                    <fsSubClientProp>
                                        <useVSS>true</useVSS>
                                        <useVSSForSystemState>True</useVSSForSystemState>
                                        <backupSystemState>True</backupSystemState>
                                        <useVssForAllFilesOptions>FAIL_THE_JOB</useVssForAllFilesOptions>
                                        <vssOptions>USE_VSS_FOR_ALL_FILES</vssOptions>
                                    </fsSubClientProp></subClientProperties></App_UpdateSubClientPropertiesRequest>'''
            else:
                updateClientProps = '''<App_UpdateSubClientPropertiesRequest><subClientProperties><fsSubClientProp>
                        <oneTouchSubclient>True</oneTouchSubclient>
                        </fsSubClientProp></subClientProperties></App_UpdateSubClientPropertiesRequest>'''
        else:
            if "Win" in self.platform:
                updateClientProps = '''<App_UpdateSubClientPropertiesRequest><subClientProperties><fsSubClientProp>
                                    <useVSS>true</useVSS>
                                    <backupSystemState>False</backupSystemState>
                                    <useVssForAllFilesOptions>CONTINUE_AND_DO_NOT_RESET_ACCESS_TIME</useVssForAllFilesOptions>
                                    <vssOptions>FOR_LOCKED_FILES_ONLY</vssOptions>
                                    </fsSubClientProp></subClientProperties></App_UpdateSubClientPropertiesRequest>'''
            else:
                updateClientProps = '''<App_UpdateSubClientPropertiesRequest><subClientProperties><fsSubClientProp>
                                    <oneTouchSubclient>False</oneTouchSubclient>
                                    </fsSubClientProp></subClientProperties></App_UpdateSubClientPropertiesRequest>'''
            
        return self.postClientPorertiesCmd(cmd, updateClientProps)
    
    def _setFSPaths(self, subclientId, paths = None):
        if paths == None:
            return True
        cmd = 'Subclient/<<subclientId>>';
        cmd = cmd.replace("<<subclientId>>", subclientId)
        firstRec = True
        for path in paths:
            if firstRec == True:
                updateClientProps = '''<App_UpdateSubClientPropertiesRequest><subClientProperties><contentOperationType>OVERWRITE</contentOperationType>
                            <content><path><<path>></path></content>
                            </subClientProperties></App_UpdateSubClientPropertiesRequest>'''
                updateClientProps = updateClientProps.replace("<<path>>", path)
                firstRec = False
                retCode = self.postClientPorertiesCmd(cmd, updateClientProps)
                if retCode == False:
                    return False
            else:
                updateClientProps = '''<App_UpdateSubClientPropertiesRequest><subClientProperties><contentOperationType>ADD</contentOperationType>
                            <content><path><<path>></path></content>
                            </subClientProperties></App_UpdateSubClientPropertiesRequest>'''
                updateClientProps = updateClientProps.replace("<<path>>", path)
                retCode = self.postClientPorertiesCmd(cmd, updateClientProps)
                if retCode == False:
                    return False
        return True
    
    def _setFSBackup(self, content):
        for node in self.subClientList:
            if node["backupsetId"] == self.curBackupSet["backupsetId"]:
                '''
                retCode = self._setSchdulist(node["subclientId"], node["subclientName"], content["Schdule"])
                if retCode == False:
                    return False
                '''
                retCode = self._setSPBySubId(node["subclientId"], content["SPName"])
                if retCode == False:
                    self.msg = "关联存储策略出错：" + self.msg
                    return False
                retCode = self._setFSSystemState(node["subclientId"], content["System States"])
                if retCode == False:
                    self.msg = "修改备份操作系统状态出错：" + self.msg
                    return False
                retCode = self._setFSPaths(node["subclientId"], content["Paths"])
                if retCode == False:
                    self.msg = "修改备份路径出错：" + self.msg
                    return False
                retCode = self._setSchdulist(node["subclientId"], node["subclientName"], content["Schdule"])
                if retCode == False:
                    self.msg = "修改计划策略出错：" + self.msg
                    return False

        return True
    
    
    def setBackup(self, credit, content):
        backupsetName = None
        if self.curBackupSet == None:
            if self._createInstance(credit) == False:
                return False
            self.getBackupSet(agentType, backupsetName)
        
        if self.curBackupSet == None:
            self.msg = "the backupset did not get" + self.curBackupSet["backupsetName"]
            return False
        curBackupset = self.curBackupSet
        backupsetName = self.curBackupSet["backupsetName"]
        
        if self.checkRunningJob(self.clientName, curBackupset["appName"], curBackupset["backupsetName"], curBackupset["instanceName"]) == True:
            self.msg = "there is a running job, did not configure"
            return False

        #print (time.asctime())
        if self.curBackupSet["appName"] == "Oracle Database":
            if self._setDataBaseBackup(credit, content) == False:
                self.msg = "set " + self.clientName + " Oracle backupset step error：" + self.msg
                return False
    
        if self.curBackupSet["appName"] == "Windows File System":
            if self._setFSBackup(content)  == False:
                self.msg = "set " + self.clientName + " WIN FS backupset step error：" + self.msg
                return False
                
        if self.curBackupSet["appName"] == "SQL Server":
            if self._setDataBaseBackup(credit, content)  == False:
                self.msg = "set " + self.clientName + " MS SQL backupset step error：" + self.msg
                return False

        self.msg = " client: " + self.clientName + " app: " + self.curBackupSet["appName"] + " set success "
        #print (time.asctime())
        return True

    def setVMBackup(self, content = None):
        if content == None:
            return True
        retCode = self.getBackupSet(self.agentType, content["backupsetName"])
        #print("step1 ", retCode, self.curBackupSet)
        if retCode == False:
            retCode = self._addVMBackupSet(content)
            if retCode == False:
                return False
        
        self.getBackupSetList()
        retCode = self.getBackupSet(self.agentType, content["backupsetName"])
        #print("step2", retCode, self.curBackupSet)
        if retCode == False:
            self.msg = "create success , but did not get this backupset :" + self.clientId + "  " + content["backupsetName"]
            return False

        flag = 0
        for node in self.subClientList:
            if node["backupsetId"] == self.curBackupSet["backupsetId"]:
                flag = 1
                break;
        
        if flag == 0:
            self.msg = "did not find subclient in this backupset:" + self.curBackupSet["backupsetName"]
            return False
        return self._modifyVMBackupset(node, content)

    def _setVMBackupContent(self, node, vmlist):
        #print(node)
        if node == None or vmlist == None:
            return True
        cmd = 'Subclient/<<subclientId>>';
        cmd = cmd.replace("<<subclientId>>", node["subclientId"])
        vmUpdateCmd = '''<App_UpdateSubClientPropertiesRequest><association><entity><appName>Virtual Server</appName>
                        <instanceName>VMware</instanceName><backupsetName><<backupsetName>></backupsetName><clientName><<clientName>></clientName><subclientName><<subclientName>></subclientName>
                        </entity></association>
                        <subClientProperties>
                        <vmContentOperationType>OVERWRITE</vmContentOperationType>
                        <vmContent>
                        <<vmcontent>>
                        </vmContent>
                        </subClientProperties>
                        </App_UpdateSubClientPropertiesRequest>'''
                        
        vmUpdateCmd = vmUpdateCmd.replace("<<subclientName>>", node["subclientName"])
        vmUpdateCmd = vmUpdateCmd.replace("<<clientName>>", node["clientName"])
        vmUpdateCmd = vmUpdateCmd.replace("<<backupsetName>>", node["backupsetName"])
        vmcontent = ""
        for vm in vmlist:
            if vm == None or vm =="":
                continue
            vmname = 'displayName="<<vm>>"'
            vmname = vmname.replace("<<vm>>", vm)
            vmcontent += '<children equalsOrNotEquals="1" name="" <<vmname>> type="VMName"/>'
            vmcontent = vmcontent.replace("<<vmname>>", vmname)
            
        if vmcontent == "":
            return True
        vmUpdateCmd = vmUpdateCmd.replace("<<vmcontent>>", vmcontent)        
        return self.postClientPorertiesCmd(cmd, vmUpdateCmd)
        
    def _modifyVMBackupset(self, subclientNode, content):
        curBackupset = self.curBackupSet
        if self.checkRunningJob(self.clientName, curBackupset["appName"], curBackupset["backupsetName"], curBackupset["instanceName"]) == True:
            self.msg = "there is a running job, did not configure"
            return False
        
        retCode = self._setSPBySubId(subclientNode["subclientId"], content["SPName"])
        if retCode == False:
            self.msg = "关联存储策略出错：" + self.msg
            return False
        retCode = self._setSchdulist(subclientNode["subclientId"], subclientNode["subclientName"], content["Schdule"])
        if retCode == False:
            self.msg = "修改计划策略出错：" + self.msg
            print(self.sendText)
            print(self.receiveText)
            return False
        retCode = self._setVMBackupContent(subclientNode, content["vmList"])
        if retCode == False:
            self.msg = "添加备份内容出错：" + self.msg
            return False
               
                
        return True
        
    def _addVMBackupSet(self, content = None):
        if content == None:
            return True
        vsaBackupsetInfo = content
        
        #vsaBackupsetInfo = {"vsType":"VMWARE", "vsClientName":"vsTest.hzx", "backupsetName":"app1", "vsProxy":proxylist, "vmList":vmList, "SPName":"SP-7DAY", "Schdule":None}
        command = 'qcreate backupset -c <<clientName>> -a Q_VIRTUAL_SERVER -i VMware -n <<backupsetName>>'
        command = command.replace("<<backupsetName>>", vsaBackupsetInfo["backupsetName"])
        command = command.replace("<<clientName>>", self.clientName)
        #print(command)
        retCode = self.qCmd(command)
        receive = str(self.receiveText)
        if "successfully" in receive:
            return True
        else:
            self.msg = "create vmware backupset error :" + receive
            return False
            
    def deleteVMBackupset(self):
        curBackupset = self.curBackupSet
        if curBackupset == None:
            self.msg = "did not find this backupset"
            return False

        if self.checkRunningJob(self.clientName, curBackupset["appName"], curBackupset["backupsetName"], curBackupset["instanceName"]) == True:
            self.msg = "there is a running job, did not delete"
            return False

        command = "Backupset/<<backupsetId>>"
        command = command.replace("<<backupsetId>>", curBackupset["backupsetId"])
        return self.delCmd(command)
        
        
        return True
    
class CV_Operator(CV_GetAllInformation):
    def __init__(self, token):
        """
        Constructor
        """
        super(CV_Operator, self).__init__(token)
        self.curBrowselist = []

        
    def backup(self):
        return
        
    def oraRestore(self, restoreOperator):
        input = "template/ora-Restore.xml"
        output = "script/oraRestore-" + restoreOperator["destClient"] + ".xml"
        
        sourceClient = restoreOperator["sourceClient"]
        destClient = restoreOperator["destClient"]
        instance = restoreOperator["instanceName"]
        restoreTime = restoreOperator["restoreTime"]
        try:
            tree = ET.parse(input)
            root = tree.getroot()
            sourceclients = root.findall(".//associations/clientName")
            for node in sourceclients:
                node.text = sourceClient
                break
            destclients = root.findall(".//destClient/clientName")
            for node in destclients:
                node.text = destClient
                break
            sourceclients = root.findall(".//backupset/clientName")
            for node in sourceclients:
                node.text = sourceClient
                break
            instanceNames = root.findall(".//associations/instanceName")
            for node in instanceNames:
                node.text = instance
                break
        except:
            self.msg = "the file format is wrong: " + input
            return False
        
        try:
            tree.write(output)
        except:
            self.msg = "error write config file: " + output
            return False
        
        cmd = "qoperation execute -af " + output + " -toTimeValue ' " + restoreTime + "' "
        param  = ""
        self.qCmd(cmd, param)
        try:
            root = ET.fromstring(self.receiveText)
        except:
            self.msg = "unknown error" + self.receiveText
            return False
            
        nodes = root.findall(".//jobIds")
        for node in nodes:
            self.msg = "jobid is: " + node.attrib["val"]
            return True
        self.msg = "unknown error:" + self.receiveText
        return False
        
    def appRestore(self, restoreOperator):
    
        return
        
    def browse(self, subclientNode, path = None, browse_file = False):
        #print(subclientNode)
        del self.curBrowselist[:]
        
        command = "Subclient/<<subclientId>>/Browse?"
        
        if subclientNode["appName"] == "Virtual Server":
            if path == None or path == "":
                if browse_file == True:
                    param = "path=%5C&showDeletedFiles=false&vsFileBrowse=true"
                else:
                    param = "path=%5C&showDeletedFiles=false&vsDiskBrowse=true"
            else:
                content =  urllib.quote(path.encode(encoding="utf-8")) 
                if browse_file == True:
                    param = "path=<<content>>&showDeletedFiles=false&vsFileBrowse=true"
                else:
                    param = "path=<<content>>&showDeletedFiles=false&vsDiskBrowse=true"
                param = param.replace("<<content>>", content)
                
        if "File System" in subclientNode["appName"] :
            if path == None or path == "":
                param = "path=%5C&showDeletedFiles=True"
            else:
                content =  urllib.quote(path.encode(encoding="utf-8")) 
                param = "path=<<content>>&showDeletedFiles=True"
                param = param.replace("<<content>>", content)
            
        command = command.replace("<<subclientId>>", subclientNode["subclientId"])
        resp = self.getCmd(command + param)
        nodelist = resp.findall(".//dataResultSet")
        for node in nodelist:
            flags = node.findall(".//flags")
            attrib = node.attrib
            if flags[0] != None:
                if "directory" in flags[0].attrib:
                    attrib["DorF"] = "D"
                else:
                    attrib["DorF"] = "F"
            else:
                attrib["DorF"] = "F"
            self.curBrowselist.append(attrib)
        #print(self.receiveText)
        return None
        
        
    def vmwareRestore(self, restoreOperator):
        input = "template/VMRestore.xml"
        output = "script/VMRestore-" + restoreOperator["sourceClient"] + "-" + restoreOperator["backupsetName"] + ".xml"
        tree = ET.parse(input)
        root = tree.getroot()
        cvSetXML = CV_VMRestore(root)

        backupsetname = restoreOperator["backupsetName"]
        clientName = restoreOperator["sourceClient"]
        proxyClient = restoreOperator["proxyClient"]
        vmName = restoreOperator["vmName"]
        vmGUID = restoreOperator["vmGUID"]
        destproxyclient = restoreOperator["destproxyclient"]
        newname = restoreOperator["newname"]
        esxhost = restoreOperator["esxhost"]
        dataStoreName = restoreOperator["dataStoreName"]
        vcenterIp = restoreOperator["vcenterIp"]
        vcenterUser = restoreOperator["vcenterUser"]
        diskOption = restoreOperator["diskOption"]
        power = restoreOperator["power"]
        overWrite = restoreOperator["overWrite"]
        destClient = restoreOperator["destClient"]


        cvBackupset = CV_Backupset(self.token, clientName, "Virtual Server", backupsetname)
        subclientnode = None
        for subclientnode in cvBackupset.subClientList:
            if subclientnode["backupsetId"] == cvBackupset.curBackupSet["backupsetId"]:
                break;
        if subclientnode == None:
            print("did not get this backupset: %s  %s" % (clientName, backupsetname))
            return

        retCode = cvSetXML.setVMAssociate(backupsetname, clientName)
        if retCode == False:
            self.msg = "the file format is wrong: " + input + " backupsetname"
            return False
        retCode = cvSetXML.setVMbrowseOption(backupsetname, proxyClient)
        if retCode == False:
            self.msg = "the file format is wrong: " + input + " proxyClient"
            return False

        cvOperator = CV_Operator(self.token)
        cvOperator.browse(subclientnode)

        cvOperator.browse(subclientnode, vmGUID)
        disklist = []
        for node in cvOperator.curBrowselist:
            if ".vmdk" in node["name"]:
                disklist.append(node)

        retCode = cvSetXML.setVMdestination(destproxyclient)
        if retCode == False:
            self.msg = "the file format is wrong: " + input + " destproxyclient"
            return False

        retCode = cvSetXML.setVMFileOption(vmGUID)
        if retCode == False:
            self.msg = "the file format is wrong: " + input + " vmGUID"
            return False
        retCode = cvSetXML.setVMadvancedRestoreOptions(dataStoreName, disklist, esxhost, vmGUID,
                                                       vmName, newname, None)
        if retCode == False:
            self.msg = "the file format is wrong: " + input + " setVMadvancedRestoreOptions"
            return False

        retCode = cvSetXML.setVMdiskLevelVMRestoreOption(vcenterIp, esxhost, vcenterUser, diskOption=diskOption,
                                                         overWrite=overWrite, power=power)
        if retCode == False:
            self.msg = "the file format is wrong: " + input + " setVMdiskLevelVMRestoreOption"
            return False

        retCode = cvSetXML.setVMvCenterInstance(destClient)
        if retCode == False:
            self.msg = "the file format is wrong: " + input + " destClient"
            return False

        try:
            tree.write(output)
        except:
            self.msg = "error write config file: " + output
            return False

        cmd = "qoperation execute -af " + output
        param = ""
        self.qCmd(cmd, param)
        try:
            root = ET.fromstring(self.receiveText)
        except:
            self.msg = "unknown error" + self.receiveText
            return False

        nodes = root.findall(".//jobIds")
        for node in nodes:
            self.msg = "jobid is: " + node.attrib["val"]
            return True
        self.msg = "unknown error:" + self.receiveText
        return False

    def sqlRestore(self, restoreOperator):
        input = "template/sql-Restore.xml"
        output = "script/sqlRestore-" + restoreOperator["destClient"] + ".xml"

        sourceClient = restoreOperator["sourceClient"]
        destClient = restoreOperator["destClient"]
        instance = restoreOperator["instanceName"]
        restoreTime = restoreOperator["restoreTime"]
        overWrite = restoreOperator["overWrite"]
        try:
            tree = ET.parse(input)
            root = tree.getroot()
            sourceclients = root.findall(".//associations/clientName")
            for node in sourceclients:
                node.text = sourceClient
                break
            destclients = root.findall(".//destClient/clientName")
            for node in destclients:
                node.text = destClient
                break
            sourceclients = root.findall(".//backupset/clientName")
            for node in sourceclients:
                node.text = sourceClient
                break
            instanceNames = root.findall(".//associations/instanceName")
            for node in instanceNames:
                node.text = instance
                break
            overWrites = root.findall(".//sqlServerRstOption/overWrite")
            for node in overWrites:
                if overWrite == True:
                    node.text = "True"
                else:
                    node.text = "False"
                break
        except:
            self.msg = "the file format is wrong: " + input
            return False

        try:
            tree.write(output)
        except:
            self.msg = "error write config file: " + output
            return False

        cmd = "qoperation execute -af " + output + " -toTimeValue ' " + restoreTime + "' "
        param = ""
        self.qCmd(cmd, param)
        try:
            root = ET.fromstring(self.receiveText)
        except:
            self.msg = "unknown error" + self.receiveText
            return False

        nodes = root.findall(".//jobIds")
        for node in nodes:
            self.msg = "jobid is: " + node.attrib["val"]
            return True
        self.msg = "unknown error:" + self.receiveText
        return False

    def fileRestore(self, restoreOperator):
        input = "template/file-Restore.xml"
        output = "script/fileRestore-" + restoreOperator["destClient"] + ".xml"

        sourceClient = restoreOperator["sourceClient"]
        destClient = restoreOperator["destClient"]
        instance = restoreOperator["instanceName"]
        restoreTime = restoreOperator["restoreTime"]
        overWrite = restoreOperator["overWrite"]
        inPlace = restoreOperator["inPlace"]
        destPath =  restoreOperator["destPath"]
        sourceItemlist = restoreOperator["sourceItemlist"]
        try:
            tree = ET.parse(input)
            root = tree.getroot()
            sourceclients = root.findall(".//associations/clientName")
            for node in sourceclients:
                node.text = sourceClient
                break
            destclients = root.findall(".//destClient/clientName")
            for node in destclients:
                node.text = destClient
                break
            sourceclients = root.findall(".//backupset/clientName")
            for node in sourceclients:
                node.text = sourceClient
                break
            overWrites = root.findall(".//commonOptions/unconditionalOverwrite")
            for node in overWrites:
                if overWrite == True:
                    node.text = "True"
                else:
                    node.text = "False"
                break
            inPlaces = root.findall(".//destination/inPlace")
            for node in inPlaces:
                if inPlace == True:
                    node.text = "True"
                else:
                    node.text = "False"
                break
            destPaths = root.findall(".//destination/destPath")
            for node in destPaths:
                node.text = destPath
                break

            parent = root.findall(".//fileOption")
            children = parent[0].getchildren()
            for child in children:
                if child.tag == "sourceItem":
                    parent[0].remove(child)

            for sourceItem in sourceItemlist:
                child = ET.Element('sourceItem')
                child.text = sourceItem
                parent[0].append(child)
            if len(sourceItemlist)==0:
                child = ET.Element('sourceItem')
                child.text = '\\'
                parent[0].append(child)
        except:
            self.msg = "the file format is wrong: " + input
            return False

        try:
            tree.write(output)
        except:
            self.msg = "error write config file: " + output
            return False

        cmd = "qoperation execute -af " + output + " -toTimeValue ' " + restoreTime + "' "
        param = ""
        self.qCmd(cmd, param)
        try:
            root = ET.fromstring(self.receiveText)
        except:
            self.msg = "unknown error" + self.receiveText
            return False

        nodes = root.findall(".//jobIds")
        for node in nodes:
            self.msg = "jobid is: " + node.attrib["val"]
            return True
        self.msg = "unknown error:" + self.receiveText
        return False
    
class CV_VMRestore(object):    
    def __init__(self, et):
        """
        Constructor
        """
        super(CV_VMRestore, self).__init__()
        self.root = et
    
    def setVMAssociate(self, backupsetname, clientname):
        ''' source virtual client '''
        et = self.root
        try:
            backupsetnames = et.findall(".//associations/backupsetName")
            backupsetnames[0].text = backupsetname
            clientnames = et.findall(".//associations/clientName")
            clientnames[0].text = clientname
        except:
            return False
        return True
    
    def setVMbrowseOption(self, backupsetname, clientname):
        ''' source proxy client '''
        et = self.root
        try:
            backupsetnames = et.findall(".//browseOption/backupset/backupsetName")
            backupsetnames[0].text = backupsetname
            clientnames = et.findall(".//browseOption/backupset/clientName")
            clientnames[0].text = clientname
        except:
            return False
        return True
    
    def setVMdestination(self, clientname):
        ''' dest proxy client setup '''
        et = self.root
        try:
            clientnames = et.findall(".//destination/destClient/clientName")
            clientnames[0].text = clientname
        except:
            return False
        return True 

    
    def setVMFileOption(self, sourceGUID):
        ''' set source guid '''
        et = self.root
        try:
            sourceGuids = et.findall(".//fileOption/sourceItem")
            sourceGuids[0].text = "\\" + sourceGUID
        except:
            return False
        return True 

    def setVMadvancedRestoreOptions(self, datastore, disklist, esxHost, guid, name, newname, nics):
        '''  set dest info '''
        et = self.root
        
        try:
            datastores = et.findall(".//advancedRestoreOptions/Datastore")
            datastores[0].text = datastore
            esxHosts = et.findall(".//advancedRestoreOptions/esxHost")
            esxHosts[0].text = esxHost
            guids = et.findall(".//advancedRestoreOptions/guid")
            guids[0].text = guid
            names = et.findall(".//advancedRestoreOptions/name")
            names[0].text = name
            newnames = et.findall(".//advancedRestoreOptions/newName")
            newnames[0].text = newname
        
            parent = et.findall(".//advancedRestoreOptions")
            children = parent[0].getchildren()
            for child in children:
                if child.tag == "disks":
                    parent[0].remove(child)
            
            for disk in disklist:
                child = ET.Element('disks')
                a = ET.SubElement(child, 'Datastore')
                b = ET.SubElement(child, 'name')
                a.text = datastore
                b.text = disk["name"]
                parent[0].append(child)
                
        except:
            return False
        return True 

    def setVMdiskLevelVMRestoreOption(self, esxServerName, hostOrCluster, userName="Administrator", diskOption = "Auto", overWrite = False, power = False ):
        et = self.root
        try:
            esxServerNames = et.findall(".//diskLevelVMRestoreOption/esxServerName")
            esxServerNames[0].text = esxServerName
            hostOrClusters = et.findall(".//diskLevelVMRestoreOption/hostOrCluster")
            hostOrClusters[0].text = hostOrCluster
            userNames = et.findall(".//diskLevelVMRestoreOption/userPassword/userName")
            userNames[0].text = userName
            diskOptions = et.findall(".//diskLevelVMRestoreOption/diskOption")
            diskOptions[0].text = diskOption
            overWrites = et.findall(".//diskLevelVMRestoreOption/passUnconditionalOverride")
            if overWrite == True:
                overWrites[0].text = "True"
            else:
                overWrites[0].text = "False"
            powers = et.findall(".//diskLevelVMRestoreOption/powerOnVmAfterRestore")
            if power == True:
                powers[0].text = "True"
            else:
                powers[0].text = "False"
        
        except:
            return False
        return True 

    def setVMvCenterInstance(self, clientName):
        et = self.root
        try:
            clientNames = et.findall(".//vCenterInstance/clientName")
            clientNames[0].text = clientName
        except:
            return False
        return True 
    
def vmRestore(cvToken, clientName, backupsetName):
    cvBackupset = CV_Backupset(cvToken, clientName, applist["Virtual Server"], backupsetName)
    subclientnode = None
    for subclientnode in cvBackupset.subClientList:
        if subclientnode["backupsetId"] == cvBackupset.curBackupSet["backupsetId"]:
            break;
    if subclientnode == None:
        print("did not get this backupset: %s  %s" % (clientName, backupsetName) )
        return
    print '*************'    
    print(subclientnode)
    
    input = "template/VMRestore.xml"
    output = "script/VMRestore-1.xml"'''
    tree = ET.parse(input)
    root = tree.getroot()
    cvSetXML = CV_VMRestore(root)
    
    backupsetname = subclientnode["backupsetName"]
    clientName = subclientnode["clientName"]
    retCode = cvSetXML.setVMAssociate(backupsetName, clientName)
    if retCode == False:
        return
    print("set associate %s  %s" % (backupsetname, clientName))
    
    print("select browse proxy Client:")

    input = sys.stdin.readline()
    input = input.strip()
    retCode = cvSetXML.setVMbrowseOption( backupsetname, input)
    if retCode == False:
        return
    print("set browserOption %s  %s" % (backupsetname, input))
    '''
    cvOperator = CV_Operator(cvToken)
    cvOperator.browse(subclientnode)
    i = 0
    print cvOperator.curBrowselist
    for node in cvOperator.curBrowselist:
        i += 1
        print("%-3dVM name: %-20s VM GUID: %20s" % (i, node["displayName"], node["name"]))    
    while True:
        print("select vm:")
        input = sys.stdin.readline()
        choice = int(input)
        if choice > i or choice <= 0:
            print("error select")
        else:
            break;
    selectedvm = cvOperator.curBrowselist[choice - 1]
    cvOperator.browse(subclientnode, selectedvm["name"])
    disklist = []
    print("vmdk list:")
    for node in cvOperator.curBrowselist:
        if ".vmdk" in node["name"]:
            print(selectedvm["displayName"], node["name"], node["size"])
            disklist.append(node)
    
    print("select destClient:")
    input = sys.stdin.readline()
    input = input.strip()
    #print("input %s is len is %d " % (input, len(input))
    
    retCode = cvSetXML.setVMdestination(input)
    if retCode == False:
        return
    print("set VMdestination: ", input)

    retCode = cvSetXML.setVMFileOption(selectedvm["name"])
    if retCode == False:
        return
    print("set VMFileOption: ", selectedvm["name"])

    cvBackupset.discoverVCInfo(cvBackupset.clientId)
    i = 0
    for node in cvBackupset.vmDataStore:
        i += 1
        print("%-3desx name:%-10s ds name:%-20s ds type:%8s" % (i, node["esxhost"], node["dataStoreName"], node["dataStoreType"]))
    while True:
        print("select dsname")
        input = sys.stdin.readline()
        choice = int(input)
        if choice > i or choice <=0:
            print("error select")
        else:
            node = cvBackupset.vmDataStore[choice-1]
            selectedesxname = node["esxhost"]
            selecteddsname = node["dataStoreName"]            
            break;
    
    print("select new vm name")
    newname = sys.stdin.readline()
    newname = newname.strip()
    retCode = cvSetXML.setVMadvancedRestoreOptions(selecteddsname, disklist, selectedesxname, selectedvm["name"], selectedvm["displayName"], newname, None)
    if retCode == False:
        return
    print("set advancedRestoreOptions:", selecteddsname, disklist, selectedesxname, selectedvm["name"], selectedvm["displayName"], newname)

    print("select vcenter ip")
    vcname = sys.stdin.readline()
    vcname = vcname.strip()
    
    print("select vcenter user")
    username = sys.stdin.readline()
    username = username.strip()
    
    retCode = cvSetXML.setVMdiskLevelVMRestoreOption(vcname, selectedesxname, username, diskOption = "Auto", overWrite = False, power = False)
    if retCode == False:
        return
    print("set setVMdiskLevelVMRestoreOption:", vcname, selectedesxname, "Administrator", "Auto", False, False)
    
    print("input dest vclient name")
    input = sys.stdin.readline()
    input = input.strip()
    
    retCode = cvSetXML.setVMvCenterInstance(input)
    if retCode == False:
        return
    print("set vCenterInstance", input)
    
    tree.write(output)
    print("xml output:", output)
    return

    
if __name__ == "__main__":
    print('it is main')
    info = {"webaddr":"192.168.100.17", "port":"81", "username":"cvadmin", "passwd":"1qaz@WSX", "token":"", "lastlogin":0}
    #info = {"webaddr":"172.16.110.55", "port":"81", "username":"cvadmin", "passwd":"1qaz@WSX", "token":"", "lastlogin":0}
    appList = ("Exchange Database", "File System", "MySQL", "Oracle", "Oracle RAC", "SQL Server", "Virtual Server", "Sybase Database", "PostgreSQL")
    applist = {"ORACLE":"Oracle Database", "WIN FS":"Windows File System", "MS SQL":"SQL Server", "Virtual Server":"Virtual Server"}
    client = "test2.hzx"
    
    proxylist = ["test3"]
    #proxylist = ["WIN-V11-MA2"]
    vmList = ["AD-192.168.101.1", "", ""]
    #vsaClientInfo = {"vsType":"VMWARE", "vsClientName":"vsTest.hzx", "vsHost":"192.168.101.2", "vsProxy":proxylist, "userName":"administrator", "passwd":"tesunet@2016"}
    #vsaCreditInfo = {"vsType":"VMWARE", "vsBackupSet":"backupset1", "vsProxy":proxylist, "VM List":vmList}
    vsaBackupsetInfo = {"vsType":"VMWARE",  "backupsetName":"app2", "vsProxy":proxylist, "vmList":vmList, "SPName":None, "Schdule":"VM_BRONZE"}
    cvToken = CV_RestApi_Token()    
    if cvToken.login(info) == None:
        print("did not login", cvToken.msg)
        exit
    else:
        print("login in")
    '''
    vsaRestoreBrowseInfo = {"vsClientName":"vsTest.hzx", "backupsetName":"app1", "vmGUID":"5023230b-388a-0452-c1be-461b991c976f" , "vmName":"ttt"}
    vmdkList = ["ide0-0-xp-192.168.102.100.vmdk", "scsi0-0-xp-192.168.102.100_1.vmdk"]
    setName = {"oldName":None, "newName":None}
    vsaRestoreDestInfo = {"vsProxy":"test1", "Vcenter":"192.168.101.2", "DCName":"ddd", "esxHost":"192.168.100.15", "datastore":"DATA-2-NoRaid", "vmdkLists":vmdkList, "newName":"abc", "diskOption":"Auto", "Power":"False", "overWrite":"False"}
    vsaRestoreInfo = {"vsType":"VMWARE", "vsClientName":"vsTest.hzx", "source": vsaRestoreBrowseInfo, "dest":vsaRestoreDestInfo}

    racList = ["rac1", "rac2"]
    racClientInfo = {"racClient":"testRAC", "racHost":"racHost", "racProxy":["test5"]}

    oraCreditInfo = {"appName":"Oracle Database", "instanceName":"ORCL", "userName":"administrator", "passwd":"tesunet@2016", "OCS":"/", "SPName":"SP-30DAY", "ORACLE-HOME":"E:/app/Administrator/product/11.2.0/dbhome_1", "Server":"test2"}
    oraBackupContent = {"SPName":"SP-7DAY", "Schdule":"DB BACKUP Silver Plan"}

    mssqlCreditInfo = {"appName":"MS SQL", "instanceName":"test2", "SPName":"SP-7DAYS", "useVss":"True"}
    mssqlBackupContent = {"SPName":"SP-7DAY", "Schdule":"DB BACKUP Golden Plan"}

    paths=["c:\\", "e:\\"]
    fsBackupContent = {"SPName":"SP-7DAY", "Schdule":"App File Backup Bronze Plan", "Paths":paths, "System States":False}
    
    sourceClient = "test2.hzx"
    destClient = "test3.hzx"
    restoreTime = "lastest Time"
    oraRestoreOperator = {"appName":"Oracle Database", "instanceName":"ORCL", "sourceClient":sourceClient, "destClient":destClient, "restoreTime":restoreTime, "restorePath":None}
    
    fileRestoreOperator = {"appName":"File System", "backupsetName":"default", "sourceClient":sourceClient, "destClient":destClient, "restoreTime":restoreTime, "Path":"\\", "overwrite":"True", "OS Restore":False}
    
    input = "vmcreate.xml"
    output = "test.xml"
    
    #xmlTest(input, output)
    
    cvToken = CV_RestApi_Token()    
    if cvToken.login(info) == None:
        print("did not login", cvToken.msg)
        exit
    else:
        print("login in")
    '''
    '''
    print (cvToken.msg)
    cvAllInfo = CV_GetAllInformation(cvToken)
    cvAllInfo.getAllSPList()
    cvAllInfo.getAllSchduleList()
    cvAllInfo.getClientList()
    for node in cvAllInfo.SPList:
        print (node)
    
    for node in cvAllInfo.SchduleList:
        print (node)
    for node in cvAllInfo.clientList:
        print (node)
    ''' 
    
    '''
    cvClient = CV_Client(cvToken, None)
    rc = cvClient.addVSAClient(vsaClientInfo)
    print(rc, cvClient.msg, cvClient.client)
    print(cvClient.getClientInfo(cvClient.client))
    for node in cvClient.backupsetList:
        print (node)
        print("\r\n")
    cvBackupset = CV_Backupset(cvToken, "vstest.hzx", applist["Virtual Server"])
    for node in cvBackupset.backupsetList:
        print (node)
    print(cvBackupset.curBackupSet)
    cvBackupset.discoverVM()
    print(cvBackupset.vmList)
    '''
    
    '''
    cvBackupset = CV_Backupset(cvToken, client, applist["WIN FS"])
    print(cvBackupset.osinfo, " == " , cvBackupset.platform)
    
    for node in cvBackupset.backupsetList:
        print(node)
    print(cvBackupset.curBackupSet)
    
    retCode = cvBackupset.setBackup(None, fsBackupContent)
    print(retCode, cvBackupset.msg)
    '''
    
    '''
    cvBackupset = CV_Backupset(cvToken, client, applist["MS SQL"])
    print(cvBackupset.osinfo, " == " , cvBackupset.platform)
    print(cvBackupset.backupsetList)
    print(cvBackupset.curBackupSet)
    retCode = cvBackupset.setBackup(mssqlCreditInfo, mssqlBackupContent)
    print(retCode, cvBackupset.msg)
    '''
    '''
    print ("start", time.asctime())
    cvBackupset = CV_Backupset(cvToken, 11, applist["ORACLE"])
    curBackupset = cvBackupset.curBackupSet
    print(curBackupset)
    print(cvBackupset.checkRunningJob(cvBackupset.clientName, curBackupset["appName"], curBackupset["backupsetName"], curBackupset["instanceName"]))
    '''
    '''
    cvBackupset = CV_Backupset(cvToken, 32, applist["Virtual Server"], "app1")
    print(cvBackupset.curBackupSet)
    #cvBackupset.discoverVM(cvBackupset.clientId)
    #for node in cvBackupset.vmList:
    #    print(node)
    #retCode = cvBackupset.setVMBackup(vsaBackupsetInfo)
    print(retCode, cvBackupset.msg)
    #clientId, type = "backup", appTypeName=None, backupsetName = None, subclientName = None, start = None, end = None
    #print(cvBackupset.getJobList(cvBackupset.clientId, type = "backup", appTypeName = None, backupsetName = cvBackupset.curBackupSet["backupsetName"], subclientName = None, start = None, end = None))
    #retCode = cvBackupset.deleteVMBackupset()
    #print(retCode, cvBackupset.msg)
    
    #cvBackupset.createInstance(oraCreditInfo)
    #print(cvBackupset.msg)
    #print("", time.asctime())
    #retCode = cvBackupset.setBackup(None, oraBackupContent)
    #print(retCode, cvBackupset.msg)
    #print ("end", time.asctime())
    '''
    
    
    #cvBackupset = CV_Backupset(cvToken, "VCENTER2", applist["Virtual Server"], "defaultBackupSet")
    vmRestore(cvToken, "vc.Paulwen", "app1")
    #vmRestore(cvToken, "VCENTER2", "defaultBackupSet")
    
    
    #cvBackupset = CV_Backupset(cvToken, 11, applist["WIN FS"])
    #print(cvBackupset.curBackupSet)
    '''
    for subclientnode in cvBackupset.subClientList:
        if subclientnode["backupsetId"] == cvBackupset.curBackupSet["backupsetId"]:
            break;
    print(subclientnode)
    
    cvBackupset.discoverVCInfo(cvBackupset.clientId)
    for node in cvBackupset.vmDataStore:
        print(node)
    cvBackupset.discoverVM(cvBackupset.clientId)
    for node in cvBackupset.vmList:
        print(node)
    '''
    '''
    cvBackupset.discoverVCInfo(cvBackupset.clientId)

    cvOperator = CV_Operator(cvToken)
    #cvOperator.browse(node, "\C:\\Users\\Administrator")
    #for node in cvOperator.curBrowselist:
    #    print(node)
    cvOperator.browse(subclientnode)
    for node in cvOperator.curBrowselist:
        print(node)
    
    
    #print("select DC Name:")
    #dcname = sys.stdin.readline()
    
    #print(input)
    #input = input("Enter your name:")
    #print ("your name is",input)
    '''
    
    '''
    cvOperator.browse(subclientnode, "\\501c3a50-c1bf-afd8-1b6f-c50cd2643cbf")
    for node in cvOperator.curBrowselist:
        print(node)
        
    retcode = cvOperator.vmwareRestore(vsaRestoreInfo)
    print(retcode, cvOperator.msg)
    '''
    #print(cvOperator.receiveText)
    #cvOperator.browse(node, "\\5023230b-388a-0452-c1be-461b991c976f\C")
    #print(cvOperator.curBrowselist)
    #print(cvOperator.receiveText)
    #cvOperator.oraRestore(oraRestoreOperator )
    
    
    