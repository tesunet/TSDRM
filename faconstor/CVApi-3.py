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
import base64, traceback
from xml.etree.ElementTree import ElementTree

CV_APPLICATION_WORDS = {"41": "Active Directory",
                        "21": "AIX File System",
                        "134": "Cloud Apps",
                        "37": "DB2",
                        "103": "DB2 MultiNode",
                        "62": "DB2 on Unix",
                        "64": "Distributed Apps",
                        "128": "Documentum",
                        "90": "Domino Mailbox Archiver",
                        "91": "DPM",
                        "67": "Exchange Compliance Archiver",
                        "53": "Exchange Database",
                        "45": "Exchange Mailbox",
                        "54": "Exchange Mailbox (Classic)",
                        "56": "Exchange Mailbox Archiver",
                        "82": "Exchange PF Archiver",
                        "35": "Exchange Public Folder",
                        "73": "File Share Archiver",
                        "33": "Windows File System",
                        "74": "FreeBSD",
                        "71": "GroupWise DB",
                        "17": "HP-UX Files System",
                        "65": "Image Level",
                        "75": "Image Level On Unix",
                        "76": "Image Level ProxyHost",
                        "87": "Image Level ProxyHost on Unix",
                        "3": "Informix Database",
                        "29": "Linux File System",
                        "89": "MS SharePoint Archiver",
                        "104": "MySQL",
                        "13": "NAS",
                        "83": "Netware File Archiver",
                        "12": "Netware File System",
                        "10": "Novell Directory Services",
                        "124": "Object Link",
                        "131": "Object Store",
                        "86": "OES File System on Linux",
                        "22": "Oracle",
                        "80": "Oracle RAC",
                        "130": "Other External Agent",
                        "125": "PostgreSQL",
                        "38": "Proxy Client File System",
                        "87": "ProxyHost on Unix",
                        "61": "SAP for Oracle",
                        "135": "SAP HANA",
                        "78": "SharePoint Server",
                        "20": "Solaris 64bit File System",
                        "19": "Solaris File System",
                        "81": "SQL Server",
                        "5": "Sybase Database",
                        "66": "Unix File Archiver",
                        "36": "Unix Tru64 64-bit File System",
                        "106": "Virtual Server",
                        "58": "Windows File Archiver",
                        "43": "Windows 2003 64-bit File System",
                        "84": "Continuous Data Replicator",
                        }


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
        self.dumpFile = "dump.txt"

    def _err_msg(self, errno):
        return

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
            self.msg = 'Failure: webaddr ' + self.webaddr + " port " + self.port + " retcode: %d" % r.status_code

        return self.receiveText

    def getCmd(self, command, updatecmd=""):
        """
        Constructor 
        get command function
        """
        retString = self._rest_cmd("GET", command, updatecmd)
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
                return True
            else:
                try:
                    errString = node.attrib["errorString"]
                    self.msg = "PostCmd:" + command + "ErrCode: " + errorCode + "ErrString:" + errString
                except:
                    self.msg = "post command:" + command + " Error Code: " + errorCode + " receive text is " + self.receiveText
                    pass
            return False
        except:
            self.msg = "receive string is not XML format:" + self.receiveText
            return False

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
                return True
            self.msg = "del command:" + command + " xml format:" + updatecmd + " Error Code: " + errorCode + " receive text is " + self.receiveText
            return False
        except:
            self.msg = "receive string is not XML format:" + self.receiveText
            return False

    def qCmd(self, command, updatecmd=""):
        """
        Constructor 
        get command function
        """
        retString = self._rest_cmd("QCMD", command, updatecmd)
        try:
            respRoot = ET.fromstring(retString)
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

    def dump(self, operator=None, addtxt=None, append=False):
        if append == True:
            fh = open(self.dumpFile, "w+")
        else:
            fh = open(self.dumpFile, "w")
        if fh == None:
            return False
        if operator == "Receive":
            fh.write(self.receiveText)
        if operator == "Send":
            fh.write(self.sendText)
        if operator == "msg":
            fh.write(self.msg)
        if operator == None:
            fh.write(self.receiveText)
            fh.write(self.sendText)
            fh.write(self.msg)
        fh.close()
        return True


class CV_GetAllInformation(CV_RestApi):
    """
        class CV_getAllInformation is get total information class
        include client, subclient, storagePolice, schdule, JobList
        spList = {"storagePolicyId", "storagePolicyName"}
        schduleList = {"taskName", "associatedObjects", "taskType", "runUserId", "taskId", "ownerId", "description", "ownerName", "policyType", "GUID", "alertId"}
        clientList = {"clientId", "clientName", "_type_"}
        backupsetList = {}

        getSPlist return storage Police list
        getSchduleList return schdule List
        getClientList return client List
        getJobList return job list

        """

    def __init__(self, token):
        super(CV_GetAllInformation, self).__init__(token)
        self.SPList = []
        self.SchduleList = []
        self.clientList = []
        self.JobList = []
        self.pseudoClientList = []
        return

    def getSPList(self):
        del self.SPList[:]
        returnXML = self.getCmd('StoragePolicy')
        if returnXML == None:
            return None

        activePhysicalNode = returnXML.findall(".//policies")
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
        clientList = self._getClientList()
        pseudoList = self._getPseudoClient()
        for node in clientList:
            for item in pseudoList:
                if node["clientId"] == item["clientId"]:
                    node["clientType"] = item["clientType"]
        return self.clientList

    def _getClientList(self):
        del self.clientList[:]
        clientRec = {"clientName": None, "clientId": ""}
        resp = self.getCmd('/Client')
        if resp == None:
            return None

        activePhysicalNode = resp.findall(".//clientEntity")
        for node in activePhysicalNode:
            rec = copy.deepcopy(clientRec)
            rec["clientName"] = node.attrib["clientName"]
            rec["clientType"] = "Physical"
            try:
                rec["clientId"] = int(node.attrib["clientId"])
            except:
                pass
            self.clientList.append(rec)
        return self.clientList

    def getJobList(self, clientId, type="backup", appTypeName=None, backupsetName=None, subclientName=None, start=None,
                   end=None):
        statusList = {"Running": "运行", "Waiting": "等待", "Pending": "阻塞", "Suspend": "终止", "commpleted": "完成",
                      "Failed": "失败", "Failed to Start": "启动失败", "Killed": "杀掉"}
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
        del self.JobList[:]
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

        # print(self.receiveText)
        activePhysicalNode = client.findall(".//jobs/jobSummary")
        for node in activePhysicalNode:
            # if start != None:
            # if end != None:
            # print(node.attrib)
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
            self.JobList.append(node.attrib)

        return self.JobList

    def _getPseudoClient(self):
        del self.pseudoClientList[:]

        resp = self.getCmd('Client?PseudoClientType=VSPseudo')
        if resp == None:
            return None

        activePhysicalNode = resp.findall(".//VSPseudoClientsList/client")
        for node in activePhysicalNode:
            rec = {}
            rec["clientName"] = node.attrib["clientName"]
            rec["clientType"] = "Virtual"
            try:
                rec["clientId"] = int(node.attrib["clientId"])
            except:
                pass
            self.pseudoClientList.append(rec)

        resp = self.getCmd('Client?PseudoClientType=CloudApps')
        if resp == None:
            return None

        activePhysicalNode = resp.findall(".//VSPseudoClientsList/client")
        for node in activePhysicalNode:
            rec = {}
            rec["clientName"] = node.attrib["clientName"]
            rec["clientType"] = "Cloud"
            try:
                rec["clientId"] = int(node.attrib["clientId"])
            except:
                pass
            self.pseudoClientList.append(rec)

        return self.pseudoClientList


class CV_Client(CV_GetAllInformation):
    def __init__(self, token, client=None):
        """
        Constructor
                backupsetInfo = {"clientId": -1, "clientName": None, "agentType": None, "backupsetId": -1,
                                 "backupsetName": None, "instanceName": None, "instanceId": -1, "appId": None}
                subclientInfo {'subclientName','instanceName','backupsetName','appName','agentType':,'applicationId',
                                'clientName','instanceId','backupsetId','subclientId', 'clientId'}
                self.platform = {"OSName": None, "ProcessorType": 0}
                self.clientInfo = {"clientName": None, "clientId": None, "hostName": None, "platform": self.platform,
                                   "backupsetList": [],"agentList": [], "isNotPhysical": None, "pesudoInfo": None}
                agent = {"clientName":"", "clientId":"", "applicationId":"", "agentType":"", "backupsetList":[]}

        """
        super(CV_Client, self).__init__(token)
        self.client = client

        self.backupsetList = []
        self.subclientList = []
        self.platform = {"OSName": None, "ProcessorType": 0}
        self.clientInfo = {"clientName": None, "clientId": None, "hostName": None, "platform": self.platform,
                           "backupsetList": [], "clientType": "", "agentList": []}

        if client != None:
            self.getClientInfo(client)

    def rescanClient(self):
        return self.getClientInfo(self.client)

    def getClient(self, client):
        # get clientName and clientId
        clientInfo = self.clientInfo
        platform = self.platform
        if isinstance(client, (int)):
            command = "Client/<<client>>"
            command = command.replace("<<client>>", str(client))
        else:
            command = "Client/byName(clientName='<<client>>')"
            command = command.replace("<<client>>", client)

        resp = self.getCmd(command)
        if resp == None:
            return False

        # print(self.receiveText)
        try:
            clientEntity = resp.findall(".//client/clientEntity")
            # clientEntity = resp.findall(".//ActivePhysicalNode")
            clientInfo["clientId"] = clientEntity[0].attrib["clientId"]
            clientInfo["clientName"] = clientEntity[0].attrib["clientName"]
            clientInfo["hostName"] = clientEntity[0].attrib["hostName"]

            '''
            pseudoClientInfo = resp.findall(".//pseudoClientInfo")
            for node in pseudoClientInfo:
                if len(node.attrib) == 0:
                    clientInfo["isPseudo"] = False
                else:
                    clientInfo["isPseudo"] = True
          '''
        except:
            self.msg = "did not get client"
            return False

        try:
            clientProps = resp.findall(".//clientProps")
            # clientInfo["isNotPhysical"] = clientProps[0].attrib["ClientNoPhysicalMachine"]
            # clientInfo["isVirtualClient"] = clientProps[0].attrib["IsVirtualClient"]

            osinfo = resp.findall(".//osInfo")
            self.platform["type"] = osinfo[0].attrib["type"]
            self.platfrom["subType"] = osinfo[0].attrib["subType"]
            osDisplayinfo = resp.findall(".//OsDisplayInfo")
            self.platform["OSName"] = osDisplayinfo[0].attrib["OSName"]
            self.platform["ProcessorType"] = osDisplayinfo[0].attrib["ProcessorType"]
        except:
            self.msg = "error get client platform"
        return True

    def getSubClientList(self, clientId):
        # subclientInfo {'subclientName','instanceName','backupsetName','appName','agentType':,'applicationId','clientName','instanceId','backupsetId','subclientId', 'clientId'}
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
        for node in subList:
            # print(node["appName"])
            node["agentType"] = CV_APPLICATION_WORDS[node["applicationId"]]
        return subList

    def getBackupsetList(self, clientId):
        self.getSubClientList(clientId)
        agentList = self.clientInfo["agentList"]
        flag = 0
        del self.backupsetList[:]
        backupsetInfo = {"clientId": -1, "clientName": None, "agentType": None, "backupsetId": -1,
                         "backupsetName": None, "instanceName": None, "instanceId": -1, "applicationId": None,
                         "subclientList": []}

        for node in self.subclientList:
            flag = 0
            for item in self.backupsetList:
                if node["backupsetId"] == item["backupsetId"]:
                    flag = 1
                    item["subclientList"].append(node)
                    break
            if flag == 1:
                continue
            backupset = copy.deepcopy(backupsetInfo)
            # backupset = {}
            # subclientList = []
            backupset["clientName"] = node["clientName"]
            backupset["backupsetName"] = node["backupsetName"]
            backupset["instanceName"] = node["instanceName"]
            backupset["backupsetId"] = node["backupsetId"]
            backupset["instanceId"] = node["instanceId"]
            backupset["clientId"] = node["clientId"]
            backupset["agentType"] = node["agentType"]
            backupset["applicationId"] = node["applicationId"]
            backupset["subclientList"].append(node)
            self.backupsetList.append(backupset)

        for item in agentList:
            backupsetList = item["backupsetList"]
            del backupsetList[:]
            for node in self.backupsetList:
                if node["applicationId"] == item["applicationId"]:
                    backupsetList.append(node)

        return self.backupsetList

    def getClientAgentList(self, clientId):
        # agent = {"clientName":, "clientId":, "applicationId":, "agentType":}
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
                agent["clientId"] = node.attrib["clientId"]
                appId = node.attrib["applicationId"]
                agent["applicationId"] = appId
                agent["agentType"] = CV_APPLICATION_WORDS[appId]
                agent["backupsetList"] = []
                agentList.append(copy.deepcopy(agent))
        except:
            self.msg = "error get agent type"
            pass
        return agentList

    def getClientInfo(self, client):
        clientInfo = self.clientInfo
        clientInfo["clientId"] = "0"
        clientInfo["clientName"] = ""
        self.client = client
        if self.token == None or client == None:
            return None

        if self.getClient(client) == False:
            return None

        clientInfo["agentList"] = self.getClientAgentList(clientInfo["clientId"])
        clientInfo["backupsetList"] = self.getBackupsetList(clientInfo["clientId"])
        return clientInfo

    def checkClientPseudo(self, clientList):
        try:
            for node in clientList:
                if node["clientId"] == int(self.clientInfo["clientId"]):
                    self.clientInfo["clientType"] = node["clientType"]
                    break
        except:
            self.clientInfo["clientType"] = "Physical"
            pass
        return


class CV_NewClient(CV_GetAllInformation):
    def __init__(self, token):
        """
        Constructor
        """
        super(CV_NewClient, self).__init__(token)

    def newVMClient(self, vmClient):
        # param vmClient{"clientName", "vCenterHost":, "userName":, "passwd":, "proxyList":["", ""]
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

        keys = vmClient.keys()
        if "clientName" not in keys:
            self.msg = "Param vmClient did not include clientName"
            return False
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
            # print(users)
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
            clientName[0].text = vmClient["clientName"]

            hosts = root.findall(".//vmwareVendor/vcenterHostName")
            hosts[0].text = vmClient["vCenterHost"]

        except:
            self.msg = "Error: it is not VSA xml file"
            # traceback.print_exc()
            return False

        xmlString = ""
        xmlString = ET.tostring(root, encoding='utf-8', method='xml')
        # print(xmlString.encode(encoding="utf-8"))
        return self.qCmd("QCommand/qoperation execute", xmlString)

    def NewRacClient(self, clientName):
        return


class CV_Backupset(CV_GetAllInformation):
    def __init__(self, token, client=None, agentId=None, backupsetId=None):
        """
        Constructor

        """
        super(CV_Backupset, self).__init__(token)
        self.isNewBackupset = True
        self.backupsetInfo = {"clientInfo": None, "applicationId": None, "agentType": None, "backupsetId": None,
                              "backupsetNode": None, "backupContent": None}
        # subclientInfo {'subclientName','instanceName','backupsetName','appName','agentType':,'applicationId','clientName','instanceId','backupsetId','subclientId', 'clientId', 'content'}
        self.fsContent = {"fsStoragePolicy": "", "paths": [], "sysState": None, "oneTouch": None, "streams": "",
                          "schduleList": []}
        self.vmContent = {"vmStoragePolicy": "", "vmContent": [], "proxy": [], "streams": "", "schduleList": []}
        self.dbContent = {"dbStoragePolicy": "", "logStoragePolicy": "", "dbContent": [], "streams": "",
                          "schduleList": []}
        # self.dbCredit ={}

        self.subClientList = []
        if isinstance(client, CV_Client):
            self.client = client
        else:
            self.client = CV_Client(token, client)
        if self.client.clientInfo["clientId"] == "0":
            self.client = None
            return
        clientInfo = self.client.clientInfo
        self.backupsetInfo["clientInfo"] = clientInfo

        for node in clientInfo["agentList"]:
            if agentId == node["applicationId"]:
                self.backupsetInfo["applicationId"] = agentId
                self.backupsetInfo["agentType"] = CV_APPLICATION_WORDS[agentId]
                break
        if self.backupsetInfo["applicationId"] == None:
            self.client = None
            return

        for node in clientInfo["backupsetList"]:
            if backupsetId == node["backupsetId"]:
                self.backupsetInfo["backupsetNode"] = node
                self.backupsetInfo["backupsetId"] = backupsetId
                break
        if self.backupsetInfo["backupsetId"] == None:
            return

        self._getBackupset()
        self.isNewBackupset = False

    def _getBackupset(self):
        backupsetInfo = self.backupsetInfo
        agentType = backupsetInfo["agentType"]
        agentId = backupsetInfo["applicationId"]
        backupsetId = backupsetInfo["backupsetId"]
        self._getSubClientList(agentId, backupsetId)

    def _getSubClientList(self, agentId, backupsetId):
        del self.subClientList[:]
        subclientList = self.subClientList

        for node in self.client.subclientList:
            if node["applicationId"] == agentId and node["backupsetId"] == backupsetId:
                if "DDB" in node["subclientName"] or "IndexBackup" in node["subclientName"]:
                    continue
                subclientNode = copy.deepcopy(node)
                agentType = subclientNode["agentType"]
                if "File System" in agentType:
                    fscontent = self._getFSContent(subclientNode["subclientId"])
                    subclientNode["content"] = fscontent
                if "Oracle" in agentType or "SQL" in agentType:
                    dbcontent = self._getDBContent(subclientNode["subclientId"], agentType)
                    subclientNode["content"] = dbcontent
                    pass
                if "Virtual Server" in subclientNode["agentType"]:
                    pass

                subclientList.append(subclientNode)

        # print(subclientList)
        return

    def _getFSContent(self, subclientId):
        cmd = 'Subclient/%s' % subclientId
        fscontent = copy.deepcopy(self.fsContent)
        resp = self.getCmd(cmd)
        if resp == None:
            return fscontent
        # ET.dump(resp)

        storages = resp.findall(".//dataBackupStoragePolicy")
        contents = resp.findall(".//content")
        fsProps = resp.findall(".//fsSubClientProp")
        try:
            for node in storages:
                if "storagePolicyId" in node.attrib.keys():
                    fscontent["fsStoragePolicy"] = node.attrib["storagePolicyId"]
                break
            for node in contents:
                if "path" in node.attrib.keys():
                    fscontent["paths"].append(node.attrib["path"])
            for node in fsProps:
                if "backupSystemState" in node.attrib.keys():
                    fscontent["sysState"] = node.attrib["backupSystemState"]
                if "oneTouchSubclient" in node.attrib.keys():
                    fscontent["oneTouch"] = node.attrib["oneTouchSubclient"]
                # useVSS = "1"
                # vssOptions = "2"
                # oneTouchSubclient = "0"
                break
        except:
            pass

        return fscontent

    def _getDBContent(self, subclientId, agentType):
        cmd = 'Subclient/%s' % subclientId
        dbcontent = copy.deepcopy(self.dbContent)
        resp = self.getCmd(cmd)
        if resp == None:
            return dbcontent

        try:
            storages = resp.findall(".//storageDevice/dataBackupStoragePolicy")
            for node in storages:
                if "storagePolicyId" in node.attrib.keys():
                    dbcontent["dbStoragePolicy"] = node.attrib["storagePolicyId"]
                break

            storages = resp.findall(".//storageDevice/logBackupStoragePolicy")
            for node in storages:
                if "storagePolicyId" in node.attrib.keys():
                    dbcontent["logStoragePolicy"] = node.attrib["storagePolicyId"]
                break

            if "SQL Server" in agentType:
                contents = resp.findall(".//subClientProperties/content/mssqlDbContent")
                for node in contents:
                    if "databaseName" in node.attrib.keys():
                        dbcontent["dbContent"].append(node.attrib["databaseName"])
        except:
            pass

        return dbcontent

    def _getSchduleBySubId(self, subclientId):
        cmd = "Schedules?subclientId=%s" % subclientId
        resp = self.getCmd(cmd)
        if resp == None:
            return None
        # ET.dump(resp)
        schduleList = []
        schduleNode = {}
        try:
            taskDetails = resp.findall(".//taskDetail/task")
            for node in taskDetails:
                schduleNode["GUID"] = node.attrib["GUID"]
                schduleNode["taskId"] = node.attrib["taskId"]
                schduleNode["taskType"] = node.attrib["taskType"]
            schduleList.append(schduleNode)
        except:
            pass

        return schduleList

    def _setSPBySubId(self, subclientId, spname=None):
        if spname == None or subclientId == None:
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
        return self.postCmd(cmd, updateClientProps)

    def updateDBInstance(self, credit={}, dbsp="", logsp="", cmdsp="", schdule=""):
        if self.clint == None:
            self.msg = "there is not this client or agentId "
            return False
        agentType = self.backupsetInfo["agentType"]
        if "Oracle" in agentType:
            keys = credit.keys()
            if "instance" not in keys:
                self.msg = "Param credit did not include instanceName"
                return False
            if "userName" not in keys:
                self.msg = "Param credit did not include userName"
                return False
            if "passwd" not in keys:
                self.msg = "Param credit did not include passwd"
                return False
            if "home" not in keys:
                self.msg = "Param credit did not include oracle home"
                return False

            client = self.client

            return True

        if "SQL Server" in agentType:
            return True
        return

    def _oracleInstance(self, credit={}, dbsp="", logsp="", cmdsp=""):
        createCmd = '''
        <App_CreateInstanceRequest>
          <instanceProperties>
            <description></description>
            <instance>
                <appName>Oracle</appName>
                <clientName></clientName>
                <instanceName></instanceName>
            </instance>
            <oracleInstance>
                <TNSAdminPath></TNSA2nPath>
                <blockSize>1048576</blockSize>
                <catalogConnect>
                    <domainName></domainName>
                    <userName></userName>
                </catalogConnect>
                <crossCheckTimeout>600</crossCheckTimeout>
                <ctrlFileAutoBackup>1</ctrlFileAutoBackup>
                <dataArchiveGroup>
                    <storagePolicyName></storagePolicyName>
                </dataArchiveGroup>
                <disableRMANcrosscheck>false</disableRMANcrosscheck>
                <encryptionFlag>ENC_NONE</encryptionFlag>
                <isOnDemand>false</isOnDemand>
                <numberOfArchiveLogBackupStreams>2</numberOfArchiveLogBackupStreams>
                <oracleHome></oracleHome>
                <oracleStorageDevice>
                    <commandLineStoragePolicy>
                        <storagePolicyName></storagePolicyName>
                    </commandLineStoragePolicy>
                    <deDuplicationOptions>
                        <generateSignature>ON_CLIENT</generateSignature>
                    </deDuplicationOptions>
                    <logBackupStoragePolicy>
                        <storagePolicyName></storagePolicyName>
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
        </App_CreateInstanceRequest>
        '''

        updateCmd = '''
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
                    <numberOfArchiveLogBackupStreams>2</numberOfArchiveLogBackupStreams>
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
        </App_UpdateInstancePropertiesRequest>
        '''

        if self.isNewBackupset:

        else:

        return


