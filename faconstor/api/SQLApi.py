import datetime
import copy
# from TSDRM import settings
# from faconstor.CVApi_bak import *
import re
# import pyodbc
import pymssql


class DataMonitor(object):
    def __init__(self, credit):
        self.msg = ""
        self.host = credit["SQLServerHost"]
        self.user = credit["SQLServerUser"]
        self.password = credit["SQLServerPasswd"]
        self.database = credit["SQLServerDataBase"]
        self._conn = self._connection

    @property
    def _connection(self):
        try:
            # connection = pyodbc.connect('DRIVER={SQL Server};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s' % (
            #     self.host, self.database, self.user, self.password))
            # print(self.host, self.database, self.user, self.password)
            connection = pymssql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
        except Exception as e:
            self.msg = "链接数据库失败。"
            print(self.msg)
            return None
        else:
            return connection

    def fetch_one(self, temp_sql):
        result = None
        if self._conn:
            with self._conn.cursor() as cursor:
                cursor.execute(temp_sql)
                result = cursor.fetchone()
        return result

    def fetch_all(self, temp_sql):
        result = []
        if self._conn:
            with self._conn.cursor() as cursor:
                cursor.execute(temp_sql)
                result = cursor.fetchall()
        return result

    def execute(self, temp_sql):
        result = []
        if self._conn:
            with self._conn.cursor() as cursor:
                cursor.execute(temp_sql)
                self._conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()

class CVApi(DataMonitor):
    def get_all_install_clients(self):
        clients_sql = """SELECT [ClientId],[Client],[NetworkInterface],[OS [Version]]],[Hardware],[GalaxyRelease],[InstallTime],[UninstallTime],[DeletedTime],[ClientStatus],[ClientBkpEnable],[ClientRstEnable]
                            FROM [commserv].[dbo].[CommCellClientConfig]"""

        installed_clients = []
        content = self.fetch_all(clients_sql)
        for i in content:
            automatic_clients = self.get_automatic_clients()
            if i[1] not in automatic_clients:
                installed_clients.append({
                    "client_id": i[0],
                    "client_name": i[1],
                    "network_interface": i[2],
                    "os": i[3],
                    "hardware": i[4],
                    "galaxy_release": i[5],
                    "install_time": i[6],
                    "client_bkp_enable": i[7],
                    "client_rst_enable": i[8],
                })

        return installed_clients

    def get_single_installed_client(self, client):
        if isinstance(client, int):
            client_sql = """SELECT [ClientId],[Client],[NetworkInterface],[OS [Version]]],[Hardware],[GalaxyRelease],[InstallTime],[UninstallTime],[DeletedTime],[ClientStatus],[ClientBkpEnable],[ClientRstEnable]
                            FROM [commserv].[dbo].[CommCellClientConfig] WHERE [ClientId]='{0}'""".format(
                client)
        elif isinstance(client, str):
            client_sql = """SELECT [ClientId],[Client],[NetworkInterface],[OS [Version]]],[Hardware],[GalaxyRelease],[InstallTime],[UninstallTime],[DeletedTime],[ClientStatus],[ClientBkpEnable],[ClientRstEnable]
                            FROM [commserv].[dbo].[CommCellClientConfig] WHERE [Client]='{0}'""".format(
                client)
        else:
            self.msg = "请传入正确的客户端id或名称。"
            return None
        content = self.fetch_one(client_sql)
        if content:
            client_info = {
                "client_id": content[0],
                "client_name": content[1],
                "network_interface": content[2],
                "os": content[3],
                "hardware": content[4],
                "galaxy_release": content[5],
                "install_time": content[6],
                "client_bkp_enable": content[7],
                "client_rst_enable": content[8],
            }
        else:
            client_info = None
        return client_info

    def get_installed_sub_clients_all(self, client=None):
        if client:
            if isinstance(client, int):
                sub_client_sql = """SELECT [appid],[clientid],[clientname],[idataagent],[idataagentstatus],[idagentbkenable],[idagentrstenable],[instance],[backupset],[subclient],[subclientstatus],[schedjobpattern],
                                     [schedbackupday],[schedbackuptime],[schednextbackuptime],[data_sp],[data_sp_copy],[data_sp_copy_retendays],[data_sp_copy_fullcycles],[data_sp_schedauxcopypattern],[data_sp_schedauxcopyday],[data_sp_schedauxcopytime],
                                     [data_sp_schednextauxcopytime],[data_sp_scheddestcopy],[log_sp],[LastFullBkpSize(Bytes)],[LastIncBkpSize(Bytes)],[LastDiffBkpSize(Bytes)],[QDisplayName],[xmlDisplayName]
                                     FROM [commserv].[dbo].[CommCellSubClientConfig] WHERE [clientid]='{0}' AND [backupset]!='Indexing BackupSet'""".format(
                    client)
            elif isinstance(client, str):
                sub_client_sql = """SELECT [appid],[clientid],[clientname],[idataagent],[idataagentstatus],[idagentbkenable],[idagentrstenable],[instance],[backupset],[subclient],[subclientstatus],[schedjobpattern],
                                     [schedbackupday],[schedbackuptime],[schednextbackuptime],[data_sp],[data_sp_copy],[data_sp_copy_retendays],[data_sp_copy_fullcycles],[data_sp_schedauxcopypattern],[data_sp_schedauxcopyday],[data_sp_schedauxcopytime],
                                     [data_sp_schednextauxcopytime],[data_sp_scheddestcopy],[log_sp],[LastFullBkpSize(Bytes)],[LastIncBkpSize(Bytes)],[LastDiffBkpSize(Bytes)],[QDisplayName],[xmlDisplayName]
                                     FROM [commserv].[dbo].[CommCellSubClientConfig] WHERE [clientname]='{0}' AND [backupset]!='Indexing BackupSet'""".format(
                    client)
            else:
                self.msg = "请传入正确的客户端id或名称。"
                return None
        else:
            sub_client_sql = """SELECT [appid],[clientid],[clientname],[idataagent],[idataagentstatus],[idagentbkenable],[idagentrstenable],[instance],[backupset],[subclient],[subclientstatus],[schedjobpattern],
                                 [schedbackupday],[schedbackuptime],[schednextbackuptime],[data_sp],[data_sp_copy],[data_sp_copy_retendays],[data_sp_copy_fullcycles],[data_sp_schedauxcopypattern],[data_sp_schedauxcopyday],[data_sp_schedauxcopytime],
                                 [data_sp_schednextauxcopytime],[data_sp_scheddestcopy],[log_sp],[LastFullBkpSize(Bytes)],[LastIncBkpSize(Bytes)],[LastDiffBkpSize(Bytes)],[QDisplayName],[xmlDisplayName]
                                 FROM [commserv].[dbo].[CommCellSubClientConfig] WHERE [backupset]!='Indexing BackupSet'"""
        sub_clients = []
        content = self.fetch_all(sub_client_sql)
        for i in content:
            sub_clients.append({
                "appid": i[0],
                "clientid": i[1],
                "clientname": i[2],
                "idataagent": i[3],
                "idataagentstatus": i[4],
                "idagentbkenable": i[5],
                "idagentrstenable": i[6],
                "instance": i[7],
                "backupset": i[8],
                "subclient": i[9],
                "subclientstatus": i[10],
                "schedjobpattern": i[11],
                "schedbackupday": i[12],
                "schedbackuptime": i[13],
                "schednextbackuptime": i[14].strftime("%Y-%m-%d %H:%M:%S") if i[14] else '',
                "data_sp": i[15],
                "data_sp_copy": i[16],
                "data_sp_copy_retendays": i[17],
                "data_sp_copy_fullcycles": i[18],
                "data_sp_schedauxcopypattern": i[19],
                "data_sp_schedauxcopytime": i[20],
                "data_sp_schednextauxcopytime": i[21],
                "data_sp_scheddestcopy": i[22],
                "log_sp": i[23],
                "LastFullBkpSize": i[24],
                "LastIncBkpSize": i[25],
                "LastDiffBkpSize": i[26],
                "QDisplayName": i[27],
                "xmlDisplayName": i[28],
            })
        return sub_clients

    def get_installed_sub_clients_for_info(self, client=None):
        if client:
            if isinstance(client, int):
                sub_client_sql = """SELECT [appid],[clientid],[clientname],[idataagent],[idataagentstatus],[idagentbkenable],[idagentrstenable],[instance],[backupset],[subclient],[subclientstatus],[schedjobpattern],
                                     [schedbackupday],[schedbackuptime],[schednextbackuptime],[data_sp],[data_sp_copy],[data_sp_copy_retendays],[data_sp_copy_fullcycles],[data_sp_schedauxcopypattern],[data_sp_schedauxcopyday],[data_sp_schedauxcopytime],
                                     [data_sp_schednextauxcopytime],[data_sp_scheddestcopy],[log_sp],[LastFullBkpSize(Bytes)],[LastIncBkpSize(Bytes)],[LastDiffBkpSize(Bytes)],[QDisplayName],[xmlDisplayName]
                                     FROM [commserv].[dbo].[CommCellSubClientConfig] WHERE [clientid]='{0}' AND [backupset]!='Indexing BackupSet' AND [idataagent] LIKE '%Oracle%'""".format(
                    client)
            elif isinstance(client, str):
                sub_client_sql = """SELECT [appid],[clientid],[clientname],[idataagent],[idataagentstatus],[idagentbkenable],[idagentrstenable],[instance],[backupset],[subclient],[subclientstatus],[schedjobpattern],
                                     [schedbackupday],[schedbackuptime],[schednextbackuptime],[data_sp],[data_sp_copy],[data_sp_copy_retendays],[data_sp_copy_fullcycles],[data_sp_schedauxcopypattern],[data_sp_schedauxcopyday],[data_sp_schedauxcopytime],
                                     [data_sp_schednextauxcopytime],[data_sp_scheddestcopy],[log_sp],[LastFullBkpSize(Bytes)],[LastIncBkpSize(Bytes)],[LastDiffBkpSize(Bytes)],[QDisplayName],[xmlDisplayName]
                                     FROM [commserv].[dbo].[CommCellSubClientConfig] WHERE [clientname]='{0}' AND [backupset]!='Indexing BackupSet' AND [idataagent] LIKE '%Oracle%'""".format(
                    client)
            else:
                self.msg = "请传入正确的客户端id或名称。"
                return None
        else:
            sub_client_sql = """SELECT [appid],[clientid],[clientname],[idataagent],[idataagentstatus],[idagentbkenable],[idagentrstenable],[instance],[backupset],[subclient],[subclientstatus],[schedjobpattern],
                                 [schedbackupday],[schedbackuptime],[schednextbackuptime],[data_sp],[data_sp_copy],[data_sp_copy_retendays],[data_sp_copy_fullcycles],[data_sp_schedauxcopypattern],[data_sp_schedauxcopyday],[data_sp_schedauxcopytime],
                                 [data_sp_schednextauxcopytime],[data_sp_scheddestcopy],[log_sp],[LastFullBkpSize(Bytes)],[LastIncBkpSize(Bytes)],[LastDiffBkpSize(Bytes)],[QDisplayName],[xmlDisplayName]
                                 FROM [commserv].[dbo].[CommCellSubClientConfig] WHERE [backupset]!='Indexing BackupSet' AND [idataagent] LIKE '%Oracle%'"""
        sub_clients = []
        content = self.fetch_all(sub_client_sql)
        for i in content:
            sub_clients.append({
                "clientname": i[2],
                "idataagent": i[3],
                "backupset": i[8],
            })
        return sub_clients

    def get_installed_sub_clients_for_status(self, client=None):
        if client:
            if isinstance(client, int):
                sub_client_sql = """SELECT [appid],[clientid],[clientname],[idataagent],[idataagentstatus],[idagentbkenable],[idagentrstenable],[instance],[backupset],[subclient],[subclientstatus],[schedjobpattern],
                                     [schedbackupday],[schedbackuptime],[schednextbackuptime],[data_sp],[data_sp_copy],[data_sp_copy_retendays],[data_sp_copy_fullcycles],[data_sp_schedauxcopypattern],[data_sp_schedauxcopyday],[data_sp_schedauxcopytime],
                                     [data_sp_schednextauxcopytime],[data_sp_scheddestcopy],[log_sp],[LastFullBkpSize(Bytes)],[LastIncBkpSize(Bytes)],[LastDiffBkpSize(Bytes)],[QDisplayName],[xmlDisplayName]
                                     FROM [commserv].[dbo].[CommCellSubClientConfig] WHERE [clientid]='{0}' AND [backupset]!='Indexing BackupSet'""".format(
                    client)
            elif isinstance(client, str):
                sub_client_sql = """SELECT [appid],[clientid],[clientname],[idataagent],[idataagentstatus],[idagentbkenable],[idagentrstenable],[instance],[backupset],[subclient],[subclientstatus],[schedjobpattern],
                                     [schedbackupday],[schedbackuptime],[schednextbackuptime],[data_sp],[data_sp_copy],[data_sp_copy_retendays],[data_sp_copy_fullcycles],[data_sp_schedauxcopypattern],[data_sp_schedauxcopyday],[data_sp_schedauxcopytime],
                                     [data_sp_schednextauxcopytime],[data_sp_scheddestcopy],[log_sp],[LastFullBkpSize(Bytes)],[LastIncBkpSize(Bytes)],[LastDiffBkpSize(Bytes)],[QDisplayName],[xmlDisplayName]
                                     FROM [commserv].[dbo].[CommCellSubClientConfig] WHERE [clientname]='{0}' AND [backupset]!='Indexing BackupSet'""".format(
                    client)
            else:
                self.msg = "请传入正确的客户端id或名称。"
                return None
        else:
            sub_client_sql = """SELECT [appid],[clientid],[clientname],[idataagent],[idataagentstatus],[idagentbkenable],[idagentrstenable],[instance],[backupset],[subclient],[subclientstatus],[schedjobpattern],
                                 [schedbackupday],[schedbackuptime],[schednextbackuptime],[data_sp],[data_sp_copy],[data_sp_copy_retendays],[data_sp_copy_fullcycles],[data_sp_schedauxcopypattern],[data_sp_schedauxcopyday],[data_sp_schedauxcopytime],
                                 [data_sp_schednextauxcopytime],[data_sp_scheddestcopy],[log_sp],[LastFullBkpSize(Bytes)],[LastIncBkpSize(Bytes)],[LastDiffBkpSize(Bytes)],[QDisplayName],[xmlDisplayName]
                                 FROM [commserv].[dbo].[CommCellSubClientConfig] WHERE [backupset]!='Indexing BackupSet'"""
        sub_clients = []
        content = self.fetch_all(sub_client_sql)
        for i in content:
            sub_clients.append({
                "clientname": i[2],
                "idataagent": i[3],
            })
        return sub_clients

    def get_all_storage(self):
        storage_sql = """SELECT [storagepolicy],[defaultcopy],[hardwarecompress],[maxstreams],[drivepool],[library],[appid],[clientname],[idataagent],[instance],[backupset],[subclient]
                          FROM [commserv].[dbo].[CommCellStoragePolicy]
                          WHERE [hardwarecompress]!='Unknown' AND [idataagent] LIKE '%Oracle%'"""

        storages = []
        content = self.fetch_all(storage_sql)
        for i in content:
            storages.append({
                "storagepolicy": i[0],
                # "defaultcopy": i[1],
                # "hardwarecompress": i[2],
                # "maxstreams": i[3],
                # "drivepool": i[4],
                # "library": i[5],
                # "appid": i[6],
                "clientname": i[7],
                "idataagent": i[8],
                "instance": i[9],
                "backupset": i[10],
                # "subclient": i[11],
            })

        extra_content = self.get_installed_sub_clients_for_info()
        # 去重
        extra_content = remove_duplicate_for_info(extra_content)
        whole_list = []

        for storage in storages:

            for content in extra_content:
                if content['clientname'] == storage['clientname'] and content['idataagent'] == storage['idataagent'] and \
                        content['backupset'] == storage['backupset']:
                    whole_list.append({
                        "storagepolicy": storage['storagepolicy'],
                        "clientname": storage['clientname'],
                        "idataagent": storage['idataagent'],
                        "backupset": storage['backupset'],
                    })
                    # 剔除已经包含的
                    extra_content.remove({
                        "clientname": storage['clientname'],
                        "idataagent": storage['idataagent'],
                        "backupset": storage['backupset'],
                    })
        # 未包含的置空
        for e_content in extra_content:
            whole_list.append({
                "storagepolicy": '无',
                "clientname": e_content['clientname'],
                "idataagent": e_content['idataagent'],
                "backupset": e_content['backupset'],
            })
        return whole_list

    def get_all_schedules(self):
        schedule_sql = """SELECT [CommCellId],[CommCellName],[scheduleId],[scheduePolicy],[scheduleName],[scheduletask],[schedbackuptype],[schedpattern],[schedinterval]
        ,[schedbackupday],[schedbackupTime],[schednextbackuptime],[appid],[clientName],[idaagent],[instance],[backupset],[subclient]
        FROM [commserv].[dbo].[CommCellBkScheduleForSubclients] WHERE [idaagent] LIKE '%Oracle%'"""

        schedules = []
        content = self.fetch_all(schedule_sql)
        period_chz = {
            "One time": "次",
            "Daily": "日",
            "Weekly": "周",
            "Monthly": "月",
            "Monthly relative": "月",
            "Yearly": "年",
            "Yearly relative": "年",
            "Automatic schedule": "自动",
        }

        schedbackupday_chz = {
            "Sunday": "周日",
            "Monday": "周一",
            "Tuesday": "周二",
            "Wednesday": "周三",
            "Thursday": "周四",
            "Friday": "周五",
            "Saturday": "周六",
        }

        type_chz = {
            "Full": "全备",
            "Incremental": "增量",
            "Synthetic Full": "综合完全",
            "NONE": "无",
            "Differential": "差量",
            "Unknown": "预选备份类型"
        }

        month_chz = {
            "January": "1月",
            "February": "2月",
            "March": "3月",
            "April": "4月",
            "May": "5月",
            "June": "6月",
            "July": "7月",
            "August": "8月",
            "September": "9月",
            "October": "10月",
            "November": "11月",
            "December": "12月",
        }

        for i in content:
            # 处理schedbackupday
            schedbackupday = ""
            schedinterval = ""
            if i[7] == "Weekly":
                for day in i[9].split(" "):
                    if day:
                        schedbackupday += "/" + \
                            schedbackupday_chz[day] if day in schedbackupday_chz.keys(
                            ) else day
                schedbackupday = schedbackupday[1:]

                # 重复schedinterval
                if i[8] == "Every 0":
                    schedinterval = "不重复"
                else:
                    schedinterval = i[8].replace("Every", "每") + "周"

            if i[7] == "One time":
                schedbackupday = "仅一次"  # 具体时间

                if i[8] == "Every 0":
                    schedinterval = "不重复"
                else:
                    schedinterval = i[8].replace("Every", "每") + "次"

            if i[7] == "Daily":
                schedbackupday = "每天"

                if i[8] == "Every 0":
                    schedinterval = "不重复"
                else:
                    schedinterval = i[8].replace("Every", "每") + "天"

            if i[7] in ["Monthly", "Monthly relative"]:
                schedbackupday = "每月第{0}天".format(i[9])

                if i[8] == "Every 0":
                    schedinterval = "不重复"
                else:
                    schedinterval = i[8].replace("Every", "每") + "个月"

            if i[7] in ["Yearly", "Yearly relative"]:
                year_list = i[9].split(" of ")
                schedbackupday = "每年{0}{1}日".format(
                    month_chz[year_list[1]] if year_list[1] in month_chz.keys() else year_list[1], year_list[0])

                if i[8] == "Every 0":
                    schedinterval = "不重复"
                else:
                    schedinterval = i[8].replace("Every", "每") + "年"
            # 缺少自动/连续

            schedpattern = period_chz[i[7]
                                      ] if i[7] in period_chz.keys() else i[7]
            schedbackuptype = type_chz[i[6]
                                       ] if i[6] in type_chz.keys() else i[6]
            schedules.append({
                # "CommCellId": i[0],
                # "CommCellName": i[1],
                "scheduleId": i[2],
                "scheduePolicy": i[3],
                "scheduleName": i[4],
                "scheduletask": i[5],
                "schedbackuptype": schedbackuptype,
                "schedpattern": schedpattern,
                "schedinterval": schedinterval,
                "schedbackupday": schedbackupday,
                # "schedbackupTime": i[10] if i[7] != "One time" else i[11].strftime("%Y-%m-%d %H:%M:%S"),
                "schednextbackuptime": i[11].strftime("%Y-%m-%d %H:%M:%S"),
                "clientName": i[13],
                "idaagent": i[14],
                "instance": i[15],
                "backupset": i[16],
                # "subclient": i[17],
            })

        extra_content = self.get_installed_sub_clients_for_info()
        # 去重
        extra_content = remove_duplicate_for_info(extra_content)
        whole_list = []

        for schedule in schedules:

            for content in extra_content:
                if content['clientname'] == schedule['clientName'] and content['idataagent'] == schedule['idaagent'] and \
                        content['backupset'] == schedule['backupset']:
                    whole_list.append({
                        "scheduePolicy": schedule['scheduePolicy'],
                        "scheduleName": schedule['scheduleName'],
                        "schedbackuptype": schedule['schedbackuptype'],
                        "schedpattern": schedule['schedpattern'],
                        "schedinterval": schedule['schedinterval'],
                        "schedbackupday": schedule['schedbackupday'],
                        "schednextbackuptime": schedule['schednextbackuptime'],
                        "clientName": schedule['clientName'],
                        "idaagent": schedule['idaagent'],
                        "backupset": schedule['backupset'],
                    })
                    # 剔除已经包含的
                    extra_content.remove({
                        "clientname": schedule['clientName'],
                        "idataagent": schedule['idaagent'],
                        "backupset": schedule['backupset'],
                    })
        # 未包含的置空
        for e_content in extra_content:
            whole_list.append({
                "scheduePolicy": '无',
                "scheduleName": '无',
                "schedbackuptype": '无',
                "schedpattern": '无',
                "schedinterval": '无',
                "schedbackupday": '无',
                "schednextbackuptime": '无',
                "clientName": e_content['clientname'],
                "idaagent": e_content['idataagent'],
                "backupset": e_content['backupset'],
            })

        return whole_list

    def get_vm_backup_content(self, client_id=None):
        if client_id:
            vm_backup_content_sql = """
            SELECT [vmname],[vmclientid],[virtualizationclient],[virtualizationclientid],[jobid],[vmGUID],[vmstatus],[vmhost],[proxy],[startdateunixsec]
            ,[enddateunixsec],[startdate],[enddate],[failureReason],[vmbackupsizebytes],[vmguestsizebytes],[vmsizebytes],[vmcbtstatus],[vmtransportmode]
            ,[subclient],[backupset],[data_sp],[backuplevelInt],[backuplevel]
            FROM [CommServ].[dbo].[CommCellVMBackupInfo] WHERE [virtualizationclientid] = {0}
            """.format(client_id)
        else:
            vm_backup_content_sql = """
            SELECT [vmname],[vmclientid],[virtualizationclient],[virtualizationclientid],[jobid],[vmGUID],[vmstatus],[vmhost],[proxy],[startdateunixsec]
            ,[enddateunixsec],[startdate],[enddate],[failureReason],[vmbackupsizebytes],[vmguestsizebytes],[vmsizebytes],[vmcbtstatus],[vmtransportmode]
            ,[subclient],[backupset],[data_sp],[backuplevelInt],[backuplevel]
            FROM [CommServ].[dbo].[CommCellVMBackupInfo]
            """

        vm_backup_content_list = []
        content = self.fetch_all(vm_backup_content_sql)
        for i in content:
            vm_backup_content_list.append({
                "vmname": i[0],
                "vmclientid": i[1],
                "virtualizationclient": i[2],
                "virtualizationclientid": i[3],
                "vmhost": i[7],
                "backupset": i[20],
                "subclient": i[19]
            })
        return vm_backup_content_list

    def get_instance_from_oracle(self):
        # instance_sql = """SELECT DISTINCT [clientname],[idataagent],[instance], [clientid]
        #                   FROM [commserv].[dbo].[CommCellSubClientConfig]
        #                   WHERE [idataagentstatus] = 'installed' AND [instance] IS NOT NULL AND [instance] != ''
        #                   AND [idataagent] LIKE 'Oracle%';"""
        instance_sql = """SELECT DISTINCT [clientname],[idataagent],[instance], [clientid]
                          FROM [commserv].[dbo].[CommCellSubClientConfig]
                          WHERE [instance] IS NOT NULL AND [instance] != ''
                          AND [idataagent] LIKE 'Oracle%';"""
        oracle_instance = self.fetch_all(instance_sql)
        instance_list = []
        for instance in oracle_instance:
            instance_list.append({
                "clientid": instance[3],
                "clientname": instance[0],
                "agent": instance[1],
                "instance": instance[2]
            })
        return instance_list

    def get_all_backup_content(self):
        # 虚机备份内容
        # cv_token = CVRestApiToken()
        # cv_token.login(settings.CVApi_credit)
        # cv_api = CVApiOperate(cv_token)

        # "Mysql", "Windows File System", "Linux File System"
        backupset_content_sql = """SELECT [clientname],[idataagent],[backupset],[subclient],[content]
                                   FROM [commserv].[dbo].[CommCellClientFSFilters]
                                   WHERE [subclientstatus]='valid'"""
        # ["Oracle Database", "SQL Server", "Virtual Server"]
        instance_content_sql = """SELECT [clientname],[idataagent],[instance],[backupset],[subclient], [clientid]
                                  FROM [commserv].[dbo].[CommCellSubClientConfig]
                                  WHERE [idataagentstatus] = 'installed' AND [data_sp]!='not assigned'"""
        backupset_content = self.fetch_all(backupset_content_sql)
        instance_content = self.fetch_all(instance_content_sql)

        backupset_content_list = []
        for i in backupset_content:
            if i[1] in ["Mysql", "Windows File System", "Linux File System"]:
                backupset_content_list.append({
                    "clientname": i[0],
                    "idataagent": i[1],
                    "backupset": i[2],
                    "subclient": i[3],
                    "content": i[4],
                })

        for i in instance_content:
            if i[1] in ["Oracle Database", "SQL Server"]:
                backupset_content_list.append({
                    "clientname": i[0],
                    "idataagent": i[1],
                    "backupset": i[3],
                    "subclient": i[4],
                    "content": i[2],
                })
            if i[1] in ["Virtual Server"]:
                # clientId
                client_id = i[5]

                content = self.get_vm_backup_content(client_id)

                for vm_content in content:
                    backupset_content_list.append({
                        "clientname": i[0],
                        "idataagent": i[1],
                        "backupset": i[3],
                        "subclient": i[4],
                        "content": vm_content["vmname"],
                    })

        extra_content = self.get_installed_sub_clients_for_info()
        # 去重
        extra_content = remove_duplicate_for_info(extra_content)
        whole_list = []

        for b_content in backupset_content_list:

            for content in extra_content:
                if content['clientname'] == b_content['clientname'] and content['idataagent'] == b_content[
                        'idataagent'] and content['backupset'] == b_content['backupset']:
                    whole_list.append({
                        "clientname": b_content['clientname'],
                        "idataagent": b_content['idataagent'],
                        "backupset": b_content['backupset'],
                        "content": b_content['content'],
                    })
                    # 剔除已经包含的
                    extra_content.remove({
                        "clientname": b_content['clientname'],
                        "idataagent": b_content['idataagent'],
                        "backupset": b_content['backupset'],
                    })
        # 未包含的置空
        for e_content in extra_content:
            whole_list.append({
                "clientname": e_content['clientname'],
                "idataagent": e_content['idataagent'],
                "backupset": e_content['backupset'],
                "content": '无',
            })

        return whole_list

    def get_schedules(self, client=None, agent=None, backup_set=None, sub_client=None, schedule=None,
                      schedule_type=None):
        if all([client, agent, backup_set, sub_client, schedule, schedule_type]):
            schedule_sql = """SELECT [CommCellId],[CommCellName],[scheduleId],[scheduePolicy],[scheduleName],[scheduletask],[schedbackuptype],[schedpattern],[schedinterval]
            ,[schedbackupday],[schedbackupTime],[schednextbackuptime],[appid],[clientName],[idaagent],[instance],[backupset],[subclient]
            FROM [commserv].[dbo].[CommCellBkScheduleForSubclients] WHERE [clientName]='{0}' AND [idaagent]='{1}' AND [backupset]='{2}'AND [subclient]='{3}' AND [scheduePolicy]='{4}' AND [schedbackuptype]='{5}'""". \
                format(client, agent, backup_set,
                       sub_client, schedule, schedule_type)
        elif all([client, agent, backup_set, sub_client, schedule]) and not schedule_type:
            schedule_sql = """SELECT [CommCellId],[CommCellName],[scheduleId],[scheduePolicy],[scheduleName],[scheduletask],[schedbackuptype],[schedpattern],[schedinterval]
            ,[schedbackupday],[schedbackupTime],[schednextbackuptime],[appid],[clientName],[idaagent],[instance],[backupset],[subclient]
            FROM [commserv].[dbo].[CommCellBkScheduleForSubclients] WHERE [clientName]='{0}' AND [idaagent]='{1}' AND [backupset]='{2}' AND [subclient]='{3}' AND [scheduePolicy]='{4}'""". \
                format(client, agent, backup_set, sub_client, schedule)
        elif all([client, agent, backup_set, sub_client]) and not any([schedule, schedule_type]):
            schedule_sql = """SELECT [CommCellId],[CommCellName],[scheduleId],[scheduePolicy],[scheduleName],[scheduletask],[schedbackuptype],[schedpattern],[schedinterval]
            ,[schedbackupday],[schedbackupTime],[schednextbackuptime],[appid],[clientName],[idaagent],[instance],[backupset],[subclient]
            FROM [commserv].[dbo].[CommCellBkScheduleForSubclients] WHERE [clientName]='{0}' AND [idaagent]='{1}' AND [backupset]='{2}' AND [subclient]='{3}'""". \
                format(client, agent, backup_set, sub_client)
        elif all([client, agent, backup_set]) and not any([sub_client, schedule, schedule_type]):
            schedule_sql = """SELECT [CommCellId],[CommCellName],[scheduleId],[scheduePolicy],[scheduleName],[scheduletask],[schedbackuptype],[schedpattern],[schedinterval]
            ,[schedbackupday],[schedbackupTime],[schednextbackuptime],[appid],[clientName],[idaagent],[instance],[backupset],[subclient]
            FROM [commserv].[dbo].[CommCellBkScheduleForSubclients] WHERE [clientName]='{0}' AND [idaagent]='{1}' AND [backupset]='{2}'""". \
                format(client, agent, backup_set)
        elif all([client, agent]) and not any([backup_set, sub_client, schedule, schedule_type]):
            schedule_sql = """SELECT [CommCellId],[CommCellName],[scheduleId],[scheduePolicy],[scheduleName],[scheduletask],[schedbackuptype],[schedpattern],[schedinterval]
            ,[schedbackupday],[schedbackupTime],[schednextbackuptime],[appid],[clientName],[idaagent],[instance],[backupset],[subclient]
            FROM [commserv].[dbo].[CommCellBkScheduleForSubclients] WHERE [clientName]='{0}' AND [idaagent]='{1}'""". \
                format(client, agent)
        elif all([client]) and not any([agent, backup_set, sub_client, schedule, schedule_type]):
            schedule_sql = """SELECT [CommCellId],[CommCellName],[scheduleId],[scheduePolicy],[scheduleName],[scheduletask],[schedbackuptype],[schedpattern],[schedinterval]
            ,[schedbackupday],[schedbackupTime],[schednextbackuptime],[appid],[clientName],[idaagent],[instance],[backupset],[subclient]
            FROM [commserv].[dbo].[CommCellBkScheduleForSubclients] WHERE [clientName]='{0}'""". \
                format(client)
        else:
            self.msg = "至少传入一个参数。"
            return []
        schedules = []

        content = self.fetch_all(schedule_sql)
        for i in content:
            schedules.append({
                # "CommCellId": i[0],
                # "CommCellName": i[1],
                "scheduleId": i[2],
                "scheduePolicy": i[3],
                "scheduleName": i[4],
                "scheduletask": i[5],
                "schedbackuptype": i[6],
                "schedpattern": i[7],
                "schedinterval": i[8],
                "schedbackupday": i[9],
                # "schedbackupTime": i[10],
                # "schednextbackuptime": i[11],
                "appid": i[12],
                "clientName": i[13],
                "idaagent": i[14],
                "instance": i[15],
                "backupset": i[16],
                "subclient": i[17],
            })
        return schedules

    def get_all_backup_jobs(self):
        """
        :return:
        """
        status_list = {"Running": "运行", "Waiting": "等待", "Pending": "阻塞", "Suspend": "终止", "Completed": "正常",
                       "Failed": "失败", "Failed to Start": "启动失败", "Killed": "杀掉",
                       "Completed w/ one or more errors": "已完成，但有一个或多个错误",
                       "Completed w/ one or more warnings": "已完成，但有一个或多个警告"}

        job_sql = """SELECT [jobid],[clientname],[idataagent],[instance],[backupset],[subclient],[data_sp],[backuplevel],[incrlevel],[jobstatus],[jobfailedreason],[startdate],[enddate],[totalBackupSize]
                    FROM [commserv].[dbo].[CommCellBackupInfo]
                    ORDER BY [startdate] DESC"""
        content = self.fetch_all(job_sql)
        backup_jobs = []
        for i in content:
            backup_jobs.append({
                "jobid": i[0],
                "clientname": i[1],
                "idataagent": i[2],
                "instance": i[3],
                "backupset": i[4],
                "subclient": i[5],
                "data_sp": i[6],
                "backuplevel": i[7],
                "incrlevel": i[8],
                "jobstatus": i[9],
                "jobfailedreason": i[10],
                "startdate": i[11],
                "enddate": i[12],
                "totalBackupSize": i[13],
            })

        extra_content = self.get_installed_sub_clients_for_status()
        # 去重
        extra_content = remove_duplicate_for_status(extra_content)
        whole_list = []

        for backup_job in backup_jobs:
            for content in extra_content:
                if content['clientname'] == backup_job['clientname'] and content['idataagent'] == backup_job[
                        'idataagent']:
                    whole_list.append({
                        "clientname": backup_job['clientname'],
                        "idataagent": backup_job['idataagent'],
                        "data_sp": backup_job['data_sp'],
                        "jobstatus": backup_job['jobstatus'],
                        "startdate": backup_job['startdate'],
                    })
                    # 剔除已经包含的
                    extra_content.remove({
                        "clientname": backup_job['clientname'],
                        "idataagent": backup_job['idataagent'],
                    })
        # 未包含的置空
        for e_content in extra_content:
            whole_list.append({
                "clientname": e_content['clientname'],
                "idataagent": e_content['idataagent'],
                "data_sp": '无',
                "jobstatus": '无',
                "startdate": '无',
            })

        return whole_list

    def get_all_auxcopys(self):
        auxcopy_sql = """SELECT [storagepolicy], [jobstatus], [sourcecopyid], [destcopyid], [bytesxferred], [startdate] FROM [commserv].[dbo].[CommCellAuxCopyInfo] 
                        WHERE [destcopyid] != '' ORDER BY [startdate] DESC"""
        content = self.fetch_all(auxcopy_sql)
        auxcopys = []
        for i in content:
            start_time = "{:%Y-%m-%d %H:%M:%S}".format(i[5].replace(tzinfo=datetime.timezone.utc).astimezone(
                datetime.timezone(datetime.timedelta(hours=8)))) if i[5] else ""

            auxcopys.append({
                "storagepolicy": i[0],
                "jobstatus": i[1],
                "sourcecopyid": i[2],
                "destcopyid": i[3],
                "bytesxferred": i[4],
                "startdate": start_time,
            })
        return auxcopys

    def get_library_list(self):
        """
        获取库列表
        :return:
        """
        pass

    def get_library_info(self, library_name):
        """
        获取库信息
        :param library_name:
        :return:
        """
        pass

    def get_DDB_info(self):
        """
        获取DDB空间容量等信息
        :return:
        """
        ddb_sql = """SELECT [MAName],[Volume],[TotalCapacityMB],[FreeDiskSpaceMB],[TotalSpaceUsedMB],[totalActiveDedupPartitions],[totalSealedDedupPartitions]
                     FROM [CommServ].[dbo].[DDBView]"""
        content = self.fetch_all(ddb_sql)
        ddb_info = []
        for i in content:
            ddb_info.append({
                "MAName": i[0],
                "Volume": i[1],
                "TotalCapacityMB": i[2],
                "FreeDiskSpaceMB": i[3],
                "TotalSpaceUsedMB": i[4],
                "totalActiveDedupPartitions": i[5],
                "totalSealedDedupPartitions": i[6],
            })
        return ddb_info

    def get_automatic_clients(self):
        automatic_clients_sql = """SELECT [id],[name],[type],[ClientGroupBkpEnable],[ClientGroupRstEnable],[clientnames]
                                    FROM [CommServ].[dbo].[CommCellClientGroupConfig]
                                    WHERE [type]='automatic' AND [name]='Index Servers';"""
        content = self.fetch_one(automatic_clients_sql)
        automatic_clients = []

        if content:
            for i in content[5].split(','):
                automatic_clients.append(i)
        return automatic_clients

    def get_library_space_info(self):
        library_space_sql = """SELECT cmaiv.DisplayName, cmiv.LibraryName, cmpv.MountPathName, cmpv.CapacityAvailable, cmpv.SpaceReserved, cmiv.TotalSpaceMB, cmiv.LastBackupTime, cmpv.Offline
        FROM CommServ.dbo.CNMMMountPathView AS cmpv
        LEFT JOIN CommServ.dbo.CNMMMediaInfoView AS cmiv ON cmiv.TotalFreeSpaceMB=(cmpv.CapacityAvailable+cmpv.SpaceReserved) AND cmiv.LibraryID=cmpv.LibraryID
        LEFT JOIN CommServ.dbo.CNMMMALibraryView AS cmalv ON cmalv.LibraryID=cmpv.LibraryID
        LEFT JOIN CommServ.dbo.CNMMMAInfoView AS cmaiv ON cmaiv.MediaAgentID=cmalv.MediaAgentID
        ORDER BY cmaiv.DisplayName ASC, cmiv.LibraryName ASC"""
        content = self.fetch_all(library_space_sql)
        library_space_info = []
        for i in content:
            library_space_info.append({
                "DisplayName": i[0],
                "LibraryName": i[1],
                "MountPathName": i[2],
                "CapacityAvailable": i[3],
                "SpaceReserved": i[4],
                "TotalSpaceMB": i[5],
                "LastBackupTime": i[6],
                "Offline": i[7],
            })
        return library_space_info

    def get_commserv_info(self):
        commserv_info_sql = """SELECT cn.SWVersion, cn.ServicePack, cn.OSName, ac.CCHostName FROM CommServ.dbo.CNCommCellInfoView AS cn
        INNER JOIN CommServ.dbo.APP_CommCellInfo AS ac ON ac.commcellId=cn.id;"""
        commserv_info = []
        commserv_info = self.fetch_one(commserv_info_sql)

        return commserv_info

    def get_oracle_backup_job_list(self, client_name):
        oracle_backup_sql = """SELECT DISTINCT [jobid],[backuplevel],[startdate],[enddate],[instance], [nextSCN], [idataagent], [subclient], [storagePolicy], [numbytesuncomp]
                            FROM [CommServ].[dbo].[CommCellOracleBackupInfo] 
                            WHERE [jobstatus]='Success' AND [clientname]='{0}' AND [subclient]='default' AND [backuplevel]='Online Full' ORDER BY [startdate] DESC;""".format(client_name)
        content = self.fetch_all(oracle_backup_sql)
        oracle_backuplist = []
        for i in content:
            next_SCN = i[5]
            idataagent = i[6]
            cur_SCN = ""
            if next_SCN:
                if idataagent == "Oracle RAC":
                    com = re.compile(" \d+")
                    all_next_SCN = com.findall(next_SCN)
                    if all_next_SCN:
                        try:
                            first_rac_SCN = int(all_next_SCN[0].strip())
                            second_rac_SCN = int(all_next_SCN[1].strip())
                        except Exception as e:
                            print("SCN:", e)
                        else:
                            if first_rac_SCN > second_rac_SCN:
                                cur_SCN = first_rac_SCN - 1
                            else:
                                cur_SCN = second_rac_SCN - 1
                if idataagent == "Oracle Database":
                    try:
                        cur_SCN = int(next_SCN) - 1
                    except:
                        pass

            start_time = "{:%Y-%m-%d %H:%M:%S}".format(i[2].replace(tzinfo=datetime.timezone.utc).astimezone(
                datetime.timezone(datetime.timedelta(hours=8)))) if i[2] else ""
            last_time = "{:%Y-%m-%d %H:%M:%S}".format(i[3].replace(tzinfo=datetime.timezone.utc).astimezone(
                datetime.timezone(datetime.timedelta(hours=8)))) if i[3] else ""

            oracle_backuplist.append({
                "jobId": i[0],
                "jobType": "Backup",
                "Level": i[1],
                "StartTime": start_time,
                "LastTime": last_time,
                "instance": i[4],
                "cur_SCN": cur_SCN,
                "subclient": i[7],
                "data_sp": i[8],
                "numbytesuncomp": i[9],
                "idataagent": idataagent,
            })
        return oracle_backuplist

    def has_auxiliary_job(self, backup_job_id):
        """
        判断是否可以选择辅助拷贝来恢复
        :param backup_job_id:
        :return:
        """
        tmp_sql = """
        SELECT [jobId], [auxCopyJobId], [status], [copiedTime]
        FROM [commserv].[dbo].[JMJobDataStats]
        WHERE [jobId] = {backup_job_id}
        """.format(backup_job_id=backup_job_id)
        content = self.fetch_all(tmp_sql)
        ret = False
        for c in content:
            if c[1] and c[2] == 100 and c[3]:
                ret = True
                break
        return ret

    def get_job_controller(self):
        job_controller_sql = """SELECT [jobID],[operation],[clientComputer],[agentType],[subclient]
                                ,[jobType],[phase],[storagePolicy],[mediaAgent],[status],[progress],[errors],[delayReason],[description]
                                ,[scheduleId],[instanceName]
                                FROM [CommServ].[dbo].[CommCellJobController];"""
        content = self.fetch_all(job_controller_sql)
        job_controller_list = []
        for i in content:
            job_controller_list.append({
                "jobID": i[0],
                "operation": i[1],
                "clientComputer": i[2],
                "agentType": i[3],
                "storagePolicy": i[7],
                "progress": i[10],
                "delayReason": i[12],
                "instanceName": i[15],
            })
        return job_controller_list

    def updateCVUTC(self):
        # utc_sql = """SELECT [timeZone]  FROM [CommServ].[dbo].[APP_CommCell],[CommServ].[dbo].[SchedTimeZone] where [timeZone]='0:-480:'  + [timeZonename] and  [id]=2 and TimeZoneStdName='China Standard Time';"""
        # content = self.fetch_all(utc_sql)
        # job_controller_list = []
        # if len(content) > 0 and content[0][0] != "0:-480:(UTC+08:00) 北京，重庆，香港特别行政区，乌鲁木齐":
        #     update_sql = """update [CommServ].[dbo].[APP_CommCell] set [timeZone] =N'0:-480:(UTC+08:00) 北京，重庆，香港特别行政区，乌鲁木齐'
        #                                  where [id]=2;"""
        #     self.execute(update_sql)
        utc_sql = """SELECT [timeZone]  FROM [CommServ].[dbo].[APP_CommCell],[CommServ].[dbo].[SchedTimeZone] where [timeZone]='0:-480:'  + [timeZonename] and  [id]=2 and TimeZoneStdName='China Standard Time';"""
        content = self.fetch_all(utc_sql)
        job_controller_list = []
        if len(content) <= 0:
            update_sql = """update [CommServ].[dbo].[APP_CommCell] set [timeZone] ='0:-480:' + (select [timeZonename] from [CommServ].[dbo].[SchedTimeZone] where TimeZoneStdName='China Standard Time')
                                             where [id]=2;"""
            self.execute(update_sql)

    def get_backup_status(self, selected_clients):
        """
        获取备份状态： 备份状态、辅助拷贝状态
        """
        status_list = {
            "Running": "运行", "Waiting": "等待", "Pending": "阻塞", "Suspend": "终止", "Completed": "正常",
            "Failed": "失败", "Failed to Start": "启动失败", "Killed": "杀掉",
            "Completed w/ one or more errors": "已完成，但有一个或多个错误",
            "Completed w/ one or more warnings": "已完成，但有一个或多个警告", "Success": "成功"
        }
        backup_status_sql = """SELECT ccbi.clientname, ccbi.idataagent, ccbi.instance, ccbi.backupset, ccbi.subclient, ccbi.startdate, ccbi.jobstatus bk_status, ccaci.jobstatus aux_status
        FROM commserv.dbo.CommCellBackupInfo AS ccbi
        LEFT JOIN commserv.dbo.CommCellClientConfig AS cccc ON ccbi.clientname=cccc.Client AND cccc.ClientStatus='installed'
        LEFT JOIN commserv.dbo.CommCellAuxCopyInfo AS ccaci ON CAST(ccaci.storagepolicy AS char)= CAST(ccbi.data_sp AS char)
        ORDER BY ccbi.clientname DESC, ccbi.idataagent DESC, ccbi.instance DESC, ccbi.backupset DESC, ccbi.subclient DESC, ccbi.startdate DESC
        """
        content = self.fetch_all(backup_status_sql)

        backup_status_list = []
        pre_clientname = ""
        pre_idataagent = ""
        pre_instance = ""
        pre_backupset = ""
        pre_subclient = ""
        
        
        
        # 客户端 应用类型
        for c in content:
            # 去重
            if c[0] == pre_clientname and c[1] == pre_idataagent and c[2] == pre_instance and c[3] == pre_backupset and c[4] == pre_subclient:
                continue
            
            # 在指定客户端列表内
            if c[0] in selected_clients:
                bk_status = c[6]
                aux_status = c[7]
                try:
                    bk_status = status_list[bk_status]
                except:
                    pass
                try:
                    aux_status = status_list[aux_status]
                except:
                    pass           
                backup_status_list.append({
                    "clientname": c[0],
                    "idataagent": c[1],
                    "instance": c[2],
                    "backupset": c[3],
                    "subclient": c[4],
                    "startdate": c[5],
                    "bk_status": bk_status if bk_status else "无",
                    "aux_status": aux_status if aux_status else "无"
                })
                pre_clientname = c[0]
                pre_idataagent = c[1]
                pre_instance = c[2]
                pre_backupset = c[3]
                pre_subclient = c[4]
        return backup_status_list

    def get_backup_content(self, selected_clients):
        pass


class CustomFilter(CVApi):
    def custom_all_backup_content(self, client_manage_list):
        whole_content_list = []

        tmp_clients = self.get_all_install_clients()

        all_clients = []
        for client_manage in tmp_clients:
            if client_manage["client_name"] in client_manage_list:
                all_clients.append(client_manage)

        # 所有备份内容的列表
        all_content_list = self.get_all_backup_content()
        client_row_list = []
        agent_row_list = []
        backupset_row_list = []
        subclient_row_list = []
        content_row_list = []

        for client in all_clients:
            specific_content_one = []
            for content_one in all_content_list:
                if content_one["clientname"] == client["client_name"]:
                    # 当前客户端所有备份列表
                    specific_content_one.append(content_one)

            if len(specific_content_one) != 0:
                # 当前客户端的rowspan
                client_row_list.append(len(specific_content_one))

            agent_list = []
            for one in specific_content_one:
                if one["idataagent"] not in agent_list:
                    # 当前客户端下，所有agent
                    agent_list.append(one["idataagent"])
            for agent in agent_list:

                specific_content_two = []
                for content_two in all_content_list:
                    if content_two["clientname"] == client["client_name"] and content_two["idataagent"] == agent:
                        # 当前客户端/agent下所有备份列表
                        specific_content_two.append(content_two)
                # 当前客户端/agent的rowspan
                agent_row_list.append(len(specific_content_two))

                backup_set_list = []
                for two in specific_content_two:
                    if two["backupset"] not in backup_set_list:
                        # 当前客户端/agent下所有backupset
                        backup_set_list.append(two["backupset"])
                for backup_set in backup_set_list:

                    specific_content_three = []
                    for content_three in all_content_list:
                        if content_three["clientname"] == client["client_name"] and content_three[
                                "idataagent"] == agent and content_three["backupset"] == backup_set:
                            # 当前客户端/agent/backupset下所有备份列表
                            specific_content_three.append(content_three)
                    # 当前客户端/agent/backupset的rowspan
                    backupset_row_list.append(len(specific_content_three))

                    # sub_client_list = []
                    # for three in specific_content_three:
                    #     if three["subclient"] not in sub_client_list:
                    #         sub_client_list.append(three["subclient"])
                    # # ...
                    # for sub_client in sub_client_list:
                    #
                    #     specific_content_four = []
                    #     for content_four in all_content_list:
                    #         if content_four["clientname"] == client["client_name"] and content_four["idataagent"] == agent and content_four["backupset"] == backup_set and content_four["subclient"] == sub_client:
                    #             specific_content_four.append(content_four)
                    #
                    #     subclient_row_list.append(len(specific_content_four))

                    content_list = []
                    for three in specific_content_three:
                        if three["content"] not in content_list:
                            # 当前客户端/agent/backupset下所有备份内容
                            content_list.append(three["content"])

                    for content in content_list:

                        specific_content_five = []
                        for content_five in all_content_list:
                            if content_five["clientname"] == client["client_name"] and content_five[
                                    "idataagent"] == agent and content_five["backupset"] == backup_set and content_five[
                                    "content"] == content:
                                # 当前客户端/agent/backupset/备份内容的列表
                                specific_content_five.append(content_five)

                        content_row_list.append(len(specific_content_five))

                        if specific_content_five:
                            whole_content_list.extend(specific_content_five)

        row_dict = {
            "client_row_list": client_row_list,
            "agent_row_list": agent_row_list,
            "backupset_row_list": backupset_row_list,
            # "subclient_row_list": subclient_row_list,
            "content_row_list": content_row_list,
        }
        return whole_content_list, row_dict

    def custom_all_storages(self, client_manage_list):
        whole_storage_list = []

        tmp_clients = self.get_all_install_clients()

        all_clients = []
        for client_manage in tmp_clients:
            if client_manage["client_name"] in client_manage_list:
                all_clients.append(client_manage)

        all_storage_list = self.get_all_storage()

        client_row_list = []
        agent_row_list = []
        backupset_row_list = []
        # subclient_row_list = []
        storage_row_list = []

        for client in all_clients:
            specific_storage_one = []
            for storage_one in all_storage_list:
                if storage_one["clientname"] == client["client_name"]:
                    specific_storage_one.append(storage_one)

            if len(specific_storage_one) != 0:
                client_row_list.append(len(specific_storage_one))

            agent_list = []
            for one in specific_storage_one:
                if one["idataagent"] not in agent_list:
                    agent_list.append(one["idataagent"])
            for agent in agent_list:

                specific_storage_two = []
                for storage_two in all_storage_list:
                    if storage_two["clientname"] == client["client_name"] and storage_two["idataagent"] == agent:
                        specific_storage_two.append(storage_two)

                agent_row_list.append(len(specific_storage_two))

                backup_set_list = []
                for two in specific_storage_two:
                    if two["backupset"] not in backup_set_list:
                        backup_set_list.append(two["backupset"])
                for backup_set in backup_set_list:

                    specific_storage_three = []
                    for storage_three in all_storage_list:
                        if storage_three["clientname"] == client["client_name"] and storage_three[
                                "idataagent"] == agent and storage_three["backupset"] == backup_set:
                            specific_storage_three.append(storage_three)

                    backupset_row_list.append(len(specific_storage_three))

                    # sub_client_list = []
                    # for three in specific_storage_three:
                    #     if three["subclient"] not in sub_client_list:
                    #         sub_client_list.append(three["subclient"])
                    # for sub_client in sub_client_list:
                    #
                    #     specific_storage_four = []
                    #     for storage_four in all_storage_list:
                    #         if storage_four["clientname"] == client["client_name"] and storage_four["idataagent"] == agent and storage_four["backupset"] == backup_set and storage_four["subclient"] == sub_client:
                    #             specific_storage_four.append(storage_four)
                    #
                    #     subclient_row_list.append(len(specific_storage_four))

                    storage_list = []
                    for three in specific_storage_three:
                        if three["storagepolicy"] not in storage_list:
                            storage_list.append(three["storagepolicy"])
                    for storage in storage_list:

                        specific_storage_five = []
                        for storage_five in all_storage_list:
                            if storage_five["clientname"] == client["client_name"] and storage_five[
                                    "idataagent"] == agent and storage_five["backupset"] == backup_set and storage_five[
                                    "storagepolicy"] == storage:
                                specific_storage_five.append(storage_five)

                        storage_row_list.append(len(specific_storage_five))

                        if specific_storage_five:
                            whole_storage_list.extend(specific_storage_five)

        row_dict = {
            "client_row_list": client_row_list,
            "agent_row_list": agent_row_list,
            "backupset_row_list": backupset_row_list,
            # "subclient_row_list": subclient_row_list,
            "storage_row_list": storage_row_list,
        }
        return whole_storage_list, row_dict

    def custom_all_schedules(self, client_manage_list):
        whole_schedule_list = []
        # 1.排序
        tmp_clients = self.get_all_install_clients()

        all_clients = []
        for client_manage in tmp_clients:
            if client_manage["client_name"] in client_manage_list:
                all_clients.append(client_manage)

        # 2.所有schedule的列表
        all_schedule_list = self.get_all_schedules()

        client_row_list = []
        agent_row_list = []
        backupset_row_list = []
        subclient_row_list = []
        schedule_row_list = []
        schedule_type_row_list = []

        for client in all_clients:
            # specific_schedule_one = self.get_schedules(client=client["client_name"])  # 请求的方式

            # 遍历的方式
            specific_schedule_one = []
            for schedule_one in all_schedule_list:
                if schedule_one["clientName"] == client["client_name"]:
                    specific_schedule_one.append(schedule_one)

            if len(specific_schedule_one) != 0:
                client_row_list.append(len(specific_schedule_one))

            agent_list = []
            for one in specific_schedule_one:
                if one["idaagent"] not in agent_list:
                    agent_list.append(one["idaagent"])
            for agent in agent_list:
                # specific_schedule_two = self.get_schedules(client=client["client_name"], agent=agent)

                specific_schedule_two = []
                for schedule_two in all_schedule_list:
                    if schedule_two["clientName"] == client["client_name"] and schedule_two["idaagent"] == agent:
                        specific_schedule_two.append(schedule_two)

                agent_row_list.append(len(specific_schedule_two))

                backup_set_list = []
                for two in specific_schedule_two:
                    if two["backupset"] not in backup_set_list:
                        backup_set_list.append(two["backupset"])
                for backup_set in backup_set_list:

                    specific_schedule_three = []
                    for schedule_three in all_schedule_list:
                        if schedule_three["clientName"] == client["client_name"] and schedule_three[
                                "idaagent"] == agent and schedule_three["backupset"] == backup_set:
                            specific_schedule_three.append(schedule_three)

                    backupset_row_list.append(len(specific_schedule_three))

                    # sub_client_list = []
                    # for three in specific_schedule_three:
                    #     if three["subclient"] not in sub_client_list:
                    #         sub_client_list.append(three["subclient"])
                    # for sub_client in sub_client_list:
                    #
                    #     specific_schedule_four = []
                    #     for schedule_four in all_schedule_list:
                    #         if schedule_four["clientName"] == client["client_name"] and schedule_four["idaagent"] == agent and schedule_four["backupset"] == backup_set and schedule_four["subclient"] == sub_client:
                    #             specific_schedule_four.append(schedule_four)
                    #
                    #     subclient_row_list.append(len(specific_schedule_four))

                    schedule_list = []
                    for three in specific_schedule_three:
                        if three["scheduePolicy"] not in schedule_list:
                            schedule_list.append(three["scheduePolicy"])
                    for schedule in schedule_list:

                        specific_schedule_five = []
                        for schedule_five in all_schedule_list:
                            if schedule_five["clientName"] == client["client_name"] and schedule_five[
                                    "idaagent"] == agent and schedule_five["backupset"] == backup_set and schedule_five[
                                    "scheduePolicy"] == schedule:
                                specific_schedule_five.append(schedule_five)

                        schedule_row_list.append(len(specific_schedule_five))

                        schedules = []
                        for five in specific_schedule_five:
                            if five["schedbackuptype"] not in schedules:
                                schedules.append(five["schedbackuptype"])
                        for c_schedule in schedules:

                            specific_schedule_six = []
                            for schedule_six in all_schedule_list:
                                if schedule_six["clientName"] == client["client_name"] and schedule_six[
                                        "idaagent"] == agent and schedule_six["backupset"] == backup_set and schedule_six[
                                        "scheduePolicy"] == schedule and schedule_six[
                                        "schedbackuptype"] == c_schedule:
                                    specific_schedule_six.append(schedule_six)

                            schedule_type_row_list.append(
                                len(specific_schedule_six))

                            if specific_schedule_six:
                                whole_schedule_list.extend(
                                    specific_schedule_six)

        row_dict = {
            "client_row_list": client_row_list,
            "agent_row_list": agent_row_list,
            "backupset_row_list": backupset_row_list,
            "subclient_row_list": subclient_row_list,
            "schedule_row_list": schedule_row_list,
            "schedule_type_row_list": schedule_type_row_list,
        }
        return whole_schedule_list, row_dict

    def custom_concrete_job_list(self, client_manage_list):
        """
        并发请求所有agent下的job
        :param cv_api:
        :param client_id:
        :param client_name:
        :return:
        """
        status_list = {"Running": "运行", "Waiting": "等待", "Pending": "阻塞", "Suspend": "终止", "Completed": "正常",
                       "Failed": "失败", "Failed to Start": "启动失败", "Killed": "杀掉",
                       "Completed w/ one or more errors": "已完成，但有一个或多个错误",
                       "Completed w/ one or more warnings": "已完成，但有一个或多个警告", "Success": "成功"}
        whole_list = []
        job_list = self.get_all_backup_jobs()
        tmp_clients = self.get_all_install_clients()

        all_clients = []
        for client_manage in tmp_clients:
            if client_manage["client_name"] in client_manage_list:
                all_clients.append(client_manage)

        all_auxcopys = self.get_all_auxcopys()
        for client in all_clients:
            agent_job_list = []
            pre_agent_list = []

            for job in job_list:
                if job["idataagent"] not in pre_agent_list and job["clientname"] == client["client_name"] and "Oracle" in job["idataagent"]:
                    pre_agent_list.append(job["idataagent"])

                    job_status = job["jobstatus"]
                    try:
                        job_status_str = status_list[job_status]
                    except:
                        job_status_str = job_status

                    if job_status_str in ["运行", "正常", "等待", "QueuedCompleted", "Queued", "PartialSuccess", "成功"]:
                        status_label = "label label-sm label-success"
                    elif job_status_str in ["阻塞", "已完成，但有一个或多个错误", "已完成，但有一个或多个警告"]:
                        status_label = "label label-sm label-warning"
                    elif job_status_str == '无':
                        status_label = ''
                    else:
                        status_label = "label label-sm label-danger"

                    # 匹配辅助拷贝
                    aux_copy_status = "无"
                    for auxcopy in all_auxcopys:
                        if auxcopy["storagepolicy"] == job["data_sp"]:
                            aux_copy_status = auxcopy["jobstatus"]

                    try:
                        aux_copy_status_str = status_list[aux_copy_status]
                    except:
                        aux_copy_status_str = aux_copy_status

                    if aux_copy_status_str in ["运行", "正常", "等待", "QueuedCompleted", "Queued", "PartialSuccess", "成功"]:
                        aux_status_label = "label label-sm label-success"
                    elif aux_copy_status_str in ["阻塞", "已完成，但有一个或多个错误", "已完成，但有一个或多个警告"]:
                        aux_status_label = "label label-sm label-warning"
                    elif aux_copy_status_str == '无':
                        aux_status_label = ''
                    else:
                        aux_status_label = "label label-sm label-danger"
                    agent_job_list.append({
                        "client_name": client["client_name"],
                        "agent_type_name": job["idataagent"],
                        "job_start_time": job["startdate"].strftime("%Y-%m-%d %H:%M:%S") if job["startdate"] != '无' else
                        job["startdate"],
                        "job_backup_status": job_status_str,
                        "status_label": status_label,
                        "aux_copy_status": aux_copy_status_str,
                        "aux_status_label": aux_status_label,
                    })
            if agent_job_list:
                whole_list.append({
                    "agent_job_list": agent_job_list,
                    "agent_length": len(agent_job_list)
                })
        return whole_list


def remove_duplicate_for_info(dict_list):
    seen = set()
    new_dict_list = []
    for dict in dict_list:
        t_dict = {'clientname': dict['clientname'],
                  'idataagent': dict['idataagent'], 'backupset': dict['backupset']}
        t_tup = tuple(t_dict.items())
        if t_tup not in seen:
            seen.add(t_tup)
            new_dict_list.append(dict)
    return new_dict_list


def remove_duplicate_for_status(dict_list):
    seen = set()
    new_dict_list = []
    for dict in dict_list:
        t_dict = {'clientname': dict['clientname'],
                  'idataagent': dict['idataagent']}
        t_tup = tuple(t_dict.items())
        if t_tup not in seen:
            seen.add(t_tup)
            new_dict_list.append(dict)
    return new_dict_list


if __name__ == '__main__':
    credit = {
        "host": "gl.sjbh.jx\COMMVAULT",
        "user": "sa_cloud",
        "password": "1qaz@WSX",
        "database": "CommServ",
    }
    dm = CustomFilter(credit)
    print(dm.get_instance_from_oracle())
