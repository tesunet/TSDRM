import sys
import requests
import time
import copy
import datetime
import pymysql
from xml.dom.minidom import parse, parseString
import os
from lxml import etree

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
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
        # super().__init__()
        self.service = 'http://<<server>>:<<port>>/SearchSvc/CVWebService.svc/'
        self.credit = {"webaddr": "", "port": "", "username": "", "passwd": "", "token": "", "lastlogin": 0}
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
        # print(credit)
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

    def __init__(self, token):
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

    def _rest_cmd(self, restCmd, command, updatecmd=""):
        token = self.token.checkLogin()
        if token == None:
            self.msg = "did not get token"
            return None

        clientPropsReq = self.service + command
        self.sendText = clientPropsReq

        try:
            update = updatecmd.encode(encoding="utf-8")
        except:
            update = updatecmd
        headers = {'Cookie2': token}

        if restCmd == "GET":
            try:
                r = requests.get(clientPropsReq, data=update, headers=headers)
            except:
                self.msg = "Connect Failed: webaddr " + self.webaddr + " port " + self.port
                return None

        if restCmd == "POST":
            try:
                r = requests.post(clientPropsReq, data=update, headers=headers)
            except:
                self.msg = "Connect Failed: webaddr " + self.webaddr + " port " + self.port
                return None

        if restCmd == "PUT":
            try:
                r = requests.put(clientPropsReq, data=update, headers=headers)
            except:
                self.msg = "Connect Failed: webaddr " + self.webaddr + " port " + self.port
                return None

        if restCmd == "DEL":
            try:
                r = requests.delete(clientPropsReq, data=update, headers=headers)
            except:
                self.msg = "Connect Failed: webaddr " + self.webaddr + " port " + self.port
                return None

        if restCmd == "QCMD":
            try:
                r = requests.post(clientPropsReq, data=update, headers=headers)
            except:
                self.msg = "Connect Failed: webaddr " + self.webaddr + " port " + self.port
                return None

        if r.status_code == 200 or r.status_code == 201:
            self.receiveText = r.text
        else:
            self.receiveText = r.status_code
            self.msg = 'Failure: webaddr ' + self.webaddr + " port " + self.port + " retcode: %d" % r.status_code

        return self.receiveText

    def getCmd(self, command, updatecmd=""):
        """
        Constructor
        get command function
        """
        retString = self._rest_cmd("GET", command, updatecmd)
        # if tag:
        #     with open(r"C:\Users\Administrator\Desktop\{0}.xml".format(tag), "w") as f:
        #         f.write(retString)
        try:
            return ET.fromstring(retString)
        except:
            self.msg = "receive string is not XML format"
            return None

    def postCmd(self, command, updatecmd=""):
        """
        Constructor
        get command function
        """
        retString = self._rest_cmd("POST", command, updatecmd)
        try:
            respRoot = ET.fromstring(retString)
            respEle = respRoot.findall(".//response")
            errorCode = ""
            for node in respEle:
                errorCode = node.attrib["errorCode"]
            if errorCode == "0":
                self.msg = "Set successfully"
                return retString
            else:
                try:
                    errString = node.attrib["errorString"]
                    self.msg = "PostCmd:" + command + "ErrCode: " + errorCode + "ErrString:" + errString
                except:
                    self.msg = "post command:" + command + " Error Code: " + errorCode + " receive text is " + self.receiveText
                    pass
            return None
        except:
            self.msg = "receive string is not XML format:" + self.receiveText
            return None

    def delCmd(self, command, updatecmd=""):
        # DELETE <webservice>/Backupset/{backupsetId}
        retString = self._rest_cmd("DELETE", command, updatecmd)
        try:
            respRoot = ET.fromstring(retString)
            respEle = respRoot.findall(".//response")
            errorCode = ""
            for node in respEle:
                errorCode = node.attrib["errorCode"]
            if errorCode == "0":
                self.msg = "Set successfully"
                return True
            self.msg = "del command:" + command + " xml format:" + updatecmd + " Error Code: " + errorCode + " receive text is " + self.receiveText
            return False
        except:
            self.msg = "receive string is not XML format:" + self.receiveText
            return False

    def putCmd(self, command, updatecmd=""):
        # PUT <webservice>/Backupset/{backupsetId}
        retString = self._rest_cmd("PUT", command, updatecmd)
        try:
            respRoot = ET.fromstring(retString)
            respEle = respRoot.findall(".//response")
            errorCode = ""
            for node in respEle:
                errorCode = node.attrib["errorCode"]
            if errorCode == "0":
                self.msg = "Set successfully"
                return retString
            self.msg = "del command:" + command + " xml format:" + updatecmd + " Error Code: " + errorCode + " receive text is " + self.receiveText
            return None
        except:
            self.msg = "receive string is not XML format:" + self.receiveText
            return None

    def qCmd(self, command, updatecmd=""):
        """
        Constructor
        get command function
        """
        retString = self._rest_cmd("QCMD", command, updatecmd)
        try:
            respRoot = ET.fromstring(retString)
            respjob = respRoot.findall(".//jobIds")
            for node in respjob:
                return True
            respEle = respRoot.findall(".//response")
            errorCode = ""
            for node in respEle:
                errorCode = node.attrib["errorCode"]
            if errorCode == "0":
                self.msg = "Set successfully"
                return True
            else:
                try:
                    errString = node.attrib["errorString"]
                    self.msg = "qcmd command:" + command + " Error Code: " + errorCode + " ErrString: " + errString
                except:
                    self.msg = "qcmd command:" + command + " Error Code: " + errorCode + " receive text is " + self.receiveText
                    pass
            return False
        except:
            # traceback.print_exc()
            return retString


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
        clientRec = {"clientName": None, "clientId": -1}
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

    def getJobList(self, clientId, type="backup", appTypeName=None, backupsetName=None, subclientName=None, start=None,
                   end=None):
        statusList = {"Running": "运行", "Waiting": "等待", "Pending": "未决", "Suspend": "终止", "Completed": "完成",
                      "Failed": "失败", "Failed to Start": "启动失败", "Killed": "杀掉"}
        '''
        Running
        Waiting
        Pending
        Suspend
        Pending
        Suspended
        Kill Pending
        Interrupt Pending
        Interrupted
        Queued
        Running (cannot be verified)
        Abnormal Terminated Cleanup
        Completed
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

        # print(resp)
        # print(self.receiveText)
        activePhysicalNode = resp.findall(".//jobs/jobSummary")
        for node in activePhysicalNode:
            # if start != None:
            # if end != None:
            # print(node.attrib)
            if appTypeName != None:
                if appTypeName not in node.attrib["appTypeName"]:
                    continue
            if backupsetName != None:
                if backupsetName not in node.attrib["backupSetName"]:
                    continue
            if subclientName != None:
                if subclientName not in node.attrib["subclientName"]:
                    continue
            status = node.attrib["status"]
            try:
                node.attrib["status"] = statusList[status]
            except:
                node.attrib["status"] = status
            self.jobList.append(node.attrib)
        return self.jobList

    def checkRunningJob(self, clientName, appType, backupsetName, instanceName):
        command = "QCommand/qlist job -c <<clientName>> -format xml"
        command = command.replace("<<clientName>>", clientName)
        retString = self.postCmd(command)
        try:
            resp = ET.fromstring(retString)
        except:
            self.msg = "qlist job xml format is error"
            return False
        # print(clientName, appType, backupsetName, instanceName)
        jobitems = resp.findall(".//jobs")
        for node in jobitems:
            attrib = node.attrib
            # print(attrib, clientName, appType, backupsetName, instanceName)
            if attrib["clientName"] == clientName:
                # if attrib["appName"] == appType:
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

    def discoverVM(self, clientId, path=None):
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
        # VSBrowse/4787/INVENTORY?requestType=INVENTORY
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
            # print(attribDC)
            if attribDC["type"] == '4':
                self.vmDCName.append(attribDC)
            hostnodes = node.findall(".//inventoryInfo")
            for hostnode in hostnodes:
                attribHost = hostnode.attrib
                # print(attribHost)
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
                        # print(attribDatastore)
                        attribDatastore["esxhost"] = attribHost["name"]
                        attribDatastore["esxstrGUID"] = attribHost["strGUID"]
                        self.vmDataStore.append(attribDatastore)
        return self.vmDataStore


class CV_Client(CV_GetAllInformation):
    def __init__(self, token, client=None):
        """
        Constructor
        """
        super(CV_Client, self).__init__(token)
        self.client = client
        self.backupsetList = []
        self.subclientList = []
        self.platform = {"platform": None, "ProcessorType": 0, "hostName": None}
        self.clientInfo = {"clientName": None, "clientId": None, "platform": self.platform, "backupsetList": [],
                           "agentList": []}
        # self.backupInfo = {"clientId":None, "clientName":None, "agentType":None, "agentId":None, "backupsetId":None, "backupsetName":None, "instanceName":None, "instanceId":None}

        self.isNewClient = True
        self.getClientInfo(client)
        self.schedule_description = []

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
        backupsetInfo = {"clientId": -1, "clientName": None, "agentType": None, "agentId": None, "backupsetId": -1,
                         "backupsetName": None, "instanceName": None, "instanceId": -1}
        for node in self.subclientList:
            # backupsetId = int(node["backupsetId"])
            flag = 0
            for item in self.backupsetList:
                if node["backupsetId"] == item["backupsetId"]:
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
            backupset["subclientId"] = node["subclientId"]

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

    def getClientInstance(self, clientId):
        instance = {}
        myproxylist = []
        if clientId == None:
            return None
        command = "/instance?clientId=<<clientId>>"
        command = command.replace("<<clientId>>", clientId)
        resp = self.getCmd(command)

        try:
            vcinfo = resp.findall(".//vmwareVendor/virtualCenter")
            instance["HOST"] = vcinfo[0].attrib["domainName"]
            instance["USER"] = vcinfo[0].attrib["userName"]

            proxylist = resp.findall(".//memberServers/client")
            for proxy in proxylist:
                myproxylist.append({"clientId": proxy.attrib["clientId"], "clientName": proxy.attrib["clientName"]})
            instance["PROXYLIST"] = myproxylist
        except:
            self.msg = "error get client instance"
        return instance

    def getClientAgentList(self, clientId):
        agentList = []
        agent = {}
        if clientId == None:
            return None
        command = "Agent?clientId=<<clientId>>"
        command = command.replace("<<clientId>>", clientId)
        resp = self.getCmd(command)
        # print(self.receiveText)
        try:
            activePhysicalNode = resp.findall(".//idaEntity")
            for node in activePhysicalNode:
                # print("agent list")
                # print(node.attrib)
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
        # get backupsetList
        clientInfo["backupsetList"] = self.getBackupsetList(clientInfo["clientId"])
        # get platform
        self.getClientOSInfo(clientInfo["clientId"])
        # get agent list
        clientInfo["agentList"] = self.getClientAgentList(clientInfo["clientId"])
        if (clientInfo["platform"]["platform"]).upper() == "ANY":
            clientInfo["instance"] = self.getClientInstance(clientInfo["clientId"])
        return clientInfo

    def setVMWareClient(self, myclientName, vmClient):
        # param vmClient{"vCenterHost":, "userName":, "passwd":, "proxyList":["", ""]

        newVMWXML = '''
            <App_CreatePseudoClientRequest>
                <clientInfo>
                    <clientType>VIRTUAL_SERVER_CLIENT</clientType>
                    <virtualServerClientProperties>
                        <virtualServerInstanceInfo>
                            <vsInstanceType>VMW</vsInstanceType>
                            <vmwareVendor>
                                <virtualCenter>
                                    <userName></userName>
                                    <password></password>
                                    <confirmPassword></confirmPassword>
                                </virtualCenter>
                                <vcenterHostName></vcenterHostName>
                            </vmwareVendor>
                            <associatedClients>
                                <memberServers>
                                    <client>
                                        <clientName></clientName>
                                    </client>
                                </memberServers>
                            </associatedClients>
                        </virtualServerInstanceInfo>
                    </virtualServerClientProperties>
                </clientInfo>
                <entity>
                    <clientName></clientName>
                </entity>
            </App_CreatePseudoClientRequest>'''

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

        try:
            root = ET.fromstring(newVMWXML)
        except:
            self.msg = "Error:parse xml: " + newVMWXML
            # traceback.print_exc()
            return False

        try:
            users = root.findall(".//userName")
            users[0].text = vmClient["userName"]

            proxylist = vmClient["proxyList"]
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

            passwd = root.findall(".//password")
            passwd[0].text = vmClient["passwd"]
            confirmPassword = root.findall(".//confirmPassword")
            confirmPassword[0].text = vmClient["passwd"]

            clientName = root.findall(".//entity/clientName")
            clientName[0].text = myclientName

            hosts = root.findall(".//vmwareVendor/vcenterHostName")
            hosts[0].text = vmClient["vCenterHost"]

        except:
            self.msg = "Error: it is not VSA xml file"
            return False

        xmlString = ""
        xmlString = ET.tostring(root, encoding='utf-8', method='xml')
        # print(xmlString.encode(encoding="utf-8"))
        return self.qCmd("QCommand/qoperation execute", xmlString)

    def getIsNewClient(self):
        return self.isNewClient

    def getSubclientInfo(self, subclientId):
        backupInfo = {}
        mycontent = []
        if subclientId == None:
            return None
        command = "/Subclient/<<subclientId>>"
        # command = "/instance/10"
        command = command.replace("<<subclientId>>", subclientId)
        resp = self.getCmd(command)
        # print self.receiveText
        try:
            subClientEntity = resp.findall(".//subClientEntity")
            # 应用名
            backupInfo["appName"] = subClientEntity[0].get("appName", "")
            # 存储策略
            dataBackupStoragePolicy = resp.findall(".//dataBackupStoragePolicy")
            backupInfo["Storage"] = dataBackupStoragePolicy[0].get("storagePolicyName", "")
            # *********************** Schedule, Oracle connect string, SQL Server if  default covered
            # 计划策略
            # 取出所有taskid
            cmd_get_all_tasks = "SchedulePolicy"
            get_all_tasks_id = self.getCmd(cmd_get_all_tasks)
            all_tasks = get_all_tasks_id.findall(".//task")
            schedule_name = ""
            if all_tasks:
                for task in all_tasks:
                    task_id = task.get("taskId", "")
                    # 取出taskName
                    cmd_get_schedule_name = "SchedulePolicy/{0}".format(task_id)
                    content = self.getCmd(cmd_get_schedule_name)

                    # 对应子客户端
                    subclient_id = content.findall(".//associations")
                    subclient_id_list = []
                    if subclient_id:
                        for i in subclient_id:
                            subclient_id_list.append(i.get("subclientId", ""))

                    if subclientId in subclient_id_list:
                        schedule_content = content.findall(".//task")
                        if schedule_content:
                            schedule_name = schedule_content[0].get("taskName", "")
                        break
            backupInfo["schedule_name"] = schedule_name
            # *****************************************************************************

            # 文件备份集信息
            if backupInfo["appName"] == "File System":
                # content
                contentlist = resp.findall(".//content")
                for content in contentlist:
                    mycontent.append(content.get("path", ""))
                backupInfo["content"] = mycontent
                # backupSystemState
                fsSubClientProp = resp.findall(".//fsSubClientProp")
                backupInfo["backupSystemState"] = fsSubClientProp[0].get("backupSystemState", "")
                if backupInfo["backupSystemState"] == "0" or backupInfo["backupSystemState"] == "false":
                    backupInfo["backupSystemState"] = "FALSE"
                if backupInfo["backupSystemState"] == "1" or backupInfo["backupSystemState"] == "true":
                    backupInfo["backupSystemState"] = "TRUE"
            # 数据库实例信息
            if backupInfo["appName"] == "SQL Server":
                command = "/instance?clientId=<<clientId>>"
                command = command.replace("<<clientId>>", subClientEntity[0].get("clientId", ""))
                resp = self.getCmd(command)
                instancenodes = resp.findall(".//instanceProperties")
                for instancenode in instancenodes:
                    instance = instancenode.findall(".//instance")

                    if instance[0].get("instanceId", "") == subClientEntity[0].get("instanceId", ""):
                        backupInfo["instanceName"] = instance[0].get("instanceName", "")
                        mssqlInstance = instancenode.findall(".//mssqlInstance")
                        backupInfo["vss"] = mssqlInstance[0].get("useVss", "")
                        if backupInfo["vss"] == "0" or backupInfo["vss"] == "false":
                            backupInfo["vss"] = "FALSE"
                        if backupInfo["vss"] == "1" or backupInfo["vss"] == "true":
                            backupInfo["vss"] = "TRUE"

                        # iscover
                        iscover = instancenode.findall(".//mssqlInstance/overrideHigherLevelSettings")
                        if iscover:
                            iscover = iscover[0]
                            backupInfo["iscover"] = iscover.get("overrideGlobalAuthentication", "")
                        else:
                            backupInfo["iscover"] = ""

                        if backupInfo["iscover"] == "0" or backupInfo["iscover"] == "false":
                            backupInfo["iscover"] = "FALSE"
                        if backupInfo["iscover"] == "1" or backupInfo["iscover"] == "true":
                            backupInfo["iscover"] = "TRUE"
                        # user:<userAccount/>
                        userAccount = instancenode.findall(".//mssqlInstance/overrideHigherLevelSettings/userAccount")
                        if userAccount:
                            backupInfo["userName"] = userAccount[0].get("userName", "")
                        else:
                            backupInfo["userName"] = ""
                        break
            if backupInfo["appName"] == "Oracle":
                command = "/instance?clientId=<<clientId>>"
                command = command.replace("<<clientId>>", subClientEntity[0].get("clientId", ""))
                resp = self.getCmd(command)
                instancenodes = resp.findall(".//instanceProperties")
                for instancenode in instancenodes:
                    instance = instancenode.findall(".//instance")
                    if instance[0].get("instanceId", "") == subClientEntity[0].get("instanceId", ""):
                        backupInfo["instanceName"] = instance[0].get("instanceName", "")
                        oracleInstance = instancenode.findall(".//oracleInstance")
                        backupInfo["oracleHome"] = oracleInstance[0].get("oracleHome", "")
                        oracleUser = instancenode.findall(".//oracleInstance/oracleUser")
                        backupInfo["oracleUser"] = oracleUser[0].get("userName", "")
                        # connect
                        sqlConnect = instancenode.findall(".//oracleInstance/sqlConnect")
                        backupInfo["conn1"] = sqlConnect[0].get("userName", "")
                        backupInfo["conn2"] = ""  # sys密码，没有
                        backupInfo["conn3"] = sqlConnect[0].get("domainName", "")
                        break
            if backupInfo["appName"] == "Virtual Server":
                children = resp.findall(".//vmContent/children")
                for child in children:
                    mycontent.append(child.get("displayName", ""))
                backupInfo["content"] = mycontent
                backupInfo["backupsetName"] = subClientEntity[0].get("backupsetName", "")
        except:
            self.msg = "error get client instance"
        # print(backupInfo)
        return backupInfo


class CV_OperatorInterFace(CV_RestApi):
    def __init__(self, token):
        """
        Constructor
        """
        super(CV_OperatorInterFace, self).__init__(token)

    def postClientPorertiesCmd(self, cmd, updateClientProps=""):
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

    def _setSPBySubId(self, subclientId, spname=None):
        if spname == None:
            return True
        cmd = 'Subclient/<<subclientId>>'
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

    def _setSchdulist(self, agentType, node, schduleName=None):
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
        # curBackupSet = self.curBackupSet
        delCmd = 'qmodify schedulepolicy -o remove -scp \'<<oldschdule>>\' '
        addCmd = 'qmodify schedulepolicy -o add -scp \'<<newschdule>>\' '
        qcommand = ""

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
            retCode = self.qCmd("QCommand/" + command, "")

        if schduleName == None or schduleName == "":
            return True
        addCmd = addCmd.replace("<<newschdule>>", schduleName)
        command = addCmd + qcommand
        retCode = self.qCmd("QCommand/" + command, "")
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

    def setVMdiskLevelVMRestoreOption(self, esxServerName, hostOrCluster, userName="Administrator", diskOption="Auto",
                                      overWrite=False, power=False):
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
    def __init__(self, token, client, agentType, backupset=None):
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

    def getBackupset(self, agentType, backupset=None):
        # param client is clientName or clientId
        # param backupset is backupsetName or backupsetId
        # return backupset info backupset
        # None is no backupset
        self.isNewBackupset = True
        self.backupsetInfo = None
        # print(agentType, backupset)
        if agentType == None and backupset == None:
            return None
        for node in self.backupsetList:
            if backupset == None:
                if agentType in node["agentType"]:
                    self.backupsetInfo = node
                    self.isNewBackupset = False
                    return self.backupsetInfo
            else:
                # print(node)
                if "Virtual" in agentType or "File System" in agentType:
                    if node["backupsetName"] == backupset and agentType in node["agentType"]:
                        self.backupsetInfo = node
                        self.isNewBackupset = False
                        return self.backupsetInfo
                else:
                    if node["instanceName"].upper() == backupset.upper() and node[
                        "agentType"].upper() in agentType.upper():
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

    def _setFSSystemState(self, subclientId, platform, systemstates=None):
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

    def _setFSPaths(self, subclientId, paths=None):
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

    def setFSBackupset(self, backupset=None, content=None):
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
            if backupsetId == None:  # add new backupset
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
            # print(command, updateClientProps)
            retCode = self.operator.postClientPorertiesCmd(command, updateClientProps)
            # print(retCode, self.operator.msg)
            if retCode == False:
                return False
            self.getBackupsetList(self.clientInfo["clientId"])
            for node in self.backupsetList:
                if node["backupsetName"] == backupset and "File System" in node["agentType"]:
                    backupsetId = node["backupsetId"]
            if backupsetId == None:  # add new backupset
                self.msg = "after create new backupset , did not find subclientId: " + backupset
                return False

        # print(self.backupsetInfo, backupsetId)
        if backupsetId == None:
            self.msg = "backupid is not select " + backupset
            return False
        # if self.checkRunningJob(self.clientInfo["clientName"],"Windows File System", self.backupsetInfo["backupsetName"], self.backupsetInfo["instanceName"]) == True:
        # self.msg = "there is a running job, did not configure"
        # return False

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
                    self.msg = node["clientName"] + " File System update schdule error " + node[
                        "backupsetName"] + self.operator.msg
                    return False
                retCode = self.operator._setSchdulist(node["appName"], node, content["Schdule"])
                if retCode == False:
                    self.msg = node["clientName"] + " File System update schdule error " + node[
                        "backupsetName"] + self.operator.msg
                    # print(self.receiveText)
                    return False
                break

        return True

    def _setVMBackupContent(self, node, vmlist, proxyList):
        # print(node)
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
            if vm == None or vm == "":
                continue
            vmname = 'displayName="<<vm>>"'
            vmname = vmname.replace("<<vm>>", vm)
            vmcontent += '<children equalsOrNotEquals="1" name="" <<vmname>> type="VMName"/>'
            vmcontent = vmcontent.replace("<<vmname>>", vmname)

        if vmcontent == "":
            return True
        vmUpdateCmd = vmUpdateCmd.replace("<<vmcontent>>", vmcontent)
        # print(vmUpdateCmd)
        return self.operator.postClientPorertiesCmd(cmd, vmUpdateCmd)

    def setVMWareBackup(self, backupset, content=None):
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
            retCode = self.qCmd("QCommand/" + command)
            receive = str(self.receiveText)
            # print(self.receiveText)
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

        # 判断是否有正在运行备份任务
        # if self.checkRunningJob(self.clientInfo["clientName"], self.backupsetInfo["appName"], self.backupsetInfo["backupsetName"], self.backupsetInfo["instanceName"]) == True:
        # self.msg = "there is a running job, did not configure"
        # return False

        # 设置VMWare 备份配置
        retCode = self._setVMBackupContent(subclientNode, content["vmList"], content["proxyList"])
        if retCode == False:
            self.msg = "update VMWare content error ：" + self.msg
            return False
        retCode = self.operator._setSPBySubId(subclientNode["subclientId"], content["SPName"])
        if retCode == False:
            self.msg = "associate storage police error：" + self.msg
            return False
        # retCode = self.operator._setSchdulist(node["subclientId"], subclientNode["subclientName"], content["Schdule"])
        agentType = subclientNode["appName"]

        retCode = self.operator._setSchdulist(agentType, subclientNode, content["Schdule"])
        if retCode == False:
            self.msg = "associate schdule error：" + self.msg
            return False
        return True

    def _createOracleInstance(self, clientName, instanceName, platform, credit):
        newOracleXML = '''
            <App_CreateInstanceRequest>
              <instanceProperties>
                <description></description>
                <instance>
                  <appName>Oracle</appName>
                  <clientName></clientName>
                  <instanceName></instanceName>
                </instance>
                <oracleInstance>
                  <TNSAdminPath></TNSAdminPath>
                  <blockSize>1048576</blockSize>
                  <catalogConnect>
                    <domainName></domainName>
                    <userName></userName>
                  </catalogConnect>
                  <crossCheckTimeout>600</crossCheckTimeout>
                  <ctrlFileAutoBackup>1</ctrlFileAutoBackup>
                  <dataArchiveGroup>
                    <storagePolicyName>SP-30DAYS</storagePolicyName>
                  </dataArchiveGroup>
                  <disableRMANcrosscheck>false</disableRMANcrosscheck>
                  <encryptionFlag>ENC_NONE</encryptionFlag>
                  <isOnDemand>false</isOnDemand>
                  <numberOfArchiveLogBackupStreams>1</numberOfArchiveLogBackupStreams>
                  <oracleHome></oracleHome>
                  <oracleStorageDevice>
                    <commandLineStoragePolicy>
                      <storagePolicyName>SP-30DAYS</storagePolicyName>
                    </commandLineStoragePolicy>
                    <deDuplicationOptions>
                      <generateSignature>ON_CLIENT</generateSignature>
                    </deDuplicationOptions>
                    <logBackupStoragePolicy>
                      <storagePolicyName>SP-30DAYS</storagePolicyName>
                    </logBackupStoragePolicy>
                    <networkAgents>1</networkAgents>
                    <softwareCompression>USE_STORAGE_POLICY_SETTINGS</softwareCompression>
                    <throttleNetworkBandwidth>0</throttleNetworkBandwidth>
                  </oracleStorageDevice>
                  <oracleUser>
                    <domainName></domainName>
                    <password></password>
                    <userName></userName>
                  </oracleUser>
                  <oracleWalletAuthentication>false</oracleWalletAuthentication>
                  <overrideDataPathsForCmdPolicy>false</overrideDataPathsForCmdPolicy>
                  <overrideDataPathsForLogPolicy>false</overrideDataPathsForLogPolicy>
                  <sqlConnect>
                    <domainName></domainName>
                    <userName>/</userName>
                  </sqlConnect>
                  <useCatalogConnect>false</useCatalogConnect>
                </oracleInstance>
                <security/>
              </instanceProperties>

            </App_CreateInstanceRequest>'''
        try:
            root = ET.fromstring(newOracleXML)
        except:
            self.msg = "Error:parse xml: " + newOracleXML
            return False
        try:
            homenodes = root.findall(".//oracleHome")
            for node in homenodes:
                node.text = credit["ORACLE-HOME"]
                break
            spnodes = root.findall(".//storagePolicyName")
            for node in spnodes:
                node.text = credit["SPName"]
            clientnamenodes = root.findall(".//clientName")
            for node in clientnamenodes:
                node.text = clientName
            instancenamenodes = root.findall(".//instanceName")
            for node in instancenamenodes:
                node.text = instanceName
            domainnamenodes = root.findall(".//oracleUser/domainName")
            for node in domainnamenodes:
                node.text = credit["Server"]
            usernamenodes = root.findall(".//oracleUser/userName")
            for node in usernamenodes:
                node.text = credit["userName"]
            passwordnodes = root.findall(".//oracleUser/password")
            for node in passwordnodes:
                node.text = credit["passwd"]
        except:
            self.msg = "Error: it is not Oracle xml file"
            # traceback.print_exc()
            return False

        xmlString = ""
        xmlString = ET.tostring(root, encoding='utf-8', method='xml')
        # print(xmlString.encode(encoding="utf-8"))
        return self.qCmd("QCommand/qoperation execute", xmlString)

    def _modiOracleInstance(self, clientName, instanceName, platform, credit):
        updateOracleXML = '''
            <App_UpdateInstancePropertiesRequest>
                <association>
                    <entity>
                        <appName>Oracle</appName>
                        <clientName/>
                        <instanceName/>
                    </entity>
                </association>
                <instanceProperties>
                    <description/>
                    <instance>
                        <appName>Oracle</appName>
                        <clientName/>
                        <instanceName/>
                    </instance>
                    <oracleInstance>
                        <DBID/>
                        <TNSAdminPath/>
                        <blockSize/>
                        <catalogConnect>
                            <domainName/>
                            <password/>
                            <userName/>
                        </catalogConnect>
                        <clientOSType/>
                        <crossCheckTimeout/>
                        <ctrlFileAutoBackup/>
                        <disableRMANcrosscheck>false</disableRMANcrosscheck>
                        <encryptionFlag>ENC_NONE</encryptionFlag>
                        <isOnDemand>false</isOnDemand>
                        <numberOfArchiveLogBackupStreams>1</numberOfArchiveLogBackupStreams>
                        <oracleHome/>
                        <oracleStorageDevice>
                            <commandLineStoragePolicy>
                                <storagePolicyName/>
                            </commandLineStoragePolicy>
                            <deDuplicationOptions>
                                <generateSignature>ON_CLIENT</generateSignature>
                            </deDuplicationOptions>
                            <logBackupStoragePolicy>
                                <storagePolicyName/>
                            </logBackupStoragePolicy>
                            <networkAgents>1</networkAgents>
                            <softwareCompression>USE_STORAGE_POLICY_SETTINGS</softwareCompression>
                            <throttleNetworkBandwidth>0</throttleNetworkBandwidth>
                        </oracleStorageDevice>
                        <oracleUser>
                            <domainName/>
                            <password/>
                            <userName/>
                        </oracleUser>
                        <overrideDataPathsForCmdPolicy>false</overrideDataPathsForCmdPolicy>
                        <overrideDataPathsForLogPolicy>false</overrideDataPathsForLogPolicy>
                        <sqlConnect>
                            <domainName/>
                            <password/>
                            <userName/>
                        </sqlConnect>
                        <useCatalogConnect/>
                        <oracleWalletAuthentication>false</oracleWalletAuthentication>
                    </oracleInstance>
                    <security>
                        <associatedUserGroups>
                            <userGroupName/>
                        </associatedUserGroups>
                        <associatedUserGroups>
                            <userGroupName/>
                        </associatedUserGroups>
                        <associatedUserGroupsOperationType/>
                        <ownerCapabilities/>
                    </security>
                    <version/>
                </instanceProperties>
            </App_UpdateInstancePropertiesRequest>'''

        try:
            root = ET.fromstring(updateOracleXML)
        except:
            self.msg = "Error:parse xml: " + updateOracleXML
            # traceback.print_exc()
            return False

        try:
            homenodes = root.findall(".//oracleHome")
            for node in homenodes:
                node.text = credit["ORACLE-HOME"]
                break
            spnodes = root.findall(".//storagePolicyName")
            for node in spnodes:
                node.text = credit["SPName"]
            clientnamenodes = root.findall(".//clientName")
            for node in clientnamenodes:
                node.text = clientName
            instancenamenodes = root.findall(".//instanceName")
            for node in instancenamenodes:
                node.text = instanceName
            domainnamenodes = root.findall(".//oracleUser/domainName")
            for node in domainnamenodes:
                node.text = credit["Server"]
            usernamenodes = root.findall(".//oracleUser/userName")
            for node in usernamenodes:
                node.text = credit["userName"]
            passwordnodes = root.findall(".//oracleUser/password")
            for node in passwordnodes:
                node.text = credit["passwd"]
        except:
            self.msg = "Error: it is not Oracle xml file"
            # traceback.print_exc()
            return False

        xmlString = ""
        xmlString = ET.tostring(root, encoding='utf-8', method='xml')
        # print(xmlString.encode(encoding="utf-8"))
        return self.qCmd("QCommand/qoperation execute", xmlString)

    def _createMSSqlInstance(self, clientName, instanceName, platform, credit):
        newmssqlXML = '''
            <App_CreateInstanceRequest>
              <instanceProperties>
                <description></description>
                <instance>
                  <appName>SQL Server</appName>
                  <clientName></clientName>
                  <instanceName></instanceName>
                </instance>
                <mssqlInstance>
                  <MSSQLStorageDevice>
                    <commandLineStoragePolicy>
                      <storagePolicyName></storagePolicyName>
                    </commandLineStoragePolicy>
                    <logBackupStoragePolicy>
                      <storagePolicyName></storagePolicyName>
                    </logBackupStoragePolicy>
                  </MSSQLStorageDevice>
                  <enableSQLTransLogStaging>false</enableSQLTransLogStaging>
                  <isOnDemand>false</isOnDemand>
                  <overrideHigherLevelSettings>
                    <overrideGlobalAuthentication>false</overrideGlobalAuthentication>
                    <useLocalSystemAccount>true</useLocalSystemAccount>
                    <userAccount>
                      <userName></userName>
                    </userAccount>
                  </overrideHigherLevelSettings>
                  <serverType>DataBase Engine</serverType>
                  <useVss></useVss>
                  <vDITimeOut>300</vDITimeOut>
                </mssqlInstance>
                <version>10.0.1600</version>
              </instanceProperties>
            </App_CreateInstanceRequest>'''

        try:
            root = ET.fromstring(newmssqlXML)
        except:
            self.msg = "Error:parse xml: " + newmssqlXML
            return False

        # set oracle home and sp in xml
        try:
            clientnodes = root.findall(".//instance/clientName")
            for node in clientnodes:
                node.text = clientName
                break
            instancenodes = root.findall(".//instance/instanceName")
            for node in instancenodes:
                node.text = instanceName
                break
            spnodes = root.findall(".//storagePolicyName")
            for node in spnodes:
                node.text = credit["SPName"]
            vssnodes = root.findall(".//useVss")
            for node in vssnodes:
                node.text = credit["useVss"]
        except:
            self.msg = "Error: it is not MSSQL xml file"
            return False

        xmlString = ""
        xmlString = ET.tostring(root, encoding='utf-8', method='xml')
        return self.qCmd("QCommand/qoperation execute", xmlString)

    def _modiMSSqlInstance(self, clientName, instanceName, platform, credit):
        updatemssqlXML = '''
            <App_UpdateInstancePropertiesRequest>
              <instanceProperties>
                <description></description>
                <instance>
                  <appName>SQL Server</appName>
                  <clientName></clientName>
                  <instanceName></instanceName>
                </instance>
                <mssqlInstance>
                  <MSSQLStorageDevice>
                    <commandLineStoragePolicy>
                      <storagePolicyName></storagePolicyName>
                    </commandLineStoragePolicy>
                    <logBackupStoragePolicy>
                      <storagePolicyName></storagePolicyName>
                    </logBackupStoragePolicy>
                  </MSSQLStorageDevice>
                  <enableSQLTransLogStaging>false</enableSQLTransLogStaging>
                  <isOnDemand>false</isOnDemand>
                  <overrideHigherLevelSettings>
                    <overrideGlobalAuthentication>false</overrideGlobalAuthentication>
                    <useLocalSystemAccount>true</useLocalSystemAccount>
                    <userAccount>
                      <userName></userName>
                    </userAccount>
                  </overrideHigherLevelSettings>
                  <serverType>DataBase Engine</serverType>
                  <useVss></useVss>
                  <vDITimeOut>300</vDITimeOut>
                </mssqlInstance>
                <version>10.0.1600</version>
              </instanceProperties>

            </App_UpdateInstancePropertiesRequest>'''
        try:
            root = ET.fromstring(updatemssqlXML)
        except:
            self.msg = "Error:parse xml: " + updatemssqlXML
            return False

        # set oracle home and sp in xml
        try:
            clientnodes = root.findall(".//instance/clientName")
            for node in clientnodes:
                node.text = clientName
                break
            instancenodes = root.findall(".//instance/instanceName")
            for node in instancenodes:
                node.text = instanceName
                break
            spnodes = root.findall(".//storagePolicyName")
            for node in spnodes:
                node.text = credit["SPName"]
            vssnodes = root.findall(".//useVss")
            for node in vssnodes:
                node.text = credit["useVss"]
        except:
            self.msg = "Error: it is not MSSQL xml file"
            return False

        xmlString = ""
        xmlString = ET.tostring(root, encoding='utf-8', method='xml')
        return self.qCmd("QCommand/qoperation execute", xmlString)

    def setOracleBackupset(self, backupsetName=None, credit=None, content=None):
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
        # print(addInstance, instanceName, backupsetName)
        if addInstance == True:
            instanceName = backupsetName
        if instanceName == None:
            self.msg = "add oracle instance is not set instanceName"
            return False
        # if self.checkRunningJob(self.clientInfo["clientName"], "Oracle", None, instanceName) == True:
        # self.msg = "there is a running job, did not configure"
        # return False
        if addInstance == True:  # create oracle instance
            if credit == None:
                self.msg = "create oracle instance no set credit"
                return False
            retCode = self._createOracleInstance(self.clientInfo["clientName"], instanceName,
                                                 self.clientInfo["platform"]["platform"], credit)
            if retCode == False:
                return False
            else:  # refere subclient
                self.getBackupset(self.clientInfo["clientId"])
                instanceName = credit["instanceName"]

        else:  # modi oracle instance
            if credit != None:
                retCode = self._modiOracleInstance(self.clientInfo["clientName"], instanceName,
                                                   self.clientInfo["platform"]["platform"], credit)
                if retCode == False:
                    self.msg = "modi oracle instance error" + self.msg
                    return False

        if content != None:
            for node in self.subclientList:
                if node["instanceName"] == instanceName:
                    retCode = self.operator._setSchdulist("Oracle", node, content["Schdule"])
                    if retCode == False:
                        self.msg = node["clientName"] + " oracle update schdule error " + node[
                            "instanceName"] + self.operator.msg
                        return False
                    retCode = self.operator._setSPBySubId(node["subclientId"], content["SPName"])
                    if retCode == False:
                        self.msg = node["clientName"] + " oracle update sp error " + node[
                            "instanceName"] + self.operator.msg
                        return False
                    continue

        return True

    def setMssqlBackupset(self, backupset=None, credit=None, content=None):
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
            if "useVss" not in keys:
                self.msg = "credit - no useVss"
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
            if "SQL Server" in node["agentType"]:
                addInstance = False
                break
        if self.isNewClient == True:
            self.msg = "there is not this client" + self.clientInfo["clientName"]
            return False
        # if self.checkRunningJob(self.clientInfo["clientName"], "SQL Server", None, instanceName) == True:
        # self.msg = "there is a running job, did not configure"
        # return False
        if addInstance == True:  # create mssql instance
            if credit == None:
                self.msg = "create mssql instance no set credit"
                return False
            retCode = self._createMSSqlInstance(self.clientInfo["clientName"], instanceName,
                                                self.clientInfo["platform"]["platform"], credit)
            if retCode == False:
                return False
            else:  # refere subclient
                self.getSubClientList(self.clientInfo["clientId"])
                instanceName = credit["instanceName"]

        else:  # modi oracle instance
            if credit != None:
                if credit["instanceName"] != instanceName:
                    self.msg = "instanceName is not same "
                    return False
                retCode = self._modiMSSqlInstance(self.clientInfo["clientName"], instanceName,
                                                  self.clientInfo["platform"]["platform"], credit)
                if retCode == False:
                    self.msg = "modi mssql instance error" + self.msg
                    return False

        if content != None:
            for node in self.subclientList:
                if node["instanceName"] == instanceName:
                    retCode = self.operator._setSchdulist("SQL Server", node, content["Schdule"])
                    if retCode == False:
                        self.msg = node["clientName"] + " mssql update schdule error " + node[
                            "instanceName"] + self.operator.msg
                        return False
                    retCode = self.operator._setSPBySubId(node["subclientId"], content["SPName"])
                    if retCode == False:
                        self.msg = node["clientName"] + " mssql update sp error " + node[
                            "instanceName"] + self.operator.msg
                        return False
                    continue
        return True

    def browse(self, path=None, browse_file=False):
        list = []
        if self.backupsetInfo == None:
            self.msg = "there is no this backupset " + self.backupsetInfo["backupsetName"]
            return None
        backupsetInfo = self.backupsetInfo
        subclientNode = None
        for node in self.subclientList:
            if backupsetInfo["agentType"] == node["appName"] and backupsetInfo["backupsetName"] == node[
                "backupsetName"]:
                subclientNode = node
                break
        if subclientNode == None:
            self.msg = "there is no this subclient " + self.backupsetInfo["backupsetName"]
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
                content = urllib.quote(path.encode(encoding="utf-8"))
                if browse_file == True:
                    param = "path=<<content>>&showDeletedFiles=false&vsFileBrowse=true"
                else:
                    param = "path=<<content>>&showDeletedFiles=false&vsDiskBrowse=true"
                param = param.replace("<<content>>", content)
        if "File System" in subclientNode["appName"]:
            flag = True
            if path == None or path == "":
                param = "path=%5C&showDeletedFiles=True"
            else:
                content = urllib.quote(path.encode(encoding="utf-8"))
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
            # print(attrib)
            if flags[0] != None:
                if "directory" in flags[0].attrib:
                    attrib["DorF"] = "D"
                else:
                    attrib["DorF"] = "F"
            else:
                attrib["DorF"] = "F"
            list.append(attrib)
        # print(list)
        return list
        # print(self.receiveText)

    def restoreFSBackupset(self, dest, operator):
        # param client is clientName or clientId
        # backupset is backupsetName or backupsetId
        # operator is {"restoreTime":, "destPath":, "sourcePaths":["", ""], "overWrite":True/False, "OS Restore":True/False, "inPlace":True/False}
        # return jobId
        # or -1 is error
        jobId = -1

        restoreFSXML = '''
            <TMMsg_CreateTaskReq>
              <taskInfo>
                <task>
                  <taskFlags>
                    <disabled>false</disabled>
                  </taskFlags>
                  <policyType>DATA_PROTECTION</policyType>
                  <taskType>IMMEDIATE</taskType>
                  <initiatedFrom>COMMANDLINE</initiatedFrom>
                </task>
                <associations>
                  <type>GALAXY</type>
                  <subclientName></subclientName>
                  <backupsetName>defaultBackupSet</backupsetName>
                  <instanceName>DefaultInstanceName</instanceName>
                  <appName>File System</appName>
                  <clientName></clientName>
                  <clientGroupIdForGUI>0</clientGroupIdForGUI>
                  <consumeLicense>true</consumeLicense>
                  <clientSidePackage>true</clientSidePackage>
                </associations>
                <subTasks>
                  <subTask>
                    <subTaskType>RESTORE</subTaskType>
                    <operationType>RESTORE</operationType>
                  </subTask>
                  <options>
                    <restoreOptions>
                      <browseOption>
                        <commCellId>2</commCellId>
                        <backupset>
                          <backupsetName>defaultBackupSet</backupsetName>
                          <clientName></clientName>
                        </backupset>
                        <timeRange/>
                        <noImage>false</noImage>
                        <useExactIndex>false</useExactIndex>
                        <mediaOption>
                          <library/>
                          <mediaAgent/>
                          <drivePool/>
                          <copyPrecedence>
                            <copyPrecedenceApplicable>false</copyPrecedenceApplicable>
                          </copyPrecedence>
                        </mediaOption>
                        <timeZone>
                          <TimeZoneName>(GMT+08:00) &#x5317;&#x4eAC;&#xFF0C;&#x91CD;&#x5e86;&#xFF0C;&#x9999;&#x6e2F;&#x7279;&#x522B;&#x884C;&#x653F;&#x533A;&#xFF0C;&#x4e4C;&#x9C81;&#x6728;&#x9F50;</TimeZoneName>
                        </timeZone>
                        <listMedia>false</listMedia>
                      </browseOption>
                      <destination>
                        <destPath></destPath>
                        <destClient>
                          <clientName></clientName>
                        </destClient>
                        <inPlace>true</inPlace>
                        <isLegalHold>false</isLegalHold>
                        <restoreOnlyIfTargetExists>false</restoreOnlyIfTargetExists>
                        <noOfStreams>0</noOfStreams>
                      </destination>
                      <restoreACLsType>ACL_DATA</restoreACLsType>
                      <sharePointRstOption>
                        <is90OrUpgradedClient>false</is90OrUpgradedClient>
                      </sharePointRstOption>
                      <volumeRstOption>
                        <volumeLeveRestore>false</volumeLeveRestore>
                      </volumeRstOption>
                      <virtualServerRstOption>
                        <isDiskBrowse>false</isDiskBrowse>
                        <viewType>DEFAULT</viewType>
                        <isBlockLevelReplication>false</isBlockLevelReplication>
                      </virtualServerRstOption>
                      <fileOption>
                        <sourceItem>\</sourceItem>
                        <browseFilters>&lt;?xml version='1.0' encoding='UTF-8'?&gt;&lt;databrowse_Query type="0" queryId="0"&gt;&lt;dataParam&gt;&lt;sortParam ascending="1"&gt;&lt;sortBy val="38" /&gt;&lt;sortBy val="0" /&gt;&lt;/sortParam&gt;&lt;paging firstNode="0" pageSize="1000" skipNode="0" /&gt;&lt;/dataParam&gt;&lt;/databrowse_Query&gt;</browseFilters>
                      </fileOption>
                      <impersonation>
                        <useImpersonation>false</useImpersonation>
                        <user>
                          <userName></userName>
                        </user>
                      </impersonation>
                      <commonOptions>
                        <overwriteFiles>true</overwriteFiles>
                        <detectRegularExpression>true</detectRegularExpression>
                        <wildCard>false</wildCard>
                        <unconditionalOverwrite>false</unconditionalOverwrite>
                        <stripLevelType>PRESERVE_LEVEL</stripLevelType>
                        <preserveLevel>1</preserveLevel>
                        <stripLevel>0</stripLevel>
                        <recreateMountPoints>true</recreateMountPoints>
                        <restoreOnlyStubExists>false</restoreOnlyStubExists>
                        <powerRestore>false</powerRestore>
                        <doNotOverwriteFileOnDisk>false</doNotOverwriteFileOnDisk>
                        <systemStateBackup>false</systemStateBackup>
                        <onePassRestore>false</onePassRestore>
                        <offlineMiningRestore>false</offlineMiningRestore>
                        <isFromBrowseBackup>true</isFromBrowseBackup>
                        <clusterDbBackupType>ER_NON_AUTHORITATIVE</clusterDbBackupType>
                        <clusterDBBackedup>false</clusterDBBackedup>
                        <restoreToDisk>false</restoreToDisk>
                        <restoreToExchange>false</restoreToExchange>
                      </commonOptions>
                    </restoreOptions>
                    <adminOpts>
                      <contentIndexingOption>
                        <subClientBasedAnalytics>false</subClientBasedAnalytics>
                      </contentIndexingOption>
                    </adminOpts>
                  </options>
                </subTasks>
              </taskInfo>
            </TMMsg_CreateTaskReq>'''

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
        else:
            self.msg == "operator not set"
            return jobId

        try:
            root = ET.fromstring(restoreFSXML)
        except:
            self.msg = "Error:parse xml: " + restoreFSXML
            return jobId

        sourceClient = self.clientInfo["clientName"]
        destClient = dest
        backupset = self.backupsetInfo["backupsetName"]
        instance = self.backupsetInfo["instanceName"]
        restoreTime = operator["restoreTime"]
        overWrite = operator["overWrite"]
        inPlace = operator["inPlace"]
        destPath = operator["destPath"]
        sourceItemlist = operator["sourcePaths"]
        try:
            sourceclients = root.findall(".//associations/clientName")
            for node in sourceclients:
                node.text = sourceClient
                # break
            backupsets = root.findall(".//backupsetName")
            for node in backupsets:
                node.text = backupset
            instances = root.findall(".//instanceName")
            for node in instances:
                node.text = instance
            destclients = root.findall(".//destClient/clientName")
            for node in destclients:
                node.text = destClient
                # break
            sourceclients = root.findall(".//backupset/clientName")
            for node in sourceclients:
                node.text = sourceClient
                # break
            overWrites = root.findall(".//commonOptions/unconditionalOverwrite")
            for node in overWrites:
                if overWrite == True:
                    node.text = "true"
                else:
                    node.text = "false"
                # break
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
                # break

            parent = root.findall(".//fileOption")
            children = parent[0].getchildren()
            for child in children:
                if child.tag == "sourceItem":
                    parent[0].remove(child)

            for sourceItem in sourceItemlist:
                child = ET.Element('sourceItem')
                child.text = sourceItem
                parent[0].append(child)
            if len(sourceItemlist) == 0:
                child = ET.Element('sourceItem')
                child.text = '\\'
                parent[0].append(child)
            if "Last" not in restoreTime and restoreTime != None and restoreTime != "":
                timeRange = root.findall(".//timeRange")
                for node in timeRange:
                    toTimeValue = ET.Element('toTimeValue')
                    toTimeValue.text = restoreTime
                    node.append(toTimeValue)
        except:
            self.msg = "the file format is wrong"
            return jobId

        xmlString = ""
        xmlString = ET.tostring(root, encoding='utf-8', method='xml')
        if self.qCmd("QCommand/qoperation execute", xmlString):
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
        restoreVMXML = '''
            <TMMsg_CreateTaskReq>

              <taskInfo>
                <associations>
                  <appName>Virtual Server</appName>
                  <backupsetName></backupsetName>
                  <clientName></clientName>
                  <clientSidePackage>true</clientSidePackage>
                  <commCellName></commCellName>
                  <consumeLicense>true</consumeLicense>
                  <csGUID></csGUID>
                  <flags/>
                  <hostName></hostName>
                  <instanceName>VMware</instanceName>
                  <subclientName></subclientName>
                  <type>GALAXY</type>
                </associations>
                <subTasks>
                  <options>
                    <adminOpts>
                      <contentIndexingOption>
                        <subClientBasedAnalytics>false</subClientBasedAnalytics>
                      </contentIndexingOption>
                    </adminOpts>
                    <restoreOptions>
                      <browseOption>
                        <backupset>
                          <backupsetName></backupsetName>
                          <clientName></clientName>
                        </backupset>
                        <commCellId>2</commCellId>
                        <listMedia>false</listMedia>
                        <mediaOption>
                          <copyPrecedence>
                            <copyPrecedenceApplicable>false</copyPrecedenceApplicable>
                          </copyPrecedence>
                          <drivePool/>
                          <library/>
                          <mediaAgent/>
                        </mediaOption>
                        <noImage>false</noImage>
                        <timeRange/>
                        <timeZone>
                          <TimeZoneName>(GMT+08:00) &#x5317;&#x4eAC;&#xFF0C;&#x91CD;&#x5e86;&#xFF0C;&#x9999;&#x6e2F;&#x7279;&#x522B;&#x884C;&#x653F;&#x533A;&#xFF0C;&#x4e4C;&#x9C81;&#x6728;&#x9F50;</TimeZoneName>
                        </timeZone>
                        <useExactIndex>false</useExactIndex>
                      </browseOption>
                      <commonOptions>
                        <clusterDBBackedup>false</clusterDBBackedup>
                        <detectRegularExpression>true</detectRegularExpression>
                        <offlineMiningRestore>false</offlineMiningRestore>
                        <onePassRestore>false</onePassRestore>
                        <powerRestore>false</powerRestore>
                        <restoreToDisk>false</restoreToDisk>
                        <systemStateBackup>false</systemStateBackup>
                        <wildCard>false</wildCard>
                      </commonOptions>
                      <destination>
                        <destClient>
                          <clientName></clientName>
                        </destClient>
                        <inPlace>false</inPlace>
                        <isLegalHold>false</isLegalHold>
                        <noOfStreams>0</noOfStreams>
                      </destination>
                      <fileOption>
                        <browseFilters>&lt;?xml version='1.0' encoding='UTF-8'?&gt;&lt;databrowse_Query type="0" queryId="0"&gt;&lt;dataParam&gt;&lt;sortParam ascending="1"&gt;&lt;sortBy val="38" /&gt;&lt;sortBy val="0" /&gt;&lt;/sortParam&gt;&lt;paging firstNode="0" pageSize="1000" skipNode="0" /&gt;&lt;/dataParam&gt;&lt;/databrowse_Query&gt;</browseFilters>
                        <sourceItem></sourceItem>
                      </fileOption>
                      <sharePointRstOption>
                        <is90OrUpgradedClient>false</is90OrUpgradedClient>
                      </sharePointRstOption>
                      <virtualServerRstOption>
                        <diskLevelVMRestoreOption>
                          <advancedRestoreOptions>
                            <Datastore></Datastore>
                            <FolderPath></FolderPath>
                            <disks>
                              <Datastore></Datastore>
                              <name></name>
                            </disks>
                            <disks>
                              <Datastore></Datastore>
                              <name></name>
                            </disks>
                            <esxHost></esxHost>
                            <guid></guid>
                            <name></name>
                            <newName></newName>
                            <nics>
                              <destinationNetwork>VM Network</destinationNetwork>
                              <networkName></networkName>
                              <sourceNetwork>VM Network</sourceNetwork>
                              <sourceNetworkId></sourceNetworkId>
                              <subnetId></subnetId>
                            </nics>
                            <resourcePoolPath>/</resourcePoolPath>
                          </advancedRestoreOptions>
                          <dataCenterName></dataCenterName>
                          <dataStore>
                            <dataStoreName></dataStoreName>
                            <freeSpaceInBytes>0</freeSpaceInBytes>
                            <totalSizeInBytes>0</totalSizeInBytes>
                          </dataStore>
                          <delayMigrationMinutes>0</delayMigrationMinutes>
                          <diskOption></diskOption>
                          <esxServerName></esxServerName>
                          <hostOrCluster></hostOrCluster>
                          <passUnconditionalOverride></passUnconditionalOverride>
                          <powerOnVmAfterRestore></powerOnVmAfterRestore>
                          <redirectWritesToDatastore></redirectWritesToDatastore>
                          <transportMode>Auto</transportMode>
                          <userPassword>
                            <userName></userName>
                          </userPassword>
                          <vmFolderName></vmFolderName>
                          <vmName></vmName>
                        </diskLevelVMRestoreOption>
                        <esxServer></esxServer>
                        <isAttachToNewVM>false</isAttachToNewVM>
                        <isBlockLevelReplication>false</isBlockLevelReplication>
                        <isDiskBrowse>true</isDiskBrowse>
                        <isFileBrowse>false</isFileBrowse>
                        <isVirtualLab>false</isVirtualLab>
                        <isVolumeBrowse>false</isVolumeBrowse>
                        <vCenterInstance>
                          <appName>Virtual Server</appName>
                          <clientName></clientName>
                          <instanceName>VMware</instanceName>
                        </vCenterInstance>
                        <viewType>DEFAULT</viewType>
                      </virtualServerRstOption>
                      <volumeRstOption>
                        <destinationVendor>NONE</destinationVendor>
                        <volumeLeveRestore>false</volumeLeveRestore>
                        <volumeLevelRestoreType>VIRTUAL_MACHINE</volumeLevelRestoreType>
                      </volumeRstOption>
                    </restoreOptions>
                </options>
                  <subTask>
                    <operationType>RESTORE</operationType>
                    <subTaskType>RESTORE</subTaskType>
                  </subTask>
                </subTasks>
                <task>
                  <initiatedFrom>COMMANDLINE</initiatedFrom>
                  <policyType>DATA_PROTECTION</policyType>
                  <taskFlags>
                    <disabled>false</disabled>
                  </taskFlags>
                  <taskType>IMMEDIATE</taskType>
                </task>
              </taskInfo>

            </TMMsg_CreateTaskReq>'''

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
        try:
            root = ET.fromstring(restoreVMXML)
        except:
            self.msg = "Error:parse xml: " + restoreVMXML
            return jobId

        cvSetXML = CV_VMRestore(root)
        clientName = self.clientInfo["clientName"]
        backupsetname = self.backupsetInfo["backupsetName"]
        vmName = operator["vmName"]
        vmGUID = operator["vmGUID"]
        browseProxyClient = operator["vsaBrowseProxy"]
        restoreProxyClient = operator["vsaRestoreProxy"]
        vcenterIp = operator["vCenterHost"]
        vcenterUser = operator["vcenterUser"]
        diskOption = operator["diskOption"]
        power = operator["Power"]
        overWrite = operator["overWrite"]
        newname = operator["newVMName"]
        esxhost = operator["esxHost"]
        dataStoreName = operator["datastore"]
        restoreTime = operator["restoreTime"]

        retCode = cvSetXML.setVMAssociate(backupsetname, clientName)
        if retCode == False:
            self.msg = "the file format is wrong: " + input + " |set backupsetname and clientName"
            return jobId
        retCode = cvSetXML.setVMbrowseOption(backupsetname, browseProxyClient)
        if retCode == False:
            self.msg = "the file format is wrong: " + input + " |set backupsetName browseProxyClient"
            return jobId

        for subclientnode in self.subclientList:
            if subclientnode["backupsetId"] == self.backupsetInfo["backupsetId"]:
                break;
        if subclientnode == None:
            self.msg = "did not get this backupset: %s  %s" % (clientName, backupsetname)
            return jobId

        lists = self.browse("\\" + vmGUID)
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

        if "Last" not in restoreTime and restoreTime != None and restoreTime != "":
            timeRange = root.findall(".//timeRange")
            for node in timeRange:
                toTimeValue = ET.Element('toTimeValue')
                toTimeValue.text = restoreTime
                node.append(toTimeValue)

        xmlString = ""
        xmlString = ET.tostring(root, encoding='utf-8', method='xml')
        if self.qCmd("QCommand/qoperation execute", xmlString):
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

    def restoreOracleBackupset(self, source, dest, operator):
        # param client is clientName or clientId
        # operator is {"instanceName":, "destClient":, "restoreTime":, "browseJobId":None}
        # return JobId
        # or -1 is error
        jobId = -1
        instance = self.backupsetInfo["instanceName"]
        if operator != None:
            keys = operator.keys()
            if "browseJobId" not in keys:
                self.msg = "operator - no browseJobId"
                return jobId
            if "data_path" not in keys:
                self.msg = "operator - no data_path"
                return jobId
            if "copy_priority" not in keys:
                self.msg = "operator - no copy_priority"
                return jobId
            if "db_open" not in keys:
                self.msg = "operator - no db_open"
                return jobId
            if "curSCN" not in keys:
                self.msg = "operator - no curSCN"
                return jobId
        else:
            self.msg = "param not set"
            return jobId

        sourceClient = source
        destClient = dest
        data_path = operator["data_path"]
        copy_priority = operator["copy_priority"]
        curSCN = operator["curSCN"] if operator["curSCN"] else ""
        db_open = operator["db_open"]
        restoreTime = operator["restoreTime"]
        log_restore = operator["log_restore"]

        if str(log_restore) == '1':
            log_restore = 'true'
        else:
            log_restore = 'false'

        try:
            copy_priority = int(copy_priority)
        except ValueError as e:
            copy_priority = 1

        try:
            db_open = int(db_open)
        except ValueError as e:
            db_open = 1

        if db_open == 2:
            db_open = "false"
        else:
            db_open = "true"

        copyPrecedence_xml = '''                                        
        <copyPrecedence>
            <copyPrecedenceApplicable>false</copyPrecedenceApplicable>
            <synchronousCopyPrecedence>1</synchronousCopyPrecedence>
            <copyPrecedence>0</copyPrecedence>
        </copyPrecedence>
        '''
        # 2:表示选择辅助拷贝优先
        if copy_priority == 2:
            copyPrecedence_xml = '''                                        
            <copyPrecedence>
                <copyPrecedenceApplicable>true</copyPrecedenceApplicable>
                <synchronousCopyPrecedence>2</synchronousCopyPrecedence>
                <copyPrecedence>2</copyPrecedence>
            </copyPrecedence>
            '''
        data_path_xml = '''
        <redirectItemsPresent>false</redirectItemsPresent>
        <validate>false</validate>
        <renamePathForAllTablespaces></renamePathForAllTablespaces>
        <redirectAllItemsSelected>false</redirectAllItemsSelected>
        '''
        if data_path:
            data_path_xml = '''
            <redirectItemsPresent>true</redirectItemsPresent>
            <validate>false</validate>
            <renamePathForAllTablespaces>{data_path}</renamePathForAllTablespaces>
            <redirectAllItemsSelected>true</redirectAllItemsSelected>
            '''.format(data_path=data_path)

        restoreoracleXML = '''
            <TMMsg_CreateTaskReq>
                <taskInfo>
                    <associations>
                        <appName>Oracle</appName>
                        <backupsetName>default</backupsetName>
                        <clientName>{sourceClient}</clientName>
                        <instanceName>{instance}</instanceName>
                        <subclientName>default</subclientName>
                    </associations>
                    <subTasks>
                        <options>
                            <backupOpts>
                                <backupLevel>INCREMENTAL</backupLevel>
                                <vsaBackupOptions/>
                            </backupOpts>
                            <commonOpts>
                                <!--User Description for the job-->
                                <jobDescription></jobDescription>
                                <prePostOpts>
                                    <postRecoveryCommand></postRecoveryCommand>
                                    <preRecoveryCommand></preRecoveryCommand>
                                    <runPostWhenFail>false</runPostWhenFail>
                                </prePostOpts>
                                <startUpOpts>
                                    <priority>166</priority>
                                    <startInSuspendedState>false</startInSuspendedState>
                                    <useDefaultPriority>true</useDefaultPriority>
                                </startUpOpts>
                            </commonOpts>
                            <restoreOptions>
                                <browseOption>
                                    <backupset>
                                        <backupsetName>default</backupsetName>
                                        <clientName>{sourceClient}</clientName>
                                    </backupset>
                                    <commCellId>2</commCellId>
                                    <listMedia>false</listMedia>
                                    <mediaOption>
                                        {copyPrecedence_xml}
                                        <drive/>
                                        <drivePool/>
                                        <library/>
                                        <mediaAgent/>
                                        <proxyForSnapClients>
                                            <clientName></clientName>
                                        </proxyForSnapClients>
                                    </mediaOption>
                                    <noImage>false</noImage>
                                    <timeRange/>
                                    <timeZone>
                                        <TimeZoneName>(UTC+08:00)&#x5317;&#x4eAC;&#xFF0C;&#x91CD;&#x5e86;&#xFF0C;&#x9999;&#x6e2F;&#x7279;&#x522B;&#x884C;&#x653F;&#x533A;&#xFF0C;&#x4e4C;&#x9C81;&#x6728;&#x9F50;</TimeZoneName>
                                    </timeZone>
                                    <useExactIndex>false</useExactIndex>
                                </browseOption>
                                <commonOptions>
                                    <clusterDBBackedup>false</clusterDBBackedup>
                                    <detectRegularExpression>true</detectRegularExpression>
                                    <ignoreNamespaceRequirements>false</ignoreNamespaceRequirements>
                                    <isDBArchiveRestore>false</isDBArchiveRestore>
                                    <isFromBrowseBackup>false</isFromBrowseBackup>
                                    <onePassRestore>false</onePassRestore>
                                    <recoverAllProtectedMails>false</recoverAllProtectedMails>
                                    <restoreDeviceFilesAsRegularFiles>false</restoreDeviceFilesAsRegularFiles>
                                    <restoreSpaceRestrictions>false</restoreSpaceRestrictions>
                                    <restoreToDisk>false</restoreToDisk>
                                    <revert>false</revert>
                                    <skipErrorsAndContinue>false</skipErrorsAndContinue>
                                    <useRmanRestore>true</useRmanRestore>
                                </commonOptions>
                                <destination>
                                    <destClient>
                                        <clientName>{destClient}</clientName>
                                    </destClient>
                                </destination>
                                <fileOption>
                                    <sourceItem>SID&#xFF1A; jxcredit</sourceItem>
                                </fileOption>
                                <oracleOpt>
                                    <SPFilePath></SPFilePath>
                                    <SPFileTime>
                                        <timeValue>{restoreTime}</timeValue>
                                    </SPFileTime>
                                    <archiveLog>false</archiveLog>
                                    <archiveLogBy>DEFAULT</archiveLogBy>
                                    <autoDetectDevice>true</autoDetectDevice>
                                    <backupValidationOnly>false</backupValidationOnly>
                                    <catalogConnect1></catalogConnect1>
                                    <catalogConnect2>
                                        <password>||#5!M2NmZTNlZWI4NTRlOGFhNjRlMDE1NWJlYzAxOTY3NGQ1&#xA;</password>
                                    </catalogConnect2>
                                    <catalogConnect3></catalogConnect3>
                                    <checkReadOnly>false</checkReadOnly>
                                    <cloneEnv>false</cloneEnv>
                                    <controlFilePath></controlFilePath>
                                    <controlFileTime>
                                        <timeValue>{restoreTime}</timeValue>
                                    </controlFileTime>
                                    <controleFileScript></controleFileScript>
                                    <ctrlBackupPiece></ctrlBackupPiece>
                                    <ctrlFileBackupType>AUTO_BACKUP</ctrlFileBackupType>
                                    <ctrlRestoreFrom>true</ctrlRestoreFrom>
                                    <customizeScript>false</customizeScript>
                                    <databaseScript></databaseScript>
                                    <dbIncarnation>0</dbIncarnation>
                                    <deviceType>UTIL_FILE</deviceType>
                                    <doNotRecoverRedoLogs>false</doNotRecoverRedoLogs>
                                    <duplicate>false</duplicate>
                                    <duplicateActiveDatabase>false</duplicateActiveDatabase>
                                    <duplicateNoFileNamecheck>false</duplicateNoFileNamecheck>
                                    <duplicateStandby>false</duplicateStandby>
                                    <duplicateStandbyDoRecover>false</duplicateStandbyDoRecover>
                                    <duplicateStandbySID></duplicateStandbySID>
                                    <duplicateTo>false</duplicateTo>
                                    <duplicateToLogFile>false</duplicateToLogFile>
                                    <duplicateToName></duplicateToName>
                                    <duplicateToOpenRestricted>false</duplicateToOpenRestricted>
                                    <duplicateToPFile></duplicateToPFile>
                                    <duplicateToSkipReadOnly>false</duplicateToSkipReadOnly>
                                    <duplicateToSkipTablespace>false</duplicateToSkipTablespace>
                                    <endLSNNum>1</endLSNNum>
                                    <isDeviceTypeSelected>false</isDeviceTypeSelected>
                                    <logTarget></logTarget>
                                    <logTime>
                                        <fromTimeValue></fromTimeValue>
                                        <toTimeValue>{restoreTime}</toTimeValue>
                                    </logTime>
                                    <maxOpenFiles>0</maxOpenFiles>
                                    <mountDatabase>false</mountDatabase>
                                    <noCatalog>true</noCatalog>
                                    <openDatabase>{db_open}</openDatabase>
                                    <osID>2</osID>
                                    <partialRestore>false</partialRestore>
                                    <recover>{log_restore}</recover>
                                    <recoverFrom>2</recoverFrom>
                                    <recoverSCN>{curSCN}</recoverSCN>
                                    <recoverTime>
                                        <timeValue>{restoreTime}</timeValue>
                                    </recoverTime>
                                    <redirectAllItemsSelected>false</redirectAllItemsSelected>
                                    {data_path_xml}
                                    <resetDatabase>false</resetDatabase>
                                    <resetLogs>1</resetLogs>
                                    <restoreByTag>false</restoreByTag>
                                    <restoreControlFile>true</restoreControlFile>
                                    <restoreData>true</restoreData>
                                    <restoreDataTag>false</restoreDataTag>
                                    <restoreFailover>false</restoreFailover>
                                    <restoreFrom>{restoreFrom}</restoreFrom>
                                    <restoreSPFile>false</restoreSPFile>
                                    <restoreStream>1</restoreStream>
                                    <restoreTablespace>false</restoreTablespace>
                                    <restoreTag></restoreTag>
                                    <restoreTime>
                                      <timeValue>{restoreTime}</timeValue>
                                    </restoreTime>
                                    <setDBId>true</setDBId>
                                    <skipTargetConnection>false</skipTargetConnection>
                                    <spFileBackupPiece></spFileBackupPiece>
                                    <spFileBackupType>AUTO_BACKUP</spFileBackupType>
                                    <spFileRestoreFrom>false</spFileRestoreFrom>
                                    <specifyControlFile>false</specifyControlFile>
                                    <specifyControlFileTime>false</specifyControlFileTime>
                                    <specifySPFile>false</specifySPFile>
                                    <specifySPFileTime>false</specifySPFileTime>
                                    <startLSNNum>1</startLSNNum>
                                    <switchDatabaseMode>false</switchDatabaseMode>
                                    <tableViewRestore>false</tableViewRestore>
                                    <tag></tag>
                                    <timeZone>
                                        <TimeZoneName>(UTC+08:00)&#x5317;&#x4eAC;&#xFF0C;&#x91CD;&#x5e86;&#xFF0C;&#x9999;&#x6e2F;&#x7279;&#x522B;&#x884C;&#x653F;&#x533A;&#xFF0C;&#x4e4C;&#x9C81;&#x6728;&#x9F50;</TimeZoneName>
                                    </timeZone>
                                    <useEndLSN>false</useEndLSN>
                                    <useEndLog>false</useEndLog>
                                    <useStartLSN>false</useStartLSN>
                                    <useStartLog>true</useStartLog>
                                </oracleOpt>
                                <volumeRstOption>
                                    <volumeLeveRestore>false</volumeLeveRestore>
                                </volumeRstOption>
                            </restoreOptions>
                        </options>
                        <subTask>
                            <operationType>RESTORE</operationType>
                            <subTaskType>RESTORE</subTaskType>
                        </subTask>
                    </subTasks>
                    <task>
                        <alert>
                            <alertName></alertName>
                        </alert>
                        <initiatedFrom>COMMANDLINE</initiatedFrom>
                        <policyType>DATA_PROTECTION</policyType>
                        <taskFlags>
                            <disabled>false</disabled>
                        </taskFlags>
                        <taskType>IMMEDIATE</taskType>
                    </task>
                </taskInfo>
            </TMMsg_CreateTaskReq>'''.format(sourceClient=sourceClient, destClient=destClient, instance=instance,
                                             restoreTime="{0:%Y-%m-%d %H:%M:%S}".format(restoreTime if restoreTime else
                                                                                        datetime.datetime.now()),
                                             copyPrecedence_xml=copyPrecedence_xml, data_path_xml=data_path_xml,
                                             curSCN=curSCN, db_open=db_open, restoreFrom='1' if restoreTime else '0',
                                             log_restore=log_restore)

        try:
            root = ET.fromstring(restoreoracleXML)
        except:
            self.msg = "Error:parse xml: " + restoreoracleXML
            return jobId

        xmlString = ""
        xmlString = ET.tostring(root, encoding='utf-8', method='xml')
        if self.qCmd("QCommand/qoperation execute", xmlString):
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

    def restoreOracleRacBackupset(self, source, dest, operator):
        # param client is clientName or clientId
        # operator is {"instanceName":, "destClient":, "restoreTime":, "browseJobId":None}
        # return JobId
        # or -1 is error
        jobId = -1
        instance = self.backupsetInfo["instanceName"]
        if operator != None:
            keys = operator.keys()
            if "browseJobId" not in keys:
                self.msg = "operator - no browseJobId"
                return jobId
            if "data_path" not in keys:
                self.msg = "operator - no data_path"
                return jobId
            if "copy_priority" not in keys:
                self.msg = "operator - no copy_priority"
                return jobId
            if "db_open" not in keys:
                self.msg = "operator - no db_open"
                return jobId
            if "curSCN" not in keys:
                self.msg = "operator - no curSCN"
                return jobId
            if "recover_time" not in keys:
                self.msg = "operator - no recover_time"
                return jobId
        else:
            self.msg = "param not set"
            return jobId

        sourceClient = source
        destClient = dest
        browseJobId = operator["browseJobId"]
        data_path = operator["data_path"]
        copy_priority = operator["copy_priority"]
        db_open = operator["db_open"]
        log_restore = operator["log_restore"]

        if str(log_restore) == '1':
            log_restore = 'true'
        else:
            log_restore = 'false'

        recover_time = operator["recover_time"]
        curSCN = operator["curSCN"] if operator["curSCN"] else ""

        try:
            copy_priority = int(copy_priority)
        except ValueError as e:
            copy_priority = 1

        try:
            db_open = int(db_open)
        except ValueError as e:
            db_open = 1

        if db_open == 2:
            db_open = "false"
        else:
            db_open = "true"

        copyPrecedence_xml = '''                                        
        <copyPrecedence>
            <copyPrecedenceApplicable>false</copyPrecedenceApplicable>
            <synchronousCopyPrecedence>1</synchronousCopyPrecedence>
            <copyPrecedence>0</copyPrecedence>
        </copyPrecedence>
        '''
        # 2:表示选择辅助拷贝优先
        if copy_priority == 2:
            copyPrecedence_xml = '''                                        
            <copyPrecedence>
                <copyPrecedenceApplicable>true</copyPrecedenceApplicable>
                <synchronousCopyPrecedence>2</synchronousCopyPrecedence>
                <copyPrecedence>2</copyPrecedence>
            </copyPrecedence>
            '''
        data_path_xml = '''
        <redirectItemsPresent>false</redirectItemsPresent>
        <renamePathForAllTablespaces></renamePathForAllTablespaces>
        <redirectAllItemsSelected>false</redirectAllItemsSelected>
        '''
        if data_path:
            data_path_xml = '''
            <redirectItemsPresent>true</redirectItemsPresent>
            <renamePathForAllTablespaces>{data_path}</renamePathForAllTablespaces>
            <redirectAllItemsSelected>true</redirectAllItemsSelected>
            '''.format(data_path=data_path)

        # OracleRac 根据recover_time来判断恢复最新事件还是根据curSCN号恢复
        if recover_time:
            recover_from = 1
        else:
            recover_from = 4
            curSCN = ""

        restoreoracleRacXML = '''
            <TMMsg_CreateTaskReq>
                <taskInfo>
                    <associations>
                        <appName>Oracle RAC</appName>
                        <backupsetName>defaultBackupSet</backupsetName>
                        <clientName>{sourceClient}</clientName>
                        <instanceName>{instance}</instanceName>
                        <subclientName>default</subclientName>
                    </associations>
                    <subTasks>
                        <options>
                            <backupOpts>
                                <backupLevel>INCREMENTAL</backupLevel>
                                <vsaBackupOptions/>
                            </backupOpts>
                            <commonOpts>
                                <!--User Description for the job-->
                                <jobDescription></jobDescription>
                                <startUpOpts>
                                    <priority>166</priority>
                                    <startInSuspendedState>false</startInSuspendedState>
                                    <useDefaultPriority>true</useDefaultPriority>
                                </startUpOpts>
                            </commonOpts>
                            <restoreOptions>
                                <browseOption>
                                    <backupset>
                                        <backupsetName>defaultBackupSet</backupsetName>
                                        <clientName>{sourceClient}</clientName>
                                    </backupset>
                                    <commCellId>2</commCellId>
                                    <listMedia>false</listMedia>
                                    <mediaOption>
                                        {copyPrecedence_xml}
                                        <drive/>
                                        <drivePool/>
                                        <library/>
                                        <mediaAgent/>
                                        <proxyForSnapClients>
                                            <clientName></clientName>
                                        </proxyForSnapClients>
                                    </mediaOption>
                                    <noImage>false</noImage>
                                    <timeRange/>
                                    <timeZone>
                                        <TimeZoneName>(UTC+08:00)&#x5317;&#x4eAC;&#xFF0C;&#x91CD;&#x5e86;&#xFF0C;&#x9999;&#x6e2F;&#x7279;&#x522B;&#x884C;&#x653F;&#x533A;&#xFF0C;&#x4e4C;&#x9C81;&#x6728;&#x9F50;</TimeZoneName>
                                    </timeZone>
                                    <useExactIndex>false</useExactIndex>
                                </browseOption>
                                <commonOptions>
                                    <clusterDBBackedup>false</clusterDBBackedup>
                                    <detectRegularExpression>true</detectRegularExpression>
                                    <ignoreNamespaceRequirements>false</ignoreNamespaceRequirements>
                                    <isDBArchiveRestore>false</isDBArchiveRestore>
                                    <isFromBrowseBackup>false</isFromBrowseBackup>
                                    <onePassRestore>false</onePassRestore>
                                    <recoverAllProtectedMails>false</recoverAllProtectedMails>
                                    <restoreDeviceFilesAsRegularFiles>false</restoreDeviceFilesAsRegularFiles>
                                    <restoreSpaceRestrictions>false</restoreSpaceRestrictions>
                                    <restoreToDisk>false</restoreToDisk>
                                    <revert>false</revert>
                                    <skipErrorsAndContinue>false</skipErrorsAndContinue>
                                    <useRmanRestore>true</useRmanRestore>
                                </commonOptions>
                                <destination>
                                    <destClient>
                                        <clientName>{destClient}</clientName>
                                    </destClient>
                                    <destinationInstance>
                                        <appName>Oracle</appName>
                                        <clientName>{destClient}</clientName>
                                        <instanceName>{instance}</instanceName>
                                    </destinationInstance>
                                </destination>
                                <fileOption>
                                    <sourceItem>SID&#xFF1A; zfxtora</sourceItem>
                                </fileOption>
                                <oracleOpt>
                                    <SPFilePath></SPFilePath>
                                    <SPFileTime>
                                        <timeValue>{restoreTime}</timeValue>
                                    </SPFileTime>
                                    <archiveLog>false</archiveLog>
                                    <archiveLogBy>DEFAULT</archiveLogBy>
                                    <autoDetectDevice>true</autoDetectDevice>
                                    <backupValidationOnly>false</backupValidationOnly>
                                    <catalogConnect1></catalogConnect1>
                                    <catalogConnect2>
                                        <password>||#5!M2NmZTNlZWI4NTRlOGFhNjRlMDE1NWJlYzAxOTY3NGQ1&#xA;</password>
                                    </catalogConnect2>
                                    <catalogConnect3></catalogConnect3>
                                    <checkReadOnly>false</checkReadOnly>
                                    <cloneEnv>false</cloneEnv>
                                    <controlFilePath></controlFilePath>
                                    <controlFileTime>
                                        <timeValue>{restoreTime}</timeValue>
                                    </controlFileTime>
                                    <controleFileScript></controleFileScript>
                                    <ctrlBackupPiece></ctrlBackupPiece>
                                    <ctrlFileBackupType>AUTO_BACKUP</ctrlFileBackupType>
                                    <ctrlRestoreFrom>true</ctrlRestoreFrom>
                                    <customizeScript>false</customizeScript>
                                    <databaseScript></databaseScript>
                                    <dbIncarnation>0</dbIncarnation>
                                    <deviceType>UTIL_FILE</deviceType>
                                    <doNotRecoverRedoLogs>false</doNotRecoverRedoLogs>
                                    <duplicate>false</duplicate>
                                    <duplicateActiveDatabase>false</duplicateActiveDatabase>
                                    <duplicateNoFileNamecheck>false</duplicateNoFileNamecheck>
                                    <duplicateStandby>false</duplicateStandby>
                                    <duplicateStandbyDoRecover>false</duplicateStandbyDoRecover>
                                    <duplicateStandbySID></duplicateStandbySID>
                                    <duplicateTo>false</duplicateTo>
                                    <duplicateToLogFile>false</duplicateToLogFile>
                                    <duplicateToName></duplicateToName>
                                    <duplicateToOpenRestricted>false</duplicateToOpenRestricted>
                                    <duplicateToPFile></duplicateToPFile>
                                    <duplicateToSkipReadOnly>false</duplicateToSkipReadOnly>
                                    <duplicateToSkipTablespace>false</duplicateToSkipTablespace>
                                    <endLSNNum>1</endLSNNum>
                                    <isDeviceTypeSelected>false</isDeviceTypeSelected>
                                    <logTarget></logTarget>
                                    <logTime>
                                        <fromTimeValue>{restoreTime}</fromTimeValue>
                                        <toTimeValue>{restoreTime}</toTimeValue>
                                    </logTime>
                                    <maxOpenFiles>0</maxOpenFiles>
                                    <mountDatabase>false</mountDatabase>
                                    <noCatalog>true</noCatalog>
                                    <openDatabase>{db_open}</openDatabase>
                                    <osID>2</osID>
                                    <partialRestore>false</partialRestore>
                                    <racDataStreamAllcation>1 0</racDataStreamAllcation>
                                    <racDataStreamAllcation>2 0</racDataStreamAllcation>
                                    <recover>{log_restore}</recover>
                                    <recoverFrom>{recover_from}</recoverFrom>
                                    <recoverSCN>{curSCN}</recoverSCN>
                                    <recoverTime>
                                        <timeValue>{restoreTime}</timeValue>
                                    </recoverTime>
                                    {data_path_xml}
                                    <resetDatabase>false</resetDatabase>
                                    <resetLogs>1</resetLogs>
                                    <restoreByTag>false</restoreByTag>
                                    <restoreControlFile>true</restoreControlFile>
                                    <restoreData>true</restoreData>
                                    <restoreDataTag>false</restoreDataTag>
                                    <restoreFailover>false</restoreFailover>
                                    <restoreFrom>{restoreFrom}</restoreFrom>
                                    <restoreInstanceLog>false</restoreInstanceLog>
                                    <restoreSPFile>false</restoreSPFile>
                                    <restoreStream>1</restoreStream>
                                    <restoreTablespace>false</restoreTablespace>
                                    <restoreTag></restoreTag>
                                    <restoreTime>
                                        <timeValue>2020-03-19 13:33:39</timeValue>
                                    </restoreTime>
                                    <setDBId>true</setDBId>
                                    <skipTargetConnection>false</skipTargetConnection>
                                    <spFileBackupPiece></spFileBackupPiece>
                                    <spFileBackupType>AUTO_BACKUP</spFileBackupType>
                                    <spFileRestoreFrom>false</spFileRestoreFrom>
                                    <specifyControlFile>false</specifyControlFile>
                                    <specifyControlFileTime>false</specifyControlFileTime>
                                    <specifySPFile>false</specifySPFile>
                                    <specifySPFileTime>false</specifySPFileTime>
                                    <startLSNNum>1</startLSNNum>
                                    <switchDatabaseMode>false</switchDatabaseMode>
                                    <tableViewRestore>false</tableViewRestore>
                                    <tag></tag>
                                    <threadId>1</threadId>
                                    <timeZone>
                                        <TimeZoneName>(UTC+08:00)&#x5317;&#x4eAC;&#xFF0C;&#x91CD;&#x5e86;&#xFF0C;&#x9999;&#x6e2F;&#x7279;&#x522B;&#x884C;&#x653F;&#x533A;&#xFF0C;&#x4e4C;&#x9C81;&#x6728;&#x9F50;</TimeZoneName>
                                    </timeZone>
                                    <useEndLSN>false</useEndLSN>
                                    <useEndLog>false</useEndLog>
                                    <useStartLSN>false</useStartLSN>
                                    <useStartLog>true</useStartLog>
                                    <validate>false</validate>
                                </oracleOpt>
                                <volumeRstOption>
                                    <volumeLeveRestore>false</volumeLeveRestore>
                                </volumeRstOption>
                            </restoreOptions>
                        </options>
                        <subTask>
                            <operationType>RESTORE</operationType>
                            <subTaskType>RESTORE</subTaskType>
                        </subTask>
                    </subTasks>
                    <task>
                        <alert>
                            <alertName></alertName>
                        </alert>
                        <initiatedFrom>COMMANDLINE</initiatedFrom>
                        <policyType>DATA_PROTECTION</policyType>
                        <taskFlags>
                            <disabled>false</disabled>
                        </taskFlags>
                        <taskType>IMMEDIATE</taskType>
                    </task>
                </taskInfo>
            </TMMsg_CreateTaskReq>'''.format(sourceClient=sourceClient, destClient=destClient, instance=instance,
                                             restoreTime="{0:%Y-%m-%d %H:%M:%S}".format(
                                                 recover_time if recover_time else datetime.datetime.now()),
                                             copyPrecedence_xml=copyPrecedence_xml, data_path_xml=data_path_xml,
                                             curSCN=curSCN, db_open=db_open, recover_from=recover_from,
                                             restoreFrom="1" if recover_time else "0", log_restore=log_restore)

        try:
            root = ET.fromstring(restoreoracleRacXML)
        except:
            self.msg = "Error:parse xml: " + restoreoracleRacXML
            return jobId

        xmlString = ""
        xmlString = ET.tostring(root, encoding='utf-8', method='xml')
        if self.qCmd("QCommand/qoperation execute", xmlString):
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

    def restoreMssqlBackupset(self, source, dest, operator):
        # param client is clientName or clientId
        # operator is {"instanceName":, "destClient":, "restoreTime":, "restorePath":None}
        # return JobId
        # or -1 is error
        jobId = -1
        instance = self.backupsetInfo["instanceName"]
        if operator != None:
            keys = operator.keys()
            if "restoreTime" not in keys:
                self.msg = "operator - no restoreTime"
                return jobId
            if "overWrite" not in keys:
                self.msg = "operator - no overWrite"
                return jobId
        else:
            self.msg = "param not set"
            return jobId

        restoremssqlXML = '''
            <TMMsg_CreateTaskReq>
              <taskInfo>
                <associations>
                  <appName>SQL Server</appName>
                  <backupsetName>defaultBackupSet</backupsetName>
                  <clientName></clientName>
                  <clientSidePackage>true</clientSidePackage>
                  <consumeLicense>true</consumeLicense>
                  <instanceName></instanceName>
                  <subclientName></subclientName>
                  <type>GALAXY</type>
                </associations>
                <subTasks>
                  <options>
                    <adminOpts>
                      <contentIndexingOption>
                        <subClientBasedAnalytics>false</subClientBasedAnalytics>
                      </contentIndexingOption>
                    </adminOpts>
                    <restoreOptions>
                      <browseOption>
                        <backupset>
                          <backupsetName>defaultBackupSet</backupsetName>
                          <clientName></clientName>
                        </backupset>
                        <commCellId>2</commCellId>
                        <listMedia>false</listMedia>
                        <mediaOption>
                          <copyPrecedence>
                            <copyPrecedenceApplicable>false</copyPrecedenceApplicable>
                          </copyPrecedence>
                          <drivePool/>
                          <library/>
                          <mediaAgent/>
                        </mediaOption>
                        <noImage>false</noImage>
                        <timeRange/>
                        <timeZone>
                          <TimeZoneName>(GMT+08:00) &#x5317;&#x4eAC;&#xFF0C;&#x91CD;&#x5e86;&#xFF0C;&#x9999;&#x6e2F;&#x7279;&#x522B;&#x884C;&#x653F;&#x533A;&#xFF0C;&#x4e4C;&#x9C81;&#x6728;&#x9F50;</TimeZoneName>
                        </timeZone>
                        <useExactIndex>false</useExactIndex>
                      </browseOption>
                      <commonOptions>
                        <clusterDBBackedup>false</clusterDBBackedup>
                        <isDBArchiveRestore>false</isDBArchiveRestore>
                        <onePassRestore>false</onePassRestore>
                        <restoreToDisk>false</restoreToDisk>
                      </commonOptions>
                      <destination>
                        <destClient>
                          <clientName></clientName>
                        </destClient>
                        <destinationInstance>
                          <appName>SQL Server</appName>
                          <clientName></clientName>
                          <instanceName></instanceName>
                        </destinationInstance>
                      </destination>
                      <fileOption/>
                      <sharePointRstOption>
                        <fetchSqlDatabases>false</fetchSqlDatabases>
                      </sharePointRstOption>
                      <sqlServerRstOption>
                        <attachToSQLServer>false</attachToSQLServer>
                        <checksum>false</checksum>
                        <commonMountPath></commonMountPath>
                        <continueaftererror>false</continueaftererror>
                        <restoreSource>master</restoreSource>
                        <restoreSource>cvtest</restoreSource>
                        <restoreSource>msdb</restoreSource>
                        <restoreSource>model</restoreSource>
                        <database>master</database>
                        <database>cvtest</database>
                        <database>msdb</database>
                        <database>model</database>
                        <dbOnly>false</dbOnly>
                        <dropConnectionsToDatabase>false</dropConnectionsToDatabase>
                        <ffgRestore>false</ffgRestore>
                        <ignoreFullBackup>false</ignoreFullBackup>
                        <keepDataCapture>false</keepDataCapture>
                        <logShippingOnly>false</logShippingOnly>
                        <overWrite></overWrite>
                        <partialRestore>false</partialRestore>
                        <pointOfTimeRst>false</pointOfTimeRst>
                        <preserveReplicationSettings>false</preserveReplicationSettings>
                        <restoreToDisk>false</restoreToDisk>
                        <restoreToDiskPath></restoreToDiskPath>
                        <snapOopStageFolder></snapOopStageFolder>
                        <sqlRecoverType>STATE_RECOVER</sqlRecoverType>
                        <sqlRestoreType>DATABASE_RESTORE</sqlRestoreType>
                        <sqlVerifyOnly>false</sqlVerifyOnly>
                        <stopBeforeMarkRestore>false</stopBeforeMarkRestore>
                        <stopMarkRestore>false</stopMarkRestore>
                        <stopStartSSA>false</stopStartSSA>
                        <timeZone>
                          <TimeZoneName>(GMT+08:00) &#x5317;&#x4eAC;&#xFF0C;&#x91CD;&#x5e86;&#xFF0C;&#x9999;&#x6e2F;&#x7279;&#x522B;&#x884C;&#x653F;&#x533A;&#xFF0C;&#x4e4C;&#x9C81;&#x6728;&#x9F50;</TimeZoneName>
                        </timeZone>
                        <vSSBackup>true</vSSBackup>
                      </sqlServerRstOption>
                      <virtualServerRstOption>
                        <isBlockLevelReplication>false</isBlockLevelReplication>
                      </virtualServerRstOption>
                    </restoreOptions>
                  </options>
                  <subTask>
                    <operationType>RESTORE</operationType>
                    <subTaskType>RESTORE</subTaskType>
                  </subTask>
                </subTasks>
                <task>
                  <initiatedFrom>COMMANDLINE</initiatedFrom>
                  <policyType>DATA_PROTECTION</policyType>
                  <taskFlags>
                    <disabled>false</disabled>
                  </taskFlags>
                  <taskType>IMMEDIATE</taskType>
                </task>
              </taskInfo>

            </TMMsg_CreateTaskReq>'''

        try:
            root = ET.fromstring(restoremssqlXML)
        except:
            self.msg = "Error:parse xml: " + restoremssqlXML
            return jobId

        sourceClient = source
        destClient = dest
        # instance = operator["instanceName"]
        restoreTime = operator["restoreTime"]
        overWrite = operator["overWrite"]
        try:
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
            destInstanceclient = root.findall(".//destinationInstance/clientName")
            for node in destInstanceclient:
                node.text = destClient
                break
            destInstanceName = root.findall(".//destinationInstance/instanceName")
            for node in destInstanceName:
                node.text = instance
                break
            if "Last" not in restoreTime and restoreTime != None and restoreTime != "":
                timeRange = root.findall(".//timeRange")
                for node in timeRange:
                    toTimeValue = ET.Element('toTimeValue')
                    toTimeValue.text = restoreTime
                    node.append(toTimeValue)
        except:
            self.msg = "the file format is wrong"
            return jobId

        xmlString = ""
        xmlString = ET.tostring(root, encoding='utf-8', method='xml')
        if self.qCmd("QCommand/qoperation execute", xmlString):
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
        list = info.getClientList()
        self.msg = info.msg
        return list

    def getClientInfo(self, client):
        clientInfo = CV_Client(self.token)
        info = clientInfo.getClientInfo(client)
        self.msg = clientInfo.msg
        return info

    def setVMWareClient(self, clientName, vmClient):
        client = CV_Client(self.token, clientName)
        # print(client.clientInfo)
        retCode = client.setVMWareClient(clientName, vmClient)
        self.msg = client.msg
        return retCode

    def delVMWareClient(self, client):
        # param client is clientName or clientId
        # return True / False
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

    def getBackupset(self, client, agentType, backupset=None):
        # param client is clientName or clientId
        # param backupset is backupsetName or backupsetId
        # return backupset info backupset
        # None is no backupset
        info = CV_Backupset(self.token, client, agentType)
        backupsetInfo = info.getBackupset(agentType, backupset)
        self.msg = info.msg
        return backupsetInfo

    def getSubclientInfo(self, subclientId):
        # param client is clientName or clientId
        # param backupset is backupsetName or backupsetId
        # return backupset info backupset
        # None is no backupset
        clientInfo = CV_Client(self.token)
        return clientInfo.getSubclientInfo(subclientId)

    def setFSBackupset(self, client, backupset, content=None):
        # param client is clientName or clientId
        # backupset is backupsetName or backupsetId
        # content is  FSBackupset {"SPName":, "Schdule":, "Paths":["", ""], "OS":True/False}
        # return True / False
        fsBackupset = CV_Backupset(self.token, client, "File System", backupset)
        if fsBackupset.getIsNewClient() == True:
            self.msg = "there is not this fs Client " + client
            return False
        # print(fsBackupset.backupsetInfo)
        retCode = fsBackupset.setFSBackupset(backupset, content)
        self.msg = fsBackupset.msg
        return retCode

    def setVMWareBackupset(self, client, backupset, content=None):
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

    def setOracleBackupset(self, client, instanceName, credit, content=None):
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

    def setMssqlBackupset(self, client, instanceName, credit=None, content=None):
        # param client is clientName or clientId
        # backupset is backupsetName or backupsetId
        # credit is {"instanceName":,"Server":, "userName":, "passwd":, SPName":, "useVss":True/False}
        # content is {"SPName":, "Schdule":}
        # return True / False
        mssqlBackupset = CV_Backupset(self.token, client, "SQL Server", instanceName)
        if mssqlBackupset.getIsNewClient() == True:
            self.msg = "there is not this mssql Client " + client
            return False
        retCode = mssqlBackupset.setMssqlBackupset(instanceName, credit, content)
        self.msg = mssqlBackupset.msg
        return retCode

    def browse(self, client, agentType, backupset, path, showDeleted=False):
        # param client is clientName or clientId
        # backupset is backupsetName or backupsetId
        # operator is {"destClient":, "restoreTime":, "destPath":, "Path":, "overwrite":True/False, "OS Restore": True/False}
        # return JobId
        # or -1 is error
        cvBackupset = CV_Backupset(self.token, client, agentType, backupset)
        if cvBackupset.getIsNewClient() == True:
            self.msg = "there is not this Client " + str(client)
            return None
        if cvBackupset.getIsNewBackupset() == True:
            self.msg = "there is not this backupset " + backupset
            return None
        list = cvBackupset.browse(path)
        self.msg = cvBackupset.msg
        return list

    def restoreFSBackupset(self, source, dest, backupset, operator=None):
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
        self.msg = sourceClient.msg
        return retCode

    def restoreOracleBackupset(self, source, dest, instance, operator=None):
        # param client is clientName or clientId
        # operator is {"instanceName":, "destClient":, "restoreTime":, "restorePath":None}
        # return JobId
        # or -1 is error

        # print(client, backupset, credit, content)
        sourceBackupset = CV_Backupset(self.token, source, "Oracle Database", instance)
        destBackupset = CV_Backupset(self.token, dest, "Oracle Database", instance)
        if sourceBackupset.getIsNewBackupset() == True:
            self.msg = "there is not this oracle sid " + source
            return False
        jobId = sourceBackupset.restoreOracleBackupset(source, dest, operator)
        self.msg = sourceBackupset.msg
        return jobId

    def restoreOracleRacBackupset(self, source, dest, instance, operator=None):
        # param client is clientName or clientId
        # operator is {"instanceName":, "destClient":, "restoreTime":, "browseJobId":None}
        # return JobId
        # or -1 is error

        # print(client, backupset, credit, content)
        sourceBackupset = CV_Backupset(self.token, source, "Oracle RAC", instance)
        destBackupset = CV_Backupset(self.token, dest, "Oracle RAC", instance)
        if sourceBackupset.getIsNewBackupset() == True:
            self.msg = "there is not this oracle rac sid" + source
            return False

        jobId = sourceBackupset.restoreOracleRacBackupset(source, dest, operator)
        self.msg = sourceBackupset.msg
        return jobId

    def restoreMssqlBackupset(self, source, dest, instance, operator=None):
        # param client is clientName or clientId
        # operator is {"instanceName":, "destClient":, "restoreTime":, "restorePath":None}
        # return JobId
        # or -1 is error

        # print(client, backupset, credit, content)
        sourceBackupset = CV_Backupset(self.token, source, "SQL Server", instance)
        destBackupset = CV_Backupset(self.token, dest, "SQL Server", instance)
        if sourceBackupset.getIsNewBackupset() == True:
            self.msg = "there is not this mssql sid " + source
            return False
        if destBackupset.getIsNewBackupset() == True:
            self.msg = "there is not this mssql sid " + dest
            return False
        jobId = sourceBackupset.restoreMssqlBackupset(source, dest, operator)
        self.msg = sourceBackupset.msg
        return jobId

    def restoreVMWareBackupset(self, source, dest, backupset=None, operator=None):
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

    def getJobList(self, client, agentType=None, backupset=None, type="backup"):
        # param client is clientName or clientId or None is all client
        # param agentType =
        # backupset is backsetupName or backsetupId
        # operator is backup, restore, admin and others
        # return job List, {"jobID":, "clientName":, "clientId":, "Start":, "End":, }
        # None is no job
        joblist = []
        jobRec = {}
        info = CV_GetAllInformation(self.token)
        clientRec = CV_Client(self.token, client)
        list = info.getJobList(clientId=clientRec.clientInfo["clientId"], type=type, appTypeName=agentType,
                               backupsetName=backupset, subclientName=None, start=None, end=None)

        for node in list:
            jobRec["jobId"] = node["jobId"]
            jobRec["status"] = node["status"]
            jobRec["client"] = clientRec.clientInfo["clientName"]
            jobRec["agentType"] = node["appTypeName"]
            jobRec["backupSetName"] = node["backupSetName"]
            # jobRec["destClient"] = node["destClientName"]
            jobRec["jobType"] = node["jobType"]
            jobRec["Level"] = node["backupLevel"]
            # 流量
            jobRec["appSize"] = node["sizeOfApplication"]
            # 磁盘容量
            jobRec["diskSize"] = node["sizeOfMediaOnDisk"]
            jobRec["StartTime"] = node["jobStartTime"]
            jobRec["LastTime"] = node["lastUpdateTime"]
            joblist.append(copy.deepcopy(jobRec))
        self.msg = info.msg
        return joblist

    def getSPList(self):
        # return SPNameList, {"SPName":, "SPId":}
        spList = []
        sp = {"SPName": None, "SPId": None}
        info = CV_GetAllInformation(self.token)
        list = info.getSPList()
        for node in list:
            sp["SPName"] = node["storagePolicyName"]
            sp["SPId"] = node["storagePolicyId"]
            spList.append(copy.deepcopy(sp))
        self.msg = info.msg
        return spList

    def getSchduleList(self):
        # return schdulelist, {"SchduleName":, "SchduleId":}
        schduleList = []
        schdule = {"SchduleName": None, "SchduleId": None}
        info = CV_GetAllInformation(self.token)
        list = info.getSchduleList()
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

        vmRec = {"VMName": None, "VMGuID": None}
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


class DoMysql(object):
    # 初始化
    def __init__(self, host, user, password, db):
        # 创建连接
        self.conn = pymysql.Connect(
            host=host,
            port=3306,
            user=user,
            password=password,
            db=db,
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor  # 以字典的形式返回数据
        )
        # 获取游标
        self.cursor = self.conn.cursor()

    # 返回多条数据
    def fetchAll(self, sql):
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    # 返回一条数据
    def fetchOne(self, sql):
        self.cursor.execute(sql)
        return self.cursor.fetchone()

    # 插入一条数据
    def insert_one(self, sql):
        result = self.cursor.execute(sql)
        self.conn.commit()
        return result

    # 插入多条数据
    def insert_many(self, sql, datas):
        result = self.cursor.executemany(sql, datas)
        self.conn.commit()
        return result

    # 更新数据
    def update(self, sql):
        result = self.cursor.execute(sql)
        self.conn.commit()
        return result

    # 关闭连接
    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


def run(origin, target, instance, processrun_id):
    #############################################
    # 从config/db_config.xml中读取数据库认证信息 #
    #############################################
    db_host, db_name, db_user, db_password = '', '', '', ''

    try:
        db_config_file = os.path.join(os.path.join(os.path.join(os.getcwd(), "faconstor"), "config"), "db_config.xml")
        with open(db_config_file, "r") as f:
            content = etree.XML(f.read())
            db_config = content.xpath('./DB_CONFIG')
            if db_config:
                db_config = db_config[0]
                db_host = db_config.attrib.get("db_host", "")
                db_name = db_config.attrib.get("db_name", "")
                db_user = db_config.attrib.get("db_user", "")
                db_password = db_config.attrib.get("db_password", "")
    except Exception as e:
        print("获取数据库信息失败。", e)
        exit(1)

    db = DoMysql(db_host, db_user, db_password, db_name)

    credit_result = {}
    recovery_result = {}

    credit_sql = "SELECT t.content FROM {db_name}.faconstor_vendor t;".format(**{"db_name": db_name})
    recovery_sql = """SELECT recover_time, browse_job_id, data_path, copy_priority, curSCN, db_open, recover_end_time, log_restore FROM {db_name}.faconstor_processrun
                      WHERE state!='9' AND id={processrun_id};""".format(
        **{"processrun_id": processrun_id, "db_name": db_name})

    try:
        credit_result = db.fetchOne(credit_sql)
        recovery_result = db.fetchOne(recovery_sql)
    except:
        pass

    db.close()
    browse_job_id = ""
    data_path = ""
    copy_priority = ""
    curSCN = ""
    recover_time = ""
    recover_end_time = ""
    db_open = ""
    log_restore = 2

    if recovery_result:
        browse_job_id = recovery_result["browse_job_id"]
        data_path = recovery_result["data_path"]
        copy_priority = recovery_result["copy_priority"]
        db_open = recovery_result["db_open"]
        curSCN = recovery_result["curSCN"]
        recover_time = recovery_result["recover_time"]
        recover_end_time = recovery_result["recover_end_time"]
        log_restore = recovery_result["log_restore"]

    webaddr = ""
    port = ""
    usernm = ""
    passwd = ""
    if credit_result:
        doc = parseString(credit_result["content"])
        try:
            webaddr = (doc.getElementsByTagName("webaddr"))[0].childNodes[0].data
        except:
            pass
        try:
            port = (doc.getElementsByTagName("port"))[0].childNodes[0].data
        except:
            pass
        try:
            usernm = (doc.getElementsByTagName("username"))[0].childNodes[0].data
        except:
            pass
        try:
            passwd = (doc.getElementsByTagName("passwd"))[0].childNodes[0].data
        except:
            pass

    info = {
        "webaddr": webaddr,
        "port": port,
        "username": usernm,
        "passwd": passwd,
        "token": "",
        "last_login": 0
    }

    cvToken = CV_RestApi_Token()
    cvToken.login(info)
    cvAPI = CV_API(cvToken)

    jobId = cvAPI.restoreOracleRacBackupset(origin, target, instance,
                                            {'browseJobId': browse_job_id, 'data_path': data_path,
                                             "copy_priority": copy_priority, "curSCN": curSCN,
                                             "db_open": db_open, "recover_time": recover_time,
                                             "recover_end_time": recover_end_time, "log_restore": log_restore})
    # jobId = 4553295
    if jobId == -1:
        print("oracleRac恢复接口调用失败。")
        exit(1)
    else:
        temp_tag = 0
        waiting_times = 0

        while True:
            ret = []
            try:
                ret = cvAPI.getJobList(origin, type="restore")
            except:
                temp_tag += 1
            for i in ret:
                if str(i["jobId"]) == str(jobId):
                    if i['status'] in ['运行']:
                        break
                    elif i['status'] in ['等待', '未决']:
                        if waiting_times > 450:
                            print(jobId)
                            exit(2)
                        waiting_times += 1
                        break
                    elif i['status'].upper() == '完成':
                        exit(0)
                    else:
                        # oracle恢复出现异常
                        #################################
                        # 程序中不要出现其他print()      #
                        # print()将会作为输出被服务器获取#
                        #################################
                        print(jobId)
                        exit(2)
            # 长时间未获取到Commvault状态，请检查Commvault恢复情况。
            if temp_tag > 100:
                exit(3)
            time.sleep(4)


if len(sys.argv) == 5:
    run(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
else:
    print("脚本传参出现异常。")
    exit(1)