def dump_cv_backupset(cvToken, client, agentType, backupset, parent):
    CVBackupset = CV_Backupset(cvToken, client, agentType, backupset)
    subclientList = CVBackupset.subClientList
    for node in subclientList:
        subclientItem = ET.SubElement(parent, "subclient")
        for key, value in node.items():
            if "content" not in key:
                subclientItem.set(key, str(value))
            else:
                content = node["content"]
                for subKey, value in content.items():
                    contentItem = ET.SubElement(subclientItem, subKey)
                    contentItem.text = str(value)
    return


def dump_cv_client(cvToken, clientName, parent, clientList):
    CVClient = CV_Client(cvToken, clientName)
    CVClient.checkClientPseudo(clientList)
    clientInfo = CVClient.clientInfo
    if clientInfo["clientId"] == "0":
        return
    # print(CVClient.clientInfo)

    for node in clientInfo["agentList"]:
        agentItem = ET.SubElement(parent, 'Agent')
        agentItem.set("agentType", node["agentType"])
        agentItem.set("applicationId", node["applicationId"])
        for node_backupset in clientInfo["backupsetList"]:
            # print(node_backupset)
            if node_backupset["applicationId"] == node["applicationId"]:
                if "File System" in node["agentType"] or "Virtual" in node["agentType"]:
                    backupsetItem = ET.SubElement(agentItem, 'Backupset')
                    # backupsetItem.text = node_backupset["backupsetName"]
                else:
                    backupsetItem = ET.SubElement(agentItem, 'Instance')
                    # backupsetItem.text = node_backupset["instanceName"]
                for key, value in node_backupset.items():
                    if "subclientList" in key:
                        continue
                    backupsetItem.set(key, str(value))
                dump_cv_backupset(cvToken, CVClient, node["applicationId"], node_backupset["backupsetId"],
                                  backupsetItem)

    return


def dump_commcell(cvToken, dumpfile):
    GetAllInfo = CV_GetAllInformation(cvToken)
    clientList = GetAllInfo.getClientList()
    spList = GetAllInfo.getSPList()
    schduleList = GetAllInfo.getSchduleList()

    root = ET.Element('CommCell')
    tree = ElementTree(root)

    listStr = ["platform", "backupsetList", "agentList"]
    for node in clientList:
        clientItem = ET.SubElement(root, 'clientEntity')
        for key, val in node.items():
            clientItem.set(key, str(val))
        CVClient = CV_Client(cvToken, node["clientName"])
        dict = CVClient.clientInfo
        for key, val in dict.items():
            if key not in listStr:
                clientItem.set(key, str(val))
        dump_cv_client(cvToken, node["clientName"], clientItem, clientList)

    for node in spList:
        spItem = ET.SubElement(root, 'StoragePolice')
        # print(node)
        # {'storagePolicyName': 'GDSP_DB', 'storagePolicyId': '5'}
        for key, value in node.items():
            spItem.set(key, str(value))

    for node in schduleList:
        schduleItem = ET.SubElement(root, 'Schdule')
        # print(node)
        # {'taskId': '193', 'ownerName': 'cvadmin', 'runUserId': '1', 'description': '', 'alertId': '0', 'ownerId': '1', 'associatedObjects': '6', 'taskType': '4', 'policyType': '0', 'taskName': 'DB backup'}
        for key, value in node.items():
            if key == "taskId":
                schduleItem.set("schduleId", str(value))
            if key == "taskName":
                schduleItem.set("schduleName", str(value))
            schduleItem.set(key, str(value))

    # ET.dump(root)
    tree.write(dumpfile, encoding='utf-8')
    return


if __name__ == "__main__":
    print('it is main')
    info = {"webaddr": "172.16.110.55", "port": "81", "username": "cvadmin", "passwd": "1qaz@WSX", "token": "",
            "lastlogin": 0}
    # info = {"webaddr": "106.14.123.86", "port": "81", "username": "cvadmin", "passwd": "1qaz@WSX", "token": "",
    #        "lastlogin": 0}
    cvToken = CV_RestApi_Token()
    if cvToken.login(info) == None:
        print("did not login", cvToken.msg)
        exit
    else:
        print("login in: ", cvToken.credit["token"])

    # dump_commcell(cvToken, "cv_dump.xml")

    # CVClient = CV_Client(cvToken, 3)
    CVClient = CV_Client(cvToken, "linux-db1")
    backupsetList = CVClient.backupsetList
    for node in backupsetList:
        print(node)
    # for key, val in CVClient.clientInfo.items():
    #    print(key, val)

    '''
    GetAllInfo = CV_GetAllInformation(cvToken)

    spList = GetAllInfo.getSPList()
    print(GetAllInfo.receiveText)
    for node in spList:
        print(node)
    
    schduleList = GetAllInfo.getSchduleList()
    for node in schduleList:
        print(node)
    clientList = GetAllInfo.getClientList()
    for node in clientList:
        print(node)
    jobList = GetAllInfo.getJobList("2")
    for node in jobList:
        print(node)
    CVClient = CV_Client(cvToken, 2)
    #CVClient.getClient(2)
    print(CVClient.clientInfo)

    newClient = CV_NewClient(cvToken)
    vmClient = {"clientName": "vcTest", "vCenterHost": "172.16.110.19", "userName":"administrator", "passwd":"123456", "proxyList": ["WIN-V11-MA2"]}
    print(newClient.NewVMClient(vmClient))
    #print("retcode %d" % retCode)
    print(newClient.msg)
    GetAllInfo = CV_GetAllInformation(cvToken)
    clientList = GetAllInfo.getClientList()
    for node in clientList:
        print(node)

    CVClient = CV_Client(cvToken, 'WIN-CLIENT1')
    print(CVClient.clientInfo)
    '''
