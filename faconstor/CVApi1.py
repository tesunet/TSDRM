# -*- coding: utf-8 -*-

import sys
import os
import requests
import time
import copy
import subprocess
import pymssql
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

#__platform__ = {"platform":None, "ProcessorType":0, "hostName":None}
#__clientInfo__ = {"clientName":None, "clientId":None, "platform":self.platform, "backupsetList":[], "agentList":[]}
        
    
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

    def getTokenString(self):
        return self.credit["token"]
    
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
        
        outlen = len(stdoutinfo)
        errlen = len(stderrinfo)
        if s.returncode == 0: 
            if outlen > 0: 
                self.receiveText = stdoutinfo
            else:
                self.receiveText = stderrinfo
            return True
        else:
            if errlen > 0: 
                self.receiveText = stderrinfo
            else:
                self.receiveText = stdoutinfo                
            return False
        return True

        
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
    getJobList return job list
    
    """
    def __init__(self, token):
        """
        Constructor
        """
        super(CV_GetAllInformation, self).__init__(token)
        
        self.SPList = []
        self.SchduleList = []
        self.clientList = []
        self.jobList = []
        self.vmClientList = []
        self.vmProxyList = []
        
        self.vmDCName = []
        self.vmESXHost = []
        self.vmDataStore = []
        self.vmList = []
        
    def getSPList(self):
        del self.SPList[:]
        client = self.getCmd('StoragePolicy')
        if client == None:
            return None
            
        activePhysicalNode = client.findall(".//policies")
        for node in activePhysicalNode:
            if node.attrib["storagePolicyId"] <= "2":
                continue
            if "System Create" in node.attrib["storagePolicyName"]:
                continue
            self.SPList.append(node.attrib)
        return self.SPList

    def getSchduleList(self):    
        del self.SchduleList[:]
        client = self.getCmd('SchedulePolicy')
        if client == None:
            return None
        activePhysicalNode = client.findall(".//taskDetail/task")
        for node in activePhysicalNode:
            if "System Created " in node.attrib["taskName"]:
                continue
            self.SchduleList.append(node.attrib)
        return self.SchduleList
    
    
    def getClientList(self):
        del self.clientList[:]
        clientRec = {"clientName":None, "clientId":-1}
        client = self.getCmd('/Client')
        if client == None:
            return None
            
        activePhysicalNode = client.findall(".//clientEntity")
        for node in activePhysicalNode:
            rec = copy.deepcopy(clientRec)
            rec["clientName"] = node.attrib["clientName"]
            try:
                rec["clientId"] = int(node.attrib["clientId"])
            except:
                pass
            self.clientList.append(rec)
        return self.clientList
    
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
        resp = self.getCmd(cmd)

           
        if resp == None:
            return None
        
        #print(resp)
        #print(self.receiveText)
        activePhysicalNode = resp.findall(".//jobs/jobSummary")
        for node in activePhysicalNode:
            #if start != None:
            #if end != None:
            #print(node.attrib)
            if appTypeName != None:
                if appTypeName not in node.attrib["appTypeName"]:
                    continue;
            if backupsetName != None:
                if  backupsetName not in node.attrib["backupSetName"]:
                    continue;
            if subclientName != None:
                if subclientName not in node.attrib["subclientName"]:
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
                if attrib["backupSetName"] == backupsetName or backupsetName == None:
                    if attrib["instanceName"] == instanceName or instanceName == None:
                        return True
            
        return False
    
    def getVMClientList(self):
        del self.vmClientList[:]
        command = "/Client/VMPseudoClient"

        client = self.getCmd(command)
        if client == None:
            return None
            
        activePhysicalNode = client.findall(".//client")
        for node in activePhysicalNode:
            self.vmClientList.append(node.attrib)
        return self.vmClientList
    
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
        if resp == None:
            return False
        activePhysicalNode = resp.findall(".//inventoryInfo")
        for node in activePhysicalNode:
            attrib = node.attrib
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
            return self.vmDataStore
        
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
        return self.vmDataStore

class CV_Client(CV_GetAllInformation):
    def __init__(self, token, client = None):
        """
        Constructor
        """
        super(CV_Client, self).__init__(token)
        self.client = client
        
        self.backupsetList = []
        self.subclientList = []
        self.platform = {"platform":None, "ProcessorType":0, "hostName":None}
        self.clientInfo = {"clientName":None, "clientId":None, "platform":self.platform, "backupsetList":[], "agentList":[]}
        #self.backupInfo = {"clientId":None, "clientName":None, "agentType":None, "agentId":None, "backupsetId":None, "backupsetName":None, "instanceName":None, "instanceId":None}

        self.isNewClient = True
        self.getClientInfo(client)
    
    def getClient(self, client):
        # get clientName and clientId
        clientInfo = self.clientInfo
        
        if isinstance(client, (int)):
            command = "Client/<<client>>"
            command = command.replace("<<client>>", str(client))
            resp = self.getCmd(command)
            if resp == None:
                return False
            clientEntity = resp.findall(".//clientEntity")
            if clientEntity == []:
                return False
            clientInfo["clientId"] = clientEntity[0].attrib["clientId"]
            clientInfo["clientName"] = clientEntity[0].attrib["clientName"]
        else:
            command = "GetId?clientName=<<client>>"
            command = command.replace("<<client>>", client)
            resp = self.getCmd(command)
            if resp == None:
                return False
            clientInfo["clientId"] = resp.attrib["clientId"]
            if int(clientInfo["clientId"]) <= 0:
                return False
            clientInfo["clientName"] = resp.attrib["clientName"]
        return True
    
    def getSubClientList(self, clientId):
        # subclientInfo {'subclientName','instanceName','backupsetName','appName','applicationId','clientName','instanceId','backupsetId','subclientId', 'clientId'}
        subList = self.subclientList
        del subList[:]
        if clientId == None:
            return None
        cmd = 'Subclient?clientId=<<clientId>>';
        cmd = cmd.replace("<<clientId>>", clientId)
        
        subclient = self.getCmd(cmd)
        if subclient == None:
            return None
        activePhysicalNode = subclient.findall(".//subClientEntity")
        for node in activePhysicalNode:
            subList.append(node.attrib)
        return subList
    
    def getBackupsetList(self, clientId):
        self.getSubClientList(clientId)
        flag = 0
        del self.backupsetList[:]
        backupsetInfo = {"clientId":-1, "clientName":None, "agentType":None, "agentId":None, "backupsetId":-1, "backupsetName":None, "instanceName":None, "instanceId":-1}
        for node in self.subclientList:
            #backupsetId = int(node["backupsetId"])
            flag = 0
            for item in self.backupsetList:
                if  node["backupsetId"] == item["backupsetId"]:
                    flag = 1
                    break
            if flag == 1:
                continue
            backupset = copy.deepcopy(backupsetInfo)
            backupset["clientName"] = node["clientName"]
            backupset["agentType"] = node["appName"]
            backupset["backupsetName"] = node["backupsetName"]
            backupset["instanceName"] = node["instanceName"]
            backupset["backupsetId"] = node["backupsetId"]
            backupset["instanceId"] = node["instanceId"]
            backupset["clientId"] = node["clientId"]
            
            self.backupsetList.append(backupset)
        return self.backupsetList
    
    def getClientOSInfo(self, clientId):
        if clientId == None:
            return None
        command = "Client/<<clientId>>"
        command = command.replace("<<clientId>>", clientId)
        resp = self.getCmd(command)
        
        try:
            osinfo = resp.findall(".//OsDisplayInfo")
            self.platform["platform"] = osinfo[0].attrib["OSName"]
            self.platform["ProcessorType"] = osinfo[0].attrib["ProcessorType"]
        
            hostnames = resp.findall(".//clientEntity")
            self.platform["hostName"] = hostnames[0].attrib["hostName"]
        except:
            self.msg = "error get client platform"

    def getClientAgentList(self, clientId):
        agentList = []
        agent = {}
        if clientId == None:
            return None
        command = "Agent?clientId=<<clientId>>"
        command = command.replace("<<clientId>>", clientId)
        resp = self.getCmd(command)
        #print(self.receiveText)
        try:
            activePhysicalNode = resp.findall(".//idaEntity")
            for node in activePhysicalNode:
                #print("agent list")
                #print(node.attrib)
                agent["clientName"] = node.attrib["clientName"]
                agent["agentType"] = node.attrib["appName"]
                agent["appId"] = node.attrib["applicationId"]
                agentList.append(copy.deepcopy(agent))
        except:
            self.msg = "error get agent type"
            pass
        return agentList

    def getClientInfo(self, client):
        self.isNewClient = True
        if self.token == None or client == None:
            return None
        # get client
        if self.getClient(client) == False:
            return None
            
        clientInfo = self.clientInfo        
        self.isNewClient = False
        #get backupsetList
        clientInfo["backupsetList"] = self.getBackupsetList(clientInfo["clientId"])
        #get platform
        self.getClientOSInfo(clientInfo["clientId"])
        
        #get agent list
        clientInfo["agentList"] = self.getClientAgentList(clientInfo["clientId"])
        return clientInfo

    def setVMWareClient(self, clientName, vmClient):
        #param vmClient{"vCenterHost":, "userName":, "passwd":, "proxyList":["", ""]
        if self.isNewClient == False:
            self.msg = "there is the same client"
            return False
            
        keys = vmClient.keys()
        if "vCenterHost" not in keys:
            self.msg = "Param vmClient did not include vCenterHost"
            return False
        if "userName" not in keys:
            self.msg = "Param vmClient did not include userName"
            return False
        if "passwd" not in keys:
            self.msg = "Param vmClient did not include passwd"
            return False
        if "proxyList" not in keys:
            self.msg = "Param vmClient did not include proxyList"
            return False

        input = os.getcwd()+"/template/vmcreate.xml"
        output = os.getcwd()+"/script/vmcreate-" + clientName +".xml"

        try: 
            tree = ET.parse(input)
            root = tree.getroot()
        except: 
            self.msg =  "Error:parse file: " +input
            return False
        
        try:
            proxylist = vmClient["proxyList"]
            users = root.findall(".//vmwareVendor/virtualCenter/userName")
            users[0].text = vmClient["userName"]
            path = root.findall(".//associatedClients")
            path[0].clear()
            parent = path[0]
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
                
        except:
            self.msg = "Error: it is not VSA xml file" + input 
            return False 
        
        try: 
            tree.write(output)
        except : 
            self.msg =  "Error:write file: " +  output
            return False 
        
        cmd = "qoperation execute -af " + output
        param = " -vcenterHostName <<hostName>> -password <<passwd>> -entity/clientName <<clientName>> "
        param = param.replace("<<clientName>>", clientName)
        param = param.replace("<<hostName>>", vmClient["vCenterHost"])
        #param = param.replace("<<userName>>", vmClient["userName"])
        param = param.replace("<<passwd>>", vmClient["passwd"])
        
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

    def getIsNewClient(self):
        return self.isNewClient

class CV_OperatorInterFace(CV_RestApi):
    def __init__(self, token):
        """
        Constructor
        """
        super(CV_OperatorInterFace, self).__init__(token)
        
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
            self.msg = "Properties set successfully"
            return True
        else:
            self.msg = "command " + cmd + " xml format" + updateClientProps + " Error Code: " + errorCode + " receive text is " + self.receiveText
            return False    

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
        schduleList = []
        cmd = "Schedules?subclientId=<<subclientId>>"
        cmd = cmd.replace("<<subclientId>>", subclientId)
        client = self.getCmd(cmd)
        try:
            activePhysicalNode = client.findall(".//task")
            for node in activePhysicalNode:
                schduleList.append(node.attrib)                
        except:
            self.msg = "did not get Task"
        return schduleList

    def _setSchdulist(self, agentType, node, schduleName = None):
        keys = node.keys()
        if "clientName" not in keys:
            self.msg = "param did not include subclientName"
            return False
        if "backupsetName" not in keys:
            self.msg = "param did not include backupsetName"
            return False
        if "instanceName" not in keys:
            self.msg = "param did not include instanceName"
            return False
        if "subclientName" not in keys:
            self.msg = "param did not include subclientName"
            return False
        if "subclientId" not in keys:
            self.msg = "param did not include subclientId"
            return False
        
        subclientId = node["subclientId"]
        clientName = node["clientName"]
        backupsetName = node["backupsetName"]
        instanceName = node["instanceName"]
        subclientName = node["subclientName"]
        
        if "command line" in subclientName:
            return True
        if schduleName == None:
            return True
        #curBackupSet = self.curBackupSet
        delCmd = 'qmodify schedulepolicy -o remove -scp \'<<oldschdule>>\' '
        addCmd = 'qmodify schedulepolicy -o add -scp \'<<newschdule>>\' '        
        qcommand  = ""
        
        if "Oracle" in agentType:
            qcommand = ' -c <<clientName>> -a Q_ORACLE -i <<instanceName>> -s <<subclientName>> '
        if "File" in agentType:
            qcommand = ' -c <<clientName>> -a Q_FILESYSTEM -b <<backupsetName>> -s <<subclientName>> '
        if "SQL" in agentType:
            qcommand = ' -c <<clientName>> -a Q_MSSQL -i <<instanceName>> -s <<subclientName>> '
        if "Virtual" in agentType:
            qcommand = ' -c <<clientName>> -a Q_VIRTUAL_SERVER -i <<instanceName>> -b <<backupsetName>> -s <<subclientName>> '
        
        if qcommand == "":
            self.msg = "did not support this agent type " + agentType
            return False
            
        qcommand = qcommand.replace("<<clientName>>", clientName)
        qcommand = qcommand.replace("<<instanceName>>", instanceName)
        qcommand = qcommand.replace("<<backupsetName>>", backupsetName)
        qcommand = qcommand.replace("<<subclientName>>", subclientName)
        
        oldList = self._getSchduleBySubId(subclientId)
        for node in oldList:
            delCmd = delCmd.replace("<<oldschdule>>", node["taskName"])
            command = delCmd + qcommand
            retCode = self.qCmd(command, "")
        
        if schduleName == None or schduleName == "":
            return True
        addCmd = addCmd.replace("<<newschdule>>", schduleName)
        command = addCmd + qcommand
        retCode = self.qCmd(command, "")
        return retCode
        
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

class CV_Backupset(CV_Client):
    def __init__(self, token, client, agentType, backupset = None):
        """
        Constructor
        """
        super(CV_Backupset, self).__init__(token, client)
        self.operator = CV_OperatorInterFace(token)
        self.isNewBackupset = True
        self.backupsetInfo = None
        self.getBackupset(agentType, backupset)
        self.curBrowselist = []
        
    def getIsNewBackupset(self):
        return self.isNewBackupset
    
    def getBackupset(self, agentType, backupset = None):
        # param client is clientName or clientId 
        # param backupset is backupsetName or backupsetId 
        # return backupset info backupset 
        # None is no backupset
        self.isNewBackupset = True
        self.backupsetInfo = None
        #print(agentType, backupset)
        if agentType == None and backupset == None:
            return None
        for node in self.backupsetList:
            if backupset == None:
                if agentType in node["agentType"]:
                    self.backupsetInfo = node
                    self.isNewBackupset = False
                    return self.backupsetInfo                        
            else:
                #print(node)
                if "Virtual" in agentType or "File System" in agentType:
                    if node["backupsetName"] == backupset and agentType in node["agentType"]:
                        self.backupsetInfo = node
                        self.isNewBackupset = False
                        return self.backupsetInfo
                else:
                    if node["instanceName"] == backupset and agentType in node["agentType"]:
                        self.backupsetInfo = node
                        self.isNewBackupset = False
                        return self.backupsetInfo
                '''
                if node["backupsetId"] == backupset:
                    self.backupsetInfo = node
                    #self._getSubclientList(node["backupsetId"])
                    self.isNewBackupset = False
                    return self.backupsetInfo
                if node["instanceName"] == backupset:
                    self.backupsetInfo = node
                    #self._getSubclientList(node["backupsetId"])
                    self.isNewBackupset = False
                    return self.backupsetInfo
                '''
        return None

    def _setFSSystemState(self, subclientId, platform, systemstates = None):
        if systemstates == None:
            return True
        cmd = 'Subclient/<<subclientId>>';
        cmd = cmd.replace("<<subclientId>>", subclientId)
        if systemstates == True:
            if "Win" in platform:
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
            if "Win" in platform:
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
            
        return self.operator.postClientPorertiesCmd(cmd, updateClientProps)
        
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
                retCode = self.operator.postClientPorertiesCmd(cmd, updateClientProps)
                if retCode == False:
                    return False
            else:
                updateClientProps = '''<App_UpdateSubClientPropertiesRequest><subClientProperties><contentOperationType>ADD</contentOperationType>
                            <content><path><<path>></path></content>
                            </subClientProperties></App_UpdateSubClientPropertiesRequest>'''
                updateClientProps = updateClientProps.replace("<<path>>", path)
                retCode = self.operator.postClientPorertiesCmd(cmd, updateClientProps)
                if retCode == False:
                    return False
        return True
        
    def setFSBackupset(self, backupset = None, content = None):
        # param client is clientName or clientId 
        # backupset is backupsetName or backupsetId
        # content is  FSBackupset {"SPName":, "Schdule":, "Paths":["", ""], "OS":True/False}
        # return True / False        
        if content == None:
            self.msg = "param is not set"
            return False
        keys = content.keys()
        if "Paths" not in keys:
            self.msg = "Paths is not set"
            return False
        if "OS" not in keys:
            self.msg = "OS is not set"
            return False
        if "SPName" not in keys:
            self.msg = "spname is not set"
            return False
        if "Schdule" not in keys:
            self.msg = "schdule is not set"
            return False

        if self.isNewClient == True:
            self.msg = " there is not a client "
            return False
            
        backupsetId = None
        addBackupset = False
        if backupset == None:
            if self.backupsetInfo != None:
                backupsetId = self.backupsetInfo["backupsetId"]
            else:
                self.msg = " there is not a default backupset "
                return False
        else:
            for node in self.backupsetList:
                if node["backupsetName"] == backupset and "File System" in node["agentType"]:
                    backupsetId = node["backupsetId"]
                    break
            if backupsetId == None: # add new backupset
                addBackupset = True
                
        if addBackupset == True:
            command = 'Backupset'
           
            updateClientProps = '''<App_CreateBackupSetRequest><association><entity><appName>File System</appName>
                                <backupsetName><<backupsetName>></backupsetName><clientName><<clientName>></clientName>
                                <instanceName><<backupsetName>></instanceName>
                                </entity></association></App_CreateBackupSetRequest>'''
            updateClientProps = updateClientProps.replace("\n", " ")                    
            updateClientProps = updateClientProps.replace("<<backupsetName>>", backupset)
            updateClientProps = updateClientProps.replace("<<clientName>>", self.clientInfo["clientName"])
            #print(command, updateClientProps)
            retCode = self.operator.postClientPorertiesCmd(command, updateClientProps)
            #print(retCode, self.operator.msg)
            if retCode == False:
                return False
            self.getBackupsetList(self.clientInfo["clientId"])        
            for node in self.backupsetList:
                if node["backupsetName"] == backupset and "File System" in node["agentType"]:
                    backupsetId = node["backupsetId"]
            if backupsetId == None: # add new backupset
                self.msg = "after create new backupset , did not find subclientId: " + backupset
                return False
            
        #print(self.backupsetInfo, backupsetId)
        if backupsetId == None:
            self.msg = "backupid is not select " + backupset
            return False
        #if self.checkRunningJob(self.clientInfo["clientName"],"Windows File System", self.backupsetInfo["backupsetName"], self.backupsetInfo["instanceName"]) == True:
            #self.msg = "there is a running job, did not configure"
            #return False

        for node in self.subclientList:
            if node["backupsetId"] == backupsetId:
                platform = self.clientInfo["platform"]["platform"]
                retCode = self._setFSSystemState(node["subclientId"], platform, content["OS"])
                if retCode == False:
                    self.msg = "修改备份操作系统状态出错：" + self.msg
                    return False
                retCode = self._setFSPaths(node["subclientId"], content["Paths"])
                if retCode == False:
                    self.msg = "修改备份路径出错：" + self.msg
                    return False
                retCode = self.operator._setSPBySubId(node["subclientId"], content["SPName"])
                if retCode == False:
                    self.msg = node["clientName"] + " File System update schdule error " + node["backupsetName"] + self.operator.msg
                    return False
                retCode = self.operator._setSchdulist(node["appName"], node, content["Schdule"])
                if retCode == False:
                    self.msg = node["clientName"] + " File System update schdule error " + node["backupsetName"] + self.operator.msg
                    #print(self.receiveText)
                    return False
                break

        return True

    def _setVMBackupContent(self, node, vmlist, proxyList):
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
                        <<proxyList>>
                        </subClientProperties>
                        </App_UpdateSubClientPropertiesRequest>'''
         
        proxyStr = '''<vsaSubclientProp>
                        <proxies><memberServers><client>
                        <<proxyList>>
                        </client></memberServers></proxies>
                        </vsaSubclientProp>'''    
        memberList = ""
        flag = False
        for proxyNode in proxyList:
            flag = True
            if proxyNode == None or proxyNode == "":
                continue
            memberStr = "<clientName><<proxy>></clientName>"
            memberStr1 = memberStr.replace("<<proxy>>", proxyNode)
            memberList += memberStr1
        
        if flag == True:
            proxyStr = proxyStr.replace("<<proxyList>>", memberList)
            vmUpdateCmd = vmUpdateCmd.replace("<<proxyList>>", proxyStr)
        else:
            vmUpdateCmd = vmUpdateCmd.replace("<<proxyList>>", "")
            
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
        #print(vmUpdateCmd)
        return self.operator.postClientPorertiesCmd(cmd, vmUpdateCmd)
    
    def setVMWareBackup(self, backupset, content = None):
        # backupset is backupsetName or backupsetId
        # content is {"proxyList":["", ""], "vmList":["", ""], "SPName":, "Schdule":}
        # return True / False
        if content == None:
            self.msg = "param is not set"
            return False
        keys = content.keys()
        if "vmList" not in keys:
            self.msg = "content vmlist is not set"
            return False
        if "proxyList" not in keys:
            self.msg = "content proxyList is not set"
            return False
        if "SPName" not in keys:
            self.msg = "spname is not set"
            return False
        if "Schdule" not in keys:
            self.msg = "schdule is not set"
            return False
        
        # 判断是否是VMWare Client
        isVSAClient = False
        for node in self.subclientList:
            if "Virtual" in node["appName"]:
                if "VMware" in node["instanceName"]:
                    isVSAClient = True
                    break
        if isVSAClient == False:
            self.msg = "this client is not vmware client" + self.clientInfo["clientName"]
            return False
            
        # 判断是否是新的backupset名称
        addBackupset = True
        for node in self.backupsetList:
            if node["backupsetName"] == backupset:
                addBackupset = False
                break
        
        # 增加新的备份集合
        if addBackupset == True:
            command = 'qcreate backupset -c <<clientName>> -a Q_VIRTUAL_SERVER -i VMware -n <<backupsetName>>'
            command = command.replace("<<backupsetName>>", backupset)
            command = command.replace("<<clientName>>", self.clientInfo["clientName"])
            retCode = self.qCmd(command)
            receive = str(self.receiveText)
            #print(self.receiveText)
            if "successfully" not in receive:
                self.msg = "create vmware backupset error :" + receive
                return False
            # 刷新客户端的子客户端和备份集合
            self.getBackupsetList(self.clientInfo["clientId"])        
        
        flag = True
        for node in self.subclientList:
            if node["backupsetName"] == backupset:
                subclientNode = node
                flag = False
                break
        if flag == True:
            self.msg = "after create vmware backupset and then did not find : " + backupset
            return False
        
        
        #判断是否有正在运行备份任务
        #if self.checkRunningJob(self.clientInfo["clientName"], self.backupsetInfo["appName"], self.backupsetInfo["backupsetName"], self.backupsetInfo["instanceName"]) == True:
            #self.msg = "there is a running job, did not configure"
            #return False
        
        # 设置VMWare 备份配置
        retCode = self._setVMBackupContent(subclientNode, content["vmList"], content["proxyList"])
        if retCode == False:
            self.msg = "update VMWare content error ：" + self.msg
            return False
        retCode = self.operator._setSPBySubId(subclientNode["subclientId"], content["SPName"])
        if retCode == False:
            self.msg = "associate storage police error：" + self.msg
            return False
        #retCode = self.operator._setSchdulist(node["subclientId"], subclientNode["subclientName"], content["Schdule"])
        agentType = subclientNode["appName"]
        retCode = self.operator._setSchdulist(agentType, subclientNode, content["Schdule"])
        if retCode == False:
            self.msg = "associate schdule error：" + self.msg
            return False
        return True

    def _createOracleInstance(self, clientName, instanceName, platform, credit):
        input = "template/oraCreate.xml"
        output = "script/oraCreat-" + credit["Server"] + ".xml"
        OHOME = credit["ORACLE-HOME"]
        SP = credit["SPName"]
        
        # set oracle home and sp in xml
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
        if "Win" in platform:
            param = " -ClientName <<clientName>> -instanceName <<instanceName>> -oracleUser/domainName <<Server>> -oracleUser/password <<passwd>> -oracleUser/userName <<userName>> "
        else:
            param = " -ClientName <<clientName>> -instanceName <<instanceName>> -oracleUser/userName <<userName>> "
        try:
            param = param.replace("<<clientName>>", clientName)
            param = param.replace("<<instanceName>>", instanceName)
            param = param.replace("<<Server>>", credit["Server"])
            param = param.replace("<<userName>>", credit["userName"])
            param = param.replace("<<passwd>>", credit["passwd"])
        except:
            self.msg = "oracle credit is error"
            return False

        self.qCmd(cmd, param)
        try:
            root = ET.fromstring(self.receiveText)
        except:
            self.msg = "unknown error: " + self.receiveText.decode('utf-8', "ignore")
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
                self.msg = "unknown error: " + self.receiveText.decode('utf-8', "ignore")
                return False
        return True

    def _modiOracleInstance(self, clientName, instanceName, platform, credit):
        input = "template/oraModify.xml"
        output = "script/oraModi-" + credit["Server"] + ".xml"
        OHOME = credit["ORACLE-HOME"]
        SP = credit["SPName"]
        
        # set OHOME AND SP to xml
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
        if "Win" in platform:
            param = " -ClientName <<clientName>> -instanceName <<instanceName>> -oracleUser/domainName <<Server>> -oracleUser/password <<passwd>> -oracleUser/userName <<userName>> "
        else:
            param = " -ClientName <<clientName>> -instanceName <<instanceName>> -oracleUser/userName <<userName>> "
        try:
            param = param.replace("<<clientName>>", clientName)
            param = param.replace("<<instanceName>>", instanceName)
            param = param.replace("<<Server>>", credit["Server"])
            param = param.replace("<<userName>>", credit["userName"])
            param = param.replace("<<passwd>>", credit["passwd"])
        except:
            self.msg = "oracle credit is error"
            return False
        
        self.qCmd(cmd, param)
        try:
            root = ET.fromstring(self.receiveText)
        except:
            self.msg = "unknown error " + self.receiveText.decode('utf-8', "ignore")
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
        
    def setOracleBackupset(self, backupsetName = None, credit = None, content = None):
        # backupset is backupsetName or None: None is create oracle Instance
        # credit is {"Server":，"userName":, "passwd":, "OCS":, "SPName":, "ORACLE-HOME":} or None
        # content is {"SPName":, "Schdule":} or None
        # instanceName == None and credit != None, create Instance
        # instanceName != None and credit != None, modi Instance
        # content != None, associate set sp and sc to subclient
        # return True / False
        if credit != None:
            keys = credit.keys()
            if "Server" not in keys:
                self.msg = "credit - no Server"
                return False
            if "userName" not in keys:
                self.msg = "credit - no userName"
                return False
            if "passwd" not in keys:
                self.msg = "credit - no user passwd"
                return False
            if "OCS" not in keys:
                self.msg = "credit - no OCS"
                return False
            if "SPName" not in keys:
                self.msg = "credit - no SPName"
                return False
            if "ORACLE-HOME" not in keys:
                self.msg = "credit - no ORACLE-HOME"
                return False
        if content != None:
            keys = content.keys()
            if "SPName" not in keys:
                self.msg = " content no SPName"
                return False
            if "Schdule" not in keys:
                self.msg = " content no Schdule"
                return False

        if self.isNewClient == True:
            self.msg = "there is not this client" + self.clientInfo["clientName"]
            return False

        instanceName = backupsetName
        addInstance = True
        for node in self.clientInfo["backupsetList"]:
            if "Oracle" in node["agentType"]:
                addInstance = False
                break
        #print(addInstance, instanceName, backupsetName)            
        if addInstance == True:
            instanceName = backupsetName
        if instanceName == None: 
            self.msg = "add oracle instance is not set instanceName"
            return False
        #if self.checkRunningJob(self.clientInfo["clientName"], "Oracle", None, instanceName) == True:
            #self.msg = "there is a running job, did not configure"
            #return False
        if addInstance == True: # create oracle instance
            if credit == None:
                self.msg = "create oracle instance no set credit"
                return False
            retCode = self._createOracleInstance(self.clientInfo["clientName"], instanceName, self.clientInfo["platform"]["platform"], credit)
            if retCode == False:
                return False
            else: # refere subclient 
                self.getBackupset(self.clientInfo["clientId"])
                instanceName = credit["instanceName"]
                
        else: # modi oracle instance
            if credit != None:  
                retCode = self._modiOracleInstance(self.clientInfo["clientName"], instanceName, self.clientInfo["platform"]["platform"], credit)
                if retCode == False:
                    self.msg = "modi oracle instance error" + self.msg
                    return False

        if content != None:
            for node in self.subclientList:
                if node["instanceName"] == instanceName:
                    retCode = self.operator._setSchdulist("Oracle", node, content["Schdule"])
                    if retCode == False:
                        self.msg = node["clientName"] + " oracle update schdule error " + node["instanceName"] + self.operator.msg
                        return False
                    retCode = self.operator._setSPBySubId(node["subclientId"], content["SPName"]) 
                    if retCode == False:
                        self.msg = node["clientName"] + " oracle update sp error " + node["instanceName"] + self.operator.msg
                        return False
                    continue
            
        return True
        
    def setMssqlBackupset(self, backupset = None, credit = None, content = None):
        # param client is clientName or clientId 
        # backupset is backupsetName or backupsetId
        # credit is {"instanceName":,"Server":, "userName":, "passwd":, SPName":, "useVss":True/False}
        # content is {"SPName":, "Schdule":}
        # return True / False
        instanceName = backupset
        if credit != None:
            keys = credit.keys()
            if "instanceName" not in keys:
                self.msg = "credit - no instanceName"
                return False
            if "Server" not in keys:
                self.msg = "credit - no Server"
                return False
            if "userName" not in keys:
                self.msg = "credit - no userName"
                return False
            if "passwd" not in keys:
                self.msg = "credit - no user passwd"
                return False
            if "SPName" not in keys:
                self.msg = "credit - no SPName"
                return False
            if "userVss" not in keys:
                self.msg = "credit - no userVss"
                return False
        if content != None:
            keys = content.keys()
            if "SPName" not in keys:
                self.msg = " content no SPName"
                return False
            if "Schdule" not in keys:
                self.msg = " content no Schdule"
                return False
        addInstance = True
        for node in self.clientInfo["backupsetList"]:
            if "Oracle" in node["agentType"]:
                addInstance = False
                break
        if self.isNewClient == True:
            self.msg = "there is not this client" + self.clientInfo["clientName"]
            return False
        #if self.checkRunningJob(self.clientInfo["clientName"], "SQL Server", None, instanceName) == True:
            #self.msg = "there is a running job, did not configure"
            #return False
        if addInstance == True: # create mssql instance
            if credit == None:
                self.msg = "create mssql instance no set credit"
                return False
            retCode = self._createMSSqlInstance(self.clientInfo["clientName"], credit)
            if retCode == False:
                return False
            else: # refere subclient 
                self.getSubClientList(self.clientInfo["clientId"])
                instanceName = credit["instanceName"]
                
        else: # modi oracle instance
            if credit != None:  
                if credit["instanceName"] != instanceName:
                    self.msg = "instanceName is not same "
                    return False
                retCode = self._modiMSSqlInstance(self.clientInfo["clientName"], credit)
                if retCode == False:
                    self.msg = "modi mssql instance error" + self.msg
                    return False
        
        if content != None:
            for node in self.subclientList:
                if node["instanceName"] == instanceName:
                    retCode = self.operator._setSchdulist("SQL Server", node, content["Schdule"])
                    if retCode == False:
                        self.msg = node["clientName"] + " mssql update schdule error " + node["instanceName"] + self.operator.msg
                        return False
                    retCode = self.operator._setSPBySubId(node["subclientId"], content["SPName"]) 
                    if retCode == False:
                        self.msg = node["clientName"] + " mssql update sp error " + node["instanceName"] + self.operator.msg
                        return False
                    continue
        return True
    
    
    def browse(self, path = None, browse_file = False):
        list =[]
        if self.backupsetInfo == None:
            self.msg = "there is no this backupset "  + self.backupsetInfo["backupsetName"]
            return None
        backupsetInfo = self.backupsetInfo
        subclientNode = None
        for node in self.subclientList:
            if  backupsetInfo["agentType"] == node["appName"] and backupsetInfo["backupsetName"] == node["backupsetName"]:
                subclientNode = node
                break
                
        if subclientNode == None:
            self.msg = "there is no this subclient "  + self.backupsetInfo["backupsetName"]
            return None
        
        command = "Subclient/<<subclientId>>/Browse?"
        flag = False
        if subclientNode["appName"] == "Virtual Server":
            flag = True
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
            flag = True
            if path == None or path == "":
                param = "path=%5C&showDeletedFiles=True"
            else:
                content =  urllib.quote(path.encode(encoding="utf-8")) 
                param = "path=<<content>>&showDeletedFiles=True"
                param = param.replace("<<content>>", content)
        
        if flag == False:
            self.msg = "agentType did not support" + self.backupsetInfo["agentType"]
            return None
            
        command = command.replace("<<subclientId>>", subclientNode["subclientId"])
        resp = self.getCmd(command + param)
        nodelist = resp.findall(".//dataResultSet")
        for node in nodelist:
            flags = node.findall(".//flags")
            attrib = node.attrib
            #print(attrib)
            if flags[0] != None:
                if "directory" in flags[0].attrib:
                    attrib["DorF"] = "D"
                else:
                    attrib["DorF"] = "F"
            else:
                attrib["DorF"] = "F"
            list.append(attrib)
        #print(list)
        return list
        #print(self.receiveText)
        
    def restoreFSBackupset(self, dest, operator):
        # param client is clientName or clientId 
        # backupset is backupsetName or backupsetId
        # operator is {"restoreTime":, "destPath":, "sourcePaths":["", ""], "overWrite":True/False, "OS Restore":True/False, "inPlace":True/False}
        # return jobId 
        # or -1 is error
        jobId = -1
        
        input = "template/file-Restore.xml"
        output = "script/fileRestore-" + self.clientInfo["clientName"] + ".xml"
        
        if operator != None:
            keys = operator.keys()
            if "restoreTime" not in keys:
                self.msg = "operator - no restoreTime"
                return jobId
            if "destPath" not in keys:
                self.msg = "operator - no destPath"
                return jobId
            if "sourcePaths" not in keys:
                self.msg = "operator - no sourcePaths"
                return jobId
            if "overWrite" not in keys:
                self.msg = "operator - no overWrite"
                return jobId
            if "OS Restore" not in keys:
                self.msg = "operator - no OS Restore"
                return jobId
            if "inPlace" not in keys:
                self.msg = "operator - no inPlace"
                return jobId
        
        sourceClient = self.clientInfo["clientName"]
        destClient = dest
        backupset = self.backupsetInfo["backupsetName"]
        instance = self.backupsetInfo["instanceName"]
        restoreTime = operator["restoreTime"]
        overWrite = operator["overWrite"]
        inPlace = operator["inPlace"]
        destPath =  operator["destPath"]
        sourceItemlist = operator["sourcePaths"]
        try:
            tree = ET.parse(input)
            root = tree.getroot()
            sourceclients = root.findall(".//associations/clientName")
            for node in sourceclients:
                node.text = sourceClient
                #break
            backupsets = root.findall(".//backupsetName")
            for node in backupsets:
                node.text = backupset
            instances = root.findall(".//instanceName")
            for node in instances:
                node.text = instance
            destclients = root.findall(".//destClient/clientName")
            for node in destclients:
                node.text = destClient
                #break
            sourceclients = root.findall(".//backupset/clientName")
            for node in sourceclients:
                node.text = sourceClient
                #break
            overWrites = root.findall(".//commonOptions/unconditionalOverwrite")
            for node in overWrites:
                if overWrite == True:
                    node.text = "true"
                else:
                    node.text = "false"
                #break
            inPlaces = root.findall(".//destination/inPlace")
            for node in inPlaces:
                if inPlace == True:
                    node.text = "true"
                else:
                    node.text = "false"
                break
            destPaths = root.findall(".//destination/destPath")
            for node in destPaths:
                node.text = destPath
                #break

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
            return jobId

        try:
            tree.write(output)
        except:
            self.msg = "error write config file: " + output
            return jobId

        if restoreTime == None:
            cmd = "qoperation execute -af " + output
        else:
            cmd = "qoperation execute -af " + output + " -toTimeValue ' " + restoreTime + "' "
        param = ""
        self.qCmd(cmd, param)
        try:
            root = ET.fromstring(self.receiveText)
        except:
            self.msg = "unknown error" + self.receiveText
            return jobId

        nodes = root.findall(".//jobIds")
        for node in nodes:
            self.msg = "jobId is: " + node.attrib["val"]
            jobId = int(node.attrib["val"])
            return jobId
        self.msg = "unknown error:" + self.receiveText
        return jobId

            
    def restoreVMWareBackupset(self, dest, operator):
        # operator is {"vsaClientName":"vsTest.hzx", "vmGUID":"" , "vmName":"" , "vsaBrowseProxy":"", "vsaRestoreProxy":"", 
        #              "vCenterHost", "DCName", "esxHost", "datastore", "newVMName":"abc", "diskOption":"Auto/Thin/thick", 
        #              "Power":True/False, "overWrite":True/False}
        jobId = -1
        input = "template/VMRestore.xml"
        output = "script/VMRestore-" + operator["vsaClientName"] + "-" + self.backupsetInfo["backupsetName"] + ".xml"
        tree = ET.parse(input)
        root = tree.getroot()
        cvSetXML = CV_VMRestore(root)
        clientName = self.clientInfo["clientName"]
        destClient = dest
        backupsetname = self.backupsetInfo["backupsetName"]
        
        if operator != None:
            keys = operator.keys()
            if "vsaClientName" not in keys:
                self.msg = "operator - no vsaClientName"
                return jobId
            if "vmGUID" not in keys:
                self.msg = "operator - no vmGUID"
                return jobId
            if "vmName" not in keys:
                self.msg = "operator - no user vmName"
                return jobId
            if "vsaBrowseProxy" not in keys:
                self.msg = "operator - no vsaBrowseProxy"
                return jobId
            if "vsaRestoreProxy" not in keys:
                self.msg = "operator - no vsaRestoreProxy"
                return jobId
            if "vCenterHost" not in keys:
                self.msg = "operator - no vCenterHost"
                return jobId
            if "DCName" not in keys:
                self.msg = "operator - no user DCName"
                return jobId
            if "esxHost" not in keys:
                self.msg = "operator - no user esxHost"
                return jobId
            if "datastore" not in keys:
                self.msg = "operator - no datastore"
                return jobId
            if "newVMName" not in keys:
                self.msg = "operator - no newVMName"
                return jobId
            if "diskOption" not in keys:
                self.msg = "operator - no user diskOption"
                return jobId
            if "Power" not in keys:
                self.msg = "operator - no Power"
                return jobId
            if "overWrite" not in keys:
                self.msg = "operator - no overWrite"
                return jobId
        else:
            self.msg == "operator not set"
            return jobId
            
        vmName = operator["vmName"]
        vmGUID = operator["vmGUID"]
        browseProxyClient = operator["vsaBrowseProxy"]
        restoreProxyClient = operator["vsaRestoreProxy"]
        vcenterIp = operator["vCenterHost"]
        vcenterUser = operator["vcenterUser"]
        diskOption = operator["diskOption"]
        power = operator["power"]
        overWrite = operator["overWrite"]
        newname = operator["newVMName"]
        esxhost = operator["esxHost"]
        dataStoreName = operator["datastore"]
        
        #destproxyclient = operator["destproxyclient"]
        
        retCode = cvSetXML.setVMAssociate(backupsetname, clientName)
        if retCode == False:
            self.msg = "the file format is wrong: " + input + " |set backupsetname and clientName"
            return jobId
        retCode = cvSetXML.setVMbrowseOption(backupsetname, browseProxyClient)
        if retCode == False:
            self.msg = "the file format is wrong: " + input + " |set backupsetName browseProxyClient"
            return jobId

        for subclientnode in self.subClientList:
            if subclientnode["backupsetId"] == self.backupsetInfo["backupsetId"]:
                break;
        if subclientnode == None:
            self.msg = "did not get this backupset: %s  %s" % (clientName, backupsetname)
            return jobId

        lists = self.browse(subclientnode, "\\" + vmGUID)
        disklist = []
        for node in lists:
            if ".vmdk" in node["name"]:
                disklist.append(node)

        retCode = cvSetXML.setVMdestination(restoreProxyClient)
        if retCode == False:
            self.msg = "the file format is wrong: " + input + " | set restoreProxyClient "
            return jobId

        retCode = cvSetXML.setVMFileOption(vmGUID)
        if retCode == False:
            self.msg = "the file format is wrong: " + input + "| set vmGUID"
            return jobId
        retCode = cvSetXML.setVMadvancedRestoreOptions(dataStoreName, disklist, esxhost, vmGUID,
                                                       vmName, newname, None)
        if retCode == False:
            self.msg = "the file format is wrong: " + input + " setVMadvancedRestoreOptions"
            return jobId

        retCode = cvSetXML.setVMdiskLevelVMRestoreOption(vcenterIp, esxhost, vcenterUser, diskOption=diskOption,
                                                         overWrite=overWrite, power=power)
        if retCode == False:
            self.msg = "the file format is wrong: " + input + " setVMdiskLevelVMRestoreOption"
            return -jobId

        retCode = cvSetXML.setVMvCenterInstance(dest)
        if retCode == False:
            self.msg = "the file format is wrong: " + input + " destClient"
            return -jobId

        try:
            tree.write(output)
        except:
            self.msg = "error write config file: " + output
            return jobId

        cmd = "qoperation execute -af " + output
        param = ""
        self.qCmd(cmd, param)
        try:
            root = ET.fromstring(self.receiveText)
        except:
            self.msg = "unknown error" + self.receiveText.decode("utf-8", "ignore")
            return jobId

        nodes = root.findall(".//jobIds")
        for node in nodes:
            self.msg = "jobid is: " + node.attrib["val"]
            jobId = int(node.attrib["val"])
            return jobId
        self.msg = "unknown error:" + self.receiveText.decode("utf-8", "ignore")
        return jobId
    
    def restoreOracleBackupset(self, source, dest, operator):
        # param client is clientName or clientId 
        # operator is {"instanceName":, "destClient":, "restoreTime":, "restorePath":None}
        # return JobId 
        # or -1 is error
        jobId = -1
        instance = self.backupsetInfo["instanceName"]
        if operator != None:
            keys = operator.keys()
            if "restoreTime" not in keys:
                self.msg = "operator - no userName"
                return jobId
            if "restorePath" not in keys:
                self.msg = "operator - no user passwd"
                return jobId
        else:
            self.msg = "param not set"
            return jobId

        input = "template/ora-Restore.xml"
        output = "script/oraRestore-" + dest + ".xml"
        
        sourceClient = source
        destClient = dest
        #instance = operator["instanceName"]
        restoreTime = operator["restoreTime"]
        restorePath = operator["restorePath"]
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
            return jobId
        
        try:
            tree.write(output)
        except:
            self.msg = "error write config file: " + output
            return jobId

        if "Last" in restoreTime or restoreTime == None or restoreTime == "" :
            cmd = "qoperation execute -af " + output  
        else:
            cmd = "qoperation execute -af " + output + "-toTimeValue ' " + restoreTime + "' " 
        
        #print(cmd)
        param  = ""
        self.qCmd(cmd, param)
        try:
            root = ET.fromstring(self.receiveText)
        except:
            self.msg = "unknown error" + self.receiveText
            return jobId
            
        nodes = root.findall(".//jobIds")
        for node in nodes:
            self.msg = "jobid is: " + node.attrib["val"]
            jobId = int(node.attrib["val"])
            return jobId
        self.msg = "unknown error:" + str(self.receiveText)
        return jobId

class CV_API(object):
    def __init__(self, cvToken):
        """
        Constructor
        """
        super(CV_API, self).__init__()
        self.token = cvToken
        self.msg = None
    
    def free(self):
        return
        
    def getClientList(self):
        info = CV_GetAllInformation(self.token)
        list =  info.getClientList()
        self.msg = info.msg
        return list

    def getClientInfo(self, client):
        clientInfo = CV_Client(self.token)
        info = clientInfo.getClientInfo(client)
        self.msg = clientInfo.msg
        return info

    def setVMWareClient(self, clientName, vmClient):
        client = CV_Client(self.token, clientName)
        #print(client.clientInfo)
        retCode = client.setVMWareClient(clientName, vmClient)
        self.msg = client.msg
        return retCode
        
    def delVMWareClient(self, client):
        #param client is clientName or clientId 
        #return True / False
        return True
        
    def setRACClient(self, client, racClient):
        # param client is clientName or clientId 
        # param racClient 
        # return True / False
        return True
        
    def delRACClient(self, client):
        # param client is clientName or clientId 
        # return True / False
        return True    
        
    def getBackupset(self, client, agentType, backupset = None):
        # param client is clientName or clientId 
        # param backupset is backupsetName or backupsetId 
        # return backupset info backupset 
        # None is no backupset        
        info = CV_Backupset(self.token, client,agentType)
        backupsetInfo = info.getBackupset(agentType, backupset)
        self.msg = info.msg
        return backupsetInfo
    
    def setFSBackupset(self, client, backupset, content = None):
        # param client is clientName or clientId 
        # backupset is backupsetName or backupsetId
        # content is  FSBackupset {"SPName":, "Schdule":, "Paths":["", ""], "OS":True/False}
        # return True / False
        fsBackupset = CV_Backupset(self.token, client, "File System", backupset)
        if fsBackupset.getIsNewClient() == True:
            self.msg = "there is not this fs Client " + client
            return False
        #print(fsBackupset.backupsetInfo)
        retCode = fsBackupset.setFSBackupset(backupset, content)
        self.msg = fsBackupset.msg
        return retCode

    def setVMWareBackupset(self, client, backupset, content = None):
        # param client is clientName or clientId 
        # backupset is backupsetName or backupsetId
        # content is {"proxyList":["",""], "vmList":["", ""], "SPName":, "Schdule":}
        # return True / False
        vmBackupset = CV_Backupset(self.token, client, "Virtual Server", backupset)
        if vmBackupset.getIsNewClient() == True:
            self.msg = "there is not this VMware Client " + client
            return False
        retCode = vmBackupset.setVMWareBackup(backupset, content)
        self.msg = vmBackupset.msg
        return retCode
        
    def setOracleBackupset(self, client, instanceName, credit, content = None):
        # param client is clientName or clientId 
        # credit is {"instanceName":"ORCL", "Server":，"userName":, "passwd":, "OCS":, "SPName":, "ORACLE-HOME":}
        # content is {"SPName":, "Schdule":}
        # return True / False
        
        oraBackupset = CV_Backupset(self.token, client, "Oracle Database", instanceName)
        if oraBackupset.getIsNewClient() == True:
            self.msg = "there is not this oracle Client " + client
            return False
        retCode = oraBackupset.setOracleBackupset(instanceName, credit, content)
        self.msg = oraBackupset.msg
        return retCode

    def setMssqlBackupset(self, client, instanceName, credit = None, content = None):
        # param client is clientName or clientId 
        # backupset is backupsetName or backupsetId
        # credit is {"instanceName":,"Server":, "userName":, "passwd":, SPName":, "useVss":True/False}
        # content is {"SPName":, "Schdule":}
        # return True / False
        mssqlBackupset = CV_Backupset(self.token, client, "SQL Server", instanceName)
        if mssqlBackupset.getIsNewClient() == True:
            self.msg = "there is not this oracle Client " + client
            return False            
        retCode = mssqlBackupset.setMssqlBackupset(instanceName, credit, content)
        self.msg = mssqlBackupset.msg
        return retCode
        
        return True
    
    def browse(self, client, agentType, backupset, path, showDeleted = False):
        # param client is clientName or clientId 
        # backupset is backupsetName or backupsetId
        # operator is {"destClient":, "restoreTime":, "destPath":, "Path":, "overwrite":True/False, "OS Restore": True/False}
        # return JobId 
        # or -1 is error
        cvBackupset = CV_Backupset(self.token, client, agentType, backupset)
        if cvBackupset.getIsNewClient() == True:
            self.msg = "there is not this Client " + client
            return None
        if cvBackupset.getIsNewBackupset() == True:
            self.msg = "there is not this backupset " + backupset
            return None
            
        list = cvBackupset.browse(path)
        self.msg = cvBackupset.msg
        return list
        
    def restoreFSBackupset(self, source, dest, backupset, operator = None):
        # param client is clientName or clientId 
        # backupset is backupsetName or backupsetId
        # operator is {"restoreTime":, "destPath":, "Path":["", ""], "overwrite":True/False, "OS Restore": True/False}
        # return JobId 
        # or -1 is error
        
        sourceClient = CV_Backupset(self.token, source, "File System", backupset)
        if sourceClient.getIsNewClient() == True:
            self.msg = "there is not this Client " + source
            return None
        if sourceClient.getIsNewBackupset() == True:
            self.msg = "there is not this backupset " + backupset
            return None
        destClient = CV_Backupset(self.token, dest, "File System")
        if destClient.getIsNewClient() == True:
            self.msg = "there is not this Client " + dest
            return None
        retCode = sourceClient.restoreFSBackupset(dest, operator)
        self.msg  = sourceClient.msg
        return retCode
        
    def restoreOracleBackupset(self, source, dest, instance, operator = None):
        # param client is clientName or clientId 
        # operator is {"instanceName":, "destClient":, "restoreTime":, "restorePath":None}
        # return JobId 
        # or -1 is error
        
        #print(client, backupset, credit, content)
        sourceBackupset = CV_Backupset(self.token, source, "Oracle Database", instance)
        destBackupset = CV_Backupset(self.token, dest, "Oracle Database", instance)
        if sourceBackupset.getIsNewBackupset() == True:
            self.msg = "there is not this oracle sid " + source
            return False            
        if destBackupset.getIsNewBackupset() == True:
            self.msg = "there is not this oracle sid " + dest
            return False            
        jobId = sourceBackupset.restoreOracleBackupset(source, dest, operator)
        self.msg = sourceBackupset.msg
        return jobId

    def restoreMssqlBackupset(self, source, dest, instance, operator = None):
        # param client is clientName or clientId 
        # backupset is backupsetName or backupsetId
        # operator is {"instanceName":, "destClient":, "restoreTime":, "restorePath":None, "OverWrite":True/False}
        # return JobId 
        # or -1 is error
        return -1
        
    def restoreVMWareBackupset(self, source, dest, backupset = None, operator = None):
        # operator is {"vmGUID":"" , "vmName":"" , "vsaBrowseProxy":"", "vsaRestoreProxy":"", 
        #              "vCenterHost", "DCName", "esxHost", "datastore", "newVMName":"abc", "diskOption":"Auto/Thin/thick", 
        #              "Power":True/False, "overWrite":True/False}
        # return JobId 
        # or -1 is error
        
        sourceBackupset = CV_Backupset(self.token, source, "Virtual Server", backupset)
        destBackupset = CV_Backupset(self.token, dest, "Virtual Server")
        if sourceBackupset.getIsNewBackupset() == True:
            self.msg = "there is not this virtual Client " + source
            return False            
        if destBackupset.getIsNewBackupset() == True:
            self.msg = "there is not this virtual Client " + dest
            return False            
        jobId = sourceBackupset.restoreVMWareBackupset(dest, operator)
        self.msg = sourceBackupset.msg
        return jobId

        return -1    
        
    def getJobList(self, client, agentType = None, backupset = None, type = "backup"):
        # param client is clientName or clientId or None is all client
        # param agentType = 
        # backupset is backsetupName or backsetupId
        # operator is backup, restore, admin and others
        # return job List, {"jobID":, "clientName":, "clientId":, "Start":, "End":, } 
        # None is no job
        joblist= []
        jobRec = {}
        info = CV_GetAllInformation(self.token)
        clientRec = CV_Client(self.token, client)
        list = info.getJobList(clientId = clientRec.clientInfo["clientId"], type = type, appTypeName=agentType, backupsetName = backupset, subclientName = None, start = None, end = None)
        for node in list:
            jobRec["jobId"] = node["jobId"]
            jobRec["status"] = node["status"]
            jobRec["client"] = clientRec.clientInfo["clientName"]
            jobRec["agentType"] = node["appTypeName"]
            jobRec["backupSetName"] = node["backupSetName"]
            #jobRec["destClient"] = node["destClientName"]
            jobRec["jobType"] = node["jobType"]
            jobRec["Level"] = node["backupLevel"]
            #流量
            jobRec["appSize"] = node["sizeOfApplication"]
            #磁盘容量
            jobRec["diskSize"] = node["sizeOfMediaOnDisk"]
            jobRec["StartTime"] = node["jobStartTime"]
            jobRec["LastTime"] = node["lastUpdateTime"]
            joblist.append(copy.deepcopy(jobRec))
        self.msg = info.msg
        return joblist
        
    def getSPList(self):
        # return SPNameList, {"SPName":, "SPId":} 
        spList = []
        sp = {"SPName":None, "SPId":None}
        info = CV_GetAllInformation(self.token)
        list =  info.getSPList()
        for node in list:
            sp["SPName"] = node["storagePolicyName"]
            sp["SPId"] = node["storagePolicyId"]
            spList.append(copy.deepcopy(sp))
        self.msg = info.msg
        return spList
        
    def getSchduleList(self):
        # return schdulelist, {"SchduleName":, "SchduleId":} 
        schduleList = []
        schdule = {"SchduleName":None, "SchduleId":None}
        info = CV_GetAllInformation(self.token)
        list =  info.getSchduleList()
        for node in list:     
            schdule["SchduleName"] = node["taskName"]
            schdule["SchduleId"] = node["taskId"]
            schduleList.append(copy.deepcopy(schdule))
        self.msg = info.msg
        return schduleList
        
    def getVMWareVMList(self, client):
        # param client is clientName or clientId
        # return vmlist, {"VMName":, "VMGuID":} 
        clientInfo = CV_Client(self.token)
        info = clientInfo.getClientInfo(client)
        if info == None:
            self.msg = clientInfo.msg
            return None
        clientId = info["clientId"]
        info = CV_GetAllInformation(self.token)        
        info.discoverVM(clientId)
        vmlist = info.vmList
        
        vmRec = {"VMName":None, "VMGuID":None} 
        list = []
        for node in vmlist:
            vmRec["VMName"] = node["name"]
            vmRec["VMGuID"] = node["strGUID"]
            list.append(copy.deepcopy(vmRec))
        return list
        
    def getVMWareDataStoreList(self, client):
        # param client is clientName or clientId
        # return dataStorelist {"DCName":, "DCGuID":, "ESXName":, "ESXGuID":, "DSName":, "DSGuID":, "totalSize":, "freeSize"} 
        clientInfo = CV_Client(self.token)
        info = clientInfo.getClientInfo(client)
        if info == None:
            self.msg = clientInfo.msg
            return None
        clientId = info["clientId"]
        info = CV_GetAllInformation(self.token)        
        list = info.discoverVCInfo(clientId)
        self.msg = info.msg
        return list
    
if __name__ == "__main__":
    print('it is main')
    conn = pymssql.connect(host='TEST1\COMMVAULT', user='sa_cloud', password='1qaz@WSX', database='CommServ')
    cur = conn.cursor()
    cur.execute('select top 5 * from CommCellBackupInfo')
    joblist =cur.fetchall()
    cur.close()
    conn.close()


    for job in joblist:

        print job

    