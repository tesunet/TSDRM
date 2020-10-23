import datetime
from datetime import timedelta
import copy
# from TSDRM import settings
# from faconstor.CVApi_bak import *
import re
import pyodbc


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
            connection = pyodbc.connect('DRIVER={SQL Server};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s' % (
                self.host, self.database, self.user, self.password))

            # connection = pymssql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
        except Exception as e:
            self.msg = "链接数据库失败。"
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

    def isconnected(self):
        return self._conn


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

    def get_all_instance(self):
        # instance_sql = """SELECT DISTINCT [clientname],[idataagent],[instance], [clientid]
        #                   FROM [commserv].[dbo].[CommCellSubClientConfig]
        #                   WHERE [idataagentstatus] = 'installed' AND [instance] IS NOT NULL AND [instance] != ''
        #                   AND [idataagent] LIKE 'Oracle%';"""
        instance_sql = """SELECT [clientid],[clientname],[idataagent],[instance],[backupset]
                    FROM [commserv].[dbo].[CommCellSubClientConfig] 
                    WHERE [backupset]!='Indexing BackupSet' AND [subclient]!='(command line)' 
                    ORDER BY [clientname] DESC, [idataagent] DESC, [instance] DESC, [backupset] DESC, [subclient] DESC"""
        ret = self.fetch_all(instance_sql)
        pre_clientname = ""
        pre_idataagent = ""
        pre_instance = ""
        pre_backupset = ""

        instance_list = []
        # 客户端 应用类型
        for c in ret:
            # 去重
            if c[0] == pre_clientname and c[1] == pre_idataagent and c[2] == pre_instance and c[3] == pre_backupset:
                continue
            type = c[4]
            if "File System" in c[2] or "Virtual" in c[2] or "Big Data Apps" in c[2]:
                type = c[4]
            if "Oracle" in c[2] or "SQL Server" in c[2] or "MySQL" in c[2] or "Exchange Database" in c[2]:
                type = c[3]
            instance_list.append({
                "clientid": c[0],
                "clientname": c[1],
                "agent": c[2],
                "instance": type
            })
            pre_clientname = c[0]
            pre_idataagent = c[1]
            pre_instance = c[2]
            pre_backupset = c[3]
        return instance_list

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

    def get_all_backup_jobs(self, full=False, success=False):
        """
        :return:
        """
        status_list = {"Running": "运行", "Waiting": "等待", "Pending": "阻塞", "Suspend": "终止", "Completed": "正常",
                       "Failed": "失败", "Failed to Start": "启动失败", "Killed": "杀掉",
                       "Completed w/ one or more errors": "已完成，但有一个或多个错误",
                       "Completed w/ one or more warnings": "已完成，但有一个或多个警告"}
        job_sql = """SELECT [jobid],[clientname],[idataagent],[instance],[backupset],[subclient],[data_sp],[backuplevel],[incrlevel],[jobstatus],[jobfailedreason],[startdate],[enddate],[totalBackupSize], [numbytescomp], [numbytesuncomp]
                        FROM [commserv].[dbo].[CommCellBackupInfo]
                        ORDER BY [startdate] DESC"""
        if full and success:
            job_sql = """SELECT [jobid],[clientname],[idataagent],[instance],[backupset],[subclient],[data_sp],[backuplevel],[incrlevel],[jobstatus],[jobfailedreason],[startdate],[enddate],[totalBackupSize], [numbytescomp], [numbytesuncomp]
                        FROM [commserv].[dbo].[CommCellBackupInfo] WHERE [backuplevel] LIKE '%Full%' AND [jobstatus] LIKE '%Success%'
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
                "numbytescomp": i[14],  # 备份大小
                "numbytesuncomp": i[15],  # 应用大小
            })

        return backup_jobs

    def get_all_auxcopys(self):
        auxcopy_sql = """SELECT [storagepolicy], [jobstatus], [sourcecopyid], [destcopyid] FROM [commserv].[dbo].[CommCellAuxCopyInfo] 
        WHERE [destcopyid] != '' ORDER BY [startdate] DESC"""
        content = self.fetch_all(auxcopy_sql)
        auxcopys = []
        for i in content:
            auxcopys.append({
                "storagepolicy": i[0],
                "jobstatus": i[1],
                "sourcecopyid": i[2],
                "destcopyid": i[3],
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

    # def get_library_space_info(self):
    #     library_space_sql = """select ma.DisplayName, ls.LibraryName, ls.TotalSpaceMB, ls.TotalFreeSpaceMB from CommServ.dbo.CNMMMediaInfoView as ls
    #                             inner join CommServ.dbo.CNMMMALibraryView as mc on mc.LibraryID = ls.LibraryID
    #                             inner join CommServ.dbo.CNMMMAInfoView as ma on mc.MediaAgentID = ma.MediaAgentID;"""
    #     content = self.fetch_all(library_space_sql)
    #     library_space_info = []
    #     for i in content:
    #         library_space_info.append({
    #             "MAName": i[0],
    #             "LibraryName": i[1],
    #             "TotalSpaceMB": i[2],
    #             "TotalFreeSpaceMB": i[3],
    #         })
    #     return library_space_info
    def get_library_space_info(self):
        library_space_sql = """SELECT cmaiv.DisplayName, cmiv.LibraryName, cmpv.MountPathName, cmpv.CapacityAvailable, cmpv.SpaceReserved, cmiv.TotalSpaceMB, cmiv.LastBackupTime, cmpv.Offline, cmiv.MediaID, cmiv.LibraryID,cmiv.BarCode
        FROM CommServ.dbo.CNMMMountPathView AS cmpv
        LEFT JOIN (SELECT BarCode,LibraryName,TotalSpaceMB,TotalFreeSpaceMB,LibraryID,max(LastBackupTime) LastBackupTime,max(MediaID) MediaID FROM CommServ.dbo.CNMMMediaInfoView GROUP BY LibraryName,TotalSpaceMB,TotalFreeSpaceMB,LibraryID, MediaID,BarCode) AS cmiv ON cmiv.TotalFreeSpaceMB=(cmpv.CapacityAvailable+cmpv.SpaceReserved) AND cmiv.LibraryID=cmpv.LibraryID
        LEFT JOIN CommServ.dbo.CNMMMALibraryView AS cmalv ON cmalv.LibraryID=cmpv.LibraryID
        LEFT JOIN CommServ.dbo.CNMMMAInfoView AS cmaiv ON cmaiv.MediaAgentID=cmalv.MediaAgentID
        WHERE cmpv.offline=0 ORDER BY cmaiv.DisplayName ASC, cmiv.LibraryName ASC"""
        # library_space_sql = """SELECT cmaiv.DisplayName, cmiv.LibraryName, cmpv.MountPathName, cmpv.CapacityAvailable, cmpv.SpaceReserved, cmiv.TotalSpaceMB, cmiv.LastBackupTime, cmpv.Offline, cmiv.MediaID, cmiv.LibraryID
        # FROM CommServ.dbo.CNMMMountPathView AS cmpv
        # LEFT JOIN (SELECT DISTINCT LibraryName,TotalSpaceMB,TotalFreeSpaceMB,LibraryID,max(LastBackupTime) LastBackupTime,max(MediaID) MediaID FROM CommServ.dbo.CNMMMediaInfoView GROUP BY LibraryName,TotalSpaceMB,TotalFreeSpaceMB,LibraryID, MediaID) AS cmiv ON cmiv.TotalFreeSpaceMB=(cmpv.CapacityAvailable+cmpv.SpaceReserved) AND cmiv.LibraryID=cmpv.LibraryID
        # LEFT JOIN CommServ.dbo.CNMMMALibraryView AS cmalv ON cmalv.LibraryID=cmpv.LibraryID
        # LEFT JOIN CommServ.dbo.CNMMMAInfoView AS cmaiv ON cmaiv.MediaAgentID=cmalv.MediaAgentID
        # ORDER BY cmaiv.DisplayName ASC, cmiv.LibraryName ASC"""
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
                "MediaID": i[8],
                "LibraryID": i[9],
                "BarCode": i[10]
            })
        return library_space_info

    def get_ma_info(self):
        library_space_sql = """select ma.MediaAgentID,ma.DisplayName,ma.InterfaceName,ma.OSName,ma.SWVersion,ma.ServicePack,ma.Offline,ma.TotalLibraries,ma.OfflineLibraries,t.TotalSpaceMB,t.TotalFreeSpaceMB,t.SpaceReserved from CommServ.dbo.CNMMMAInfoView ma left join 
		(select cmalv.MediaAgentID MediaAgentID,sum(cmpv.CapacityAvailable) CapacityAvailable, sum(cmpv.SpaceReserved) SpaceReserved, sum(cmiv.TotalSpaceMB) TotalSpaceMB, sum(cmiv.TotalFreeSpaceMB) TotalFreeSpaceMB
				from CommServ.dbo.CNMMMALibraryView AS cmalv
				LEFT JOIN (select sum(TotalFreeSpaceMB) TotalFreeSpaceMB,sum(TotalSpaceMB) TotalSpaceMB,LibraryID,LibraryName from CommServ.dbo.CNMMMediaInfoView group by LibraryID,LibraryName) cmiv on  cmiv.LibraryID= cmalv.LibraryID
				LEFT JOIN (select sum(CapacityAvailable) CapacityAvailable,sum(SpaceReserved) SpaceReserved,LibraryID  from CommServ.dbo.CNMMMountPathView group by LibraryID )AS cmpv on  cmpv.LibraryID= cmalv.LibraryID
				group by cmalv.MediaAgentID) t on  ma.MediaAgentID=t.MediaAgentID;"""
        content = self.fetch_all(library_space_sql)
        library_space_info = []
        for i in content:
            library_space_info.append({
                "MediaAgentID": i[0],
                "DisplayName": i[1],
                "InterfaceName": i[2],
                "OSName": i[3],
                "SWVersion": i[4],
                "ServicePack": i[5],
                "Offline": i[6],
                "TotalLibraries": i[7],
                "OfflineLibraries": i[8],
                "TotalSpaceMB": i[9],
                "TotalFreeSpaceMB": i[10],
                "SpaceReserved": i[11],
            })
        return library_space_info

    def get_commserv_info(self):
        commserv_info_sql = """select cn.SWVersion, cn.ServicePack, cn.OSName, ac.CCHostName from CommServ.dbo.CNCommCellInfoView as cn
                               inner join CommServ.dbo.APP_CommCellInfo as ac on ac.commcellId=cn.id;"""
        commserv_info = []
        commserv_info = self.fetch_one(commserv_info_sql)

        return commserv_info

    def get_oracle_backup_job_list(self, client_name):
        oracle_backup_sql = """SELECT DISTINCT [jobid],[backuplevel],[startdate],[enddate],[instance], [nextSCN], [idataagent], [subclient]
                            FROM [CommServ].[dbo].[CommCellOracleBackupInfo] 
                            WHERE [jobstatus]='Success' AND [clientname]='{0}' ORDER BY [startdate] DESC;""".format(
            client_name)
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
                "subclient": i[7]
            })
        return oracle_backuplist

    def get_all_backup_job_list(self, client_name, agentType, instanceName):
        backuplist = []
        if "Oracle" in agentType:
            backup_sql = """SELECT DISTINCT [jobid],[backuplevel],[startdate],[enddate],[instance], [nextSCN], [idataagent], [subclient]
            FROM [CommServ].[dbo].[CommCellOracleBackupInfo] 
            WHERE [jobstatus]='Success' AND [clientname]='{0}'  AND [idataagent]='{1}'  AND [instance]='{2}' ORDER BY [startdate] DESC;""".format(
                client_name, agentType, instanceName
            )
            content = self.fetch_all(backup_sql)
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

                backuplist.append({
                    "jobId": i[0],
                    "jobType": "Backup",
                    "Level": i[1],
                    "StartTime": start_time,
                    "LastTime": last_time,
                    "instance": i[4],
                    "cur_SCN": cur_SCN,
                    "subclient": i[7]
                })
        else:
            if "SQL Server" in agentType:
                backup_sql = """SELECT DISTINCT [jobid],[backuplevel],[startdate],[enddate],[backupset], [idataagent], [subclient]
                FROM [CommServ].[dbo].[CommCellBackupInfo] 
                WHERE [jobstatus]='Success' AND [clientname]='{0}'  AND [idataagent]='{1}'  AND [instance]='{2}' ORDER BY [startdate] DESC;""".format(
                    client_name, agentType, instanceName
                )
            else:
                backup_sql = """SELECT DISTINCT [jobid],[backuplevel],[startdate],[enddate],[backupset], [idataagent], [subclient]
                FROM [CommServ].[dbo].[CommCellBackupInfo] 
                WHERE [jobstatus]='Success' AND [clientname]='{0}'  AND [idataagent]='{1}'  AND [backupset]='{2}' ORDER BY [startdate] DESC;""".format(
                    client_name, agentType, instanceName
                )
            content = self.fetch_all(backup_sql)
            for i in content:
                idataagent = i[6]
                start_time = "{:%Y-%m-%d %H:%M:%S}".format(i[2].replace(tzinfo=datetime.timezone.utc).astimezone(
                    datetime.timezone(datetime.timedelta(hours=8)))) if i[2] else ""
                last_time = "{:%Y-%m-%d %H:%M:%S}".format(i[3].replace(tzinfo=datetime.timezone.utc).astimezone(
                    datetime.timezone(datetime.timedelta(hours=8)))) if i[3] else ""

                backuplist.append({
                    "jobId": i[0],
                    "jobType": "Backup",
                    "Level": i[1],
                    "StartTime": start_time,
                    "LastTime": last_time,
                    "instance": i[4],
                    "subclient": i[6]
                })
        return backuplist

    def get_all_restore_job_list(self, client_name,agentType,instanceName):
        if "Oracle" in agentType or "SQL Server" in agentType:
            restore_sql = """SELECT DISTINCT [jobid],[starttime],[endtime],[jobstatus]     
            FROM [CommServ].[dbo].[CommCellRestoreInfo]
            WHERE [destclientname]='{0}'  AND [idataagent]='{1}'  AND [instance]='{2}' ORDER BY [starttime] DESC;""".format(
                client_name,agentType,instanceName
            )
        else:
            restore_sql = """SELECT DISTINCT [jobid],[starttime],[endtime],[jobstatus]     
            FROM [CommServ].[dbo].[CommCellRestoreInfo]
            WHERE [destclientname]='{0}'  AND [idataagent]='{1}'  AND [backupset]='{2}' ORDER BY [starttime] DESC;""".format(
                client_name,agentType,instanceName
            )
        content = self.fetch_all(restore_sql)

        restorelist = []
        for i in content:
            start_time = "{:%Y-%m-%d %H:%M:%S}".format(i[1].replace(tzinfo=datetime.timezone.utc).astimezone(
                datetime.timezone(datetime.timedelta(hours=8)))) if i[2] else ""
            last_time = "{:%Y-%m-%d %H:%M:%S}".format(i[2].replace(tzinfo=datetime.timezone.utc).astimezone(
                datetime.timezone(datetime.timedelta(hours=8)))) if i[3] else ""

            restorelist.append({
                "jobid": i[0],
                "jobType": "Restore",
                "starttime": start_time,
                "endtime": last_time,
                "jobstatus": i[3],
            })
        return restorelist

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
                "progress": i[10],
                "delayReason": i[12]
            })
        return job_controller_list

    def updateCVUTC(self):
        utc_sql = """SELECT [timeZone] 
                                FROM [CommServ].[dbo].[APP_CommCell] where [id]=2;"""
        content = self.fetch_all(utc_sql)
        job_controller_list = []
        if len(content) > 0 and content[0][0] != "0:-480:(UTC+08:00)北京，重庆，香港特别行政区，乌鲁木齐":
            update_sql = """update [CommServ].[dbo].[APP_CommCell] set [timeZone] =N'0:-480:(UTC+08:00)北京，重庆，香港特别行政区，乌鲁木齐'
                                         where [id]=2;"""
            self.execute(update_sql)

    def get_clients_info(self, selected_clients=[]):
        clients_sql = """SELECT cccc.[ClientId],cccc.[Client],cccc.[NetworkInterface],cccc.[OS [Version]]],cccc.[Hardware],cccc.[GalaxyRelease],cccc.[InstallTime]
        FROM [commserv].[dbo].[CommCellClientConfig] AS cccc
        WHERE cccc.ClientStatus='installed'

        AND EXISTS(SELECT jobid FROM commserv.dbo.CommCellBackupInfo WHERE cccc.Client=clientname)
        AND EXISTS(SELECT scheduleId FROM commserv.dbo.CommCellBkScheduleForSubclients WHERE clientname=cccc.Client)
        """
        ret = self.fetch_all(clients_sql)
        client_list = []
        automatic_clients = self.get_automatic_clients()

        for c in ret:
            # 不在选择agents列表 不展示 默认都展示
            if c[0] in selected_clients or not selected_clients:  # selected_clients为空
                if c[1] not in automatic_clients:
                    client_list.append({
                        "client_id": c[0],
                        "client_name": c[1],
                        "network_interface": c[2],
                        "os": c[3],
                        "hardware": c[4],
                        "galaxy_release": c[5],
                        "install_time": c[6],
                    })

        return client_list

    def get_backup_status(self, selected_clients=[], selected_agents=[]):
        """
        获取备份状态： 备份状态、辅助拷贝状态
            selected_clients 指定客户端列表
            selected_agents 指定应用列表
        """
        status_list = {
            "Running": "运行", "Waiting": "等待", "Pending": "阻塞", "Suspend": "终止", "Completed": "正常",
            "Failed": "失败", "Failed to Start": "启动失败", "Killed": "杀掉",
            "Completed w/ one or more errors": "已完成，但有一个或多个错误",
            "Completed w/ one or more warnings": "已完成，但有一个或多个警告", "Success": "成功","PartialSuccess":"部分完成"
        }

        backup_status_sql = """SELECT ccbi.clientname, ccbi.idataagent, ccbi.instance, ccbi.backupset, ccbi.subclient, ccbi.startdate, ccbi.jobstatus, ccbi.jobid
        FROM commserv.dbo.CommCellBackupInfo AS ccbi

        WHERE EXISTS(SELECT jobid FROM commserv.dbo.CommCellBackupInfo WHERE ccbi.clientname=clientname AND ccbi.idataagent=idataagent) 
        AND EXISTS(SELECT scheduleId FROM commserv.dbo.CommCellBkScheduleForSubclients WHERE clientname=ccbi.clientname AND idaagent=ccbi.idataagent)

        ORDER BY ccbi.startdate DESC
        """

        backup_status = self.fetch_all(backup_status_sql)
        duplicated_subclients, client_list = self.get_duplicated_subclients()

        aux_copy = self.get_duplicated_aux_copy()

        backup_status_list = []
        for ds in duplicated_subclients:
            catched = False  # 是否匹配到
            for bs in backup_status:
                if bs[0] == ds["clientname"] and bs[1] == ds["idataagent"] and bs[2] == ds["instance"] and bs[3] == ds[
                    "backupset"] and bs[4] == ds["subclient"]:
                    catched = True
                    # 在指定客户端列表内
                    if bs[0] in selected_clients or not selected_clients:  # selected_clients为空
                        bk_status = bs[6]
                        aux_status = "无"
                        # 辅助拷贝
                        for ac in aux_copy:
                            if ac["jobId"] == bs[7]:
                                aux_status = ac["status"]
                                break

                        try:
                            bk_status = status_list[bk_status]
                        except:
                            pass

                        # 判断 实例 或 备份集
                        type = ""
                        # 备份内容
                        if "File System" in bs[1] or "Virtual" in bs[1] or "Big Data Apps" in bs[1]:
                            type = bs[3]
                        if "Oracle" in bs[1] or "SQL Server" in bs[1] or "MySQL" in bs[1] or "Exchange Database" in bs[1]:
                            type = bs[2]

                        # 数据库没有实例 或者 文件系统没有备份集
                        if not type:
                            continue

                        backup_status_list.append({
                            "clientname": bs[0],
                            "idataagent": bs[1],
                            "instance": bs[2],
                            "backupset": bs[3],
                            "subclient": bs[4],
                            "startdate": bs[5],
                            "bk_status": bk_status if bk_status else "无",
                            "aux_status": aux_status,
                            "type": type
                        })
                    break
            if not catched:
                # 添加一条空的
                # 判断 实例 或 备份集
                type = ""
                # 备份内容
                if "File System" in ds['idataagent'] or "Virtual" in ds['idataagent'] or "Big Data Apps" in ds['idataagent']:
                    type = ds['backupset']
                if "Oracle" in ds['idataagent'] or "SQL Server" in ds['idataagent'] or "MySQL" in ds['idataagent'] or "Exchange Database" in ds['idataagent']:
                    type = ds['instance']

                # 数据库没有实例 或者 文件系统没有备份集
                if not type:
                    continue

                backup_status_list.append({
                    "clientname": ds["clientname"],
                    "idataagent": ds["idataagent"],
                    "instance": ds["instance"],
                    "backupset": ds["backupset"],
                    "subclient": ds["subclient"],
                    "startdate": "无",
                    "bk_status": "无",
                    "aux_status": "无",
                    "type": type
                })


        # 排序
        final_list = []
        for ci in client_list:
            for bs in backup_status_list:
                if ci == bs["clientname"]:
                    final_list.append(bs)
        return final_list

    def get_backup_content(self, selected_clients=[], selected_agents=[]):
        """
        获取客户端备份内容
            文件系统 MySQL -> 文件夹
            Oracle SQL Server -> 实例
            VMware -> vmname

            selected_clients 指定客户端列表
            selected_agents 指定应用列表
        """
        backup_content_sql = """SELECT ccscc.clientname, ccscc.idataagent, ccscc.instance, ccscc.backupset, ccscc.subclient, ccvbi.vmname vm_content, cccff.content
        FROM (SELECT clientname, idataagent, instance, backupset, subclient FROM commserv.dbo.CommCellSubClientConfig WHERE backupset!='Indexing BackupSet' AND subclient !='(command line)') AS ccscc
        LEFT JOIN CommServ.dbo.CommCellVMBackupInfo AS ccvbi ON ccvbi.virtualizationclient=ccscc.clientname AND ccvbi.backupset=ccscc.backupset AND ccvbi.subclient=ccscc.subclient
        LEFT JOIN commserv.dbo.CommCellClientFSFilters AS cccff ON cccff.clientname=ccscc.clientname AND cccff.idataagent=ccscc.idataagent AND cccff.backupset=ccscc.backupset AND cccff.subclient=ccscc.subclient AND cccff.subclientstatus='valid'

        WHERE EXISTS(SELECT jobid FROM commserv.dbo.CommCellBackupInfo WHERE ccscc.clientname=clientname AND ccscc.idataagent=idataagent) 
        AND EXISTS(SELECT scheduleId FROM commserv.dbo.CommCellBkScheduleForSubclients WHERE clientname=ccscc.clientname AND idaagent=ccscc.idataagent)
        
        ORDER BY ccscc.clientname DESC, ccscc.idataagent DESC, ccscc.instance DESC, ccscc.backupset DESC, ccscc.subclient DESC
        """

        ret = self.fetch_all(backup_content_sql)

        # 所有全备记录
        job_list = self.get_all_backup_jobs(full=True, success=True)
        # 可用客户端
        client_list = [client["client_name"] for client in self.get_clients_info()]

        backup_content_list = []
        pre_clientname = ""
        pre_idataagent = ""
        pre_instance = ""
        pre_backupset = ""
        pre_subclient = ""
        pre_vm_content = ""
        # 客户端 应用类型
        for c in ret:
            # 不在选择agents列表 不展示 默认都展示
            if selected_agents and c[1] not in selected_agents:
                continue
            # 去重
            if c[0] == pre_clientname and c[1] == pre_idataagent and c[2] == pre_instance and c[3] == pre_backupset and \
                    c[4] == pre_subclient and c[5] == pre_vm_content:
                continue

            # 在指定客户端列表内
            if c[0] in selected_clients or not selected_clients:
                content = ""
                # 备份内容
                if "File System" in c[1] or "MySQL" in c[1]:
                    content = c[6]
                if "Oracle" in c[1] or "SQL Server" in c[1]:
                    content = c[2]
                if "Virtual" in c[1]:
                    content = c[5]

                # 判断 实例 或 备份集
                type = ""
                if "File System" in c[1] or "Virtual" in c[1] or "Big Data Apps" in c[1]:
                    type = c[3]

                if "Oracle" in c[1] or "SQL Server" in c[1] or "MySQL" in c[1] or "Exchange Database" in c[1]:
                    type = c[2]

                # 数据库没有实例 或者 文件系统没有备份集
                if not type:
                    continue

                numbytescomp = 0  # 备份大小
                numbytesuncomp = 0  # 应用大小
                # 备份记录中找到最近全备的 应用大小 备份大小

                # Virtual Server备份内容 为两个客户端 的 备份与应用大小
                # 其他Agent 备份大小为 子客户端的备份与应用大小
                if c[1] == "Virtual Server":
                    for jl in job_list:
                        if jl["clientname"] == c[5]:
                            numbytescomp = jl["numbytescomp"]
                            numbytesuncomp = jl["numbytesuncomp"]
                            break
                else:
                    for jl in job_list:
                        if c[0] == jl["clientname"] and c[1] == jl["idataagent"] and c[2] == jl["instance"] and c[3] == jl[
                            "backupset"] and c[4] == jl["subclient"]:
                            numbytescomp = jl["numbytescomp"]
                            numbytesuncomp = jl["numbytesuncomp"]
                            break

                if c[0] in client_list:
                    backup_content_list.append({
                        "clientname": c[0],
                        "idataagent": c[1],
                        "instance": c[2],
                        "backupset": c[3],
                        "subclient": c[4],
                        "content": content if content else "无",
                        "type": type,
                        "numbytescomp": numbytescomp,
                        "numbytesuncomp": numbytesuncomp,
                    })
                pre_clientname = c[0]
                pre_idataagent = c[1]
                pre_instance = c[2]
                pre_backupset = c[3]
                pre_subclient = c[4]
                pre_vm_content = c[5]

        # 排序
        final_list = []
        for ci in client_list:
            for bc in backup_content_list:
                if ci == bc["clientname"]:
                    final_list.append(bc)
        return final_list

    def get_storage_policy(self, selected_clients=[], selected_agents=[]):
        """
        获取存储策略
            文件系统 MySQL -> 文件夹
            Oracle SQL Server -> 实例
            VMware -> vmname

            selected_clients 指定客户端列表
            selected_agents 指定应用列表
        """
        storage_policy_sql = """SELECT ccscc.clientname, ccscc.idataagent, ccscc.instance, ccscc.backupset, ccscc.subclient, ccsp.storagepolicy
        FROM (SELECT clientname, idataagent, instance, backupset, subclient FROM commserv.dbo.CommCellSubClientConfig WHERE backupset!='Indexing BackupSet' AND subclient !='(command line)') AS ccscc
        LEFT JOIN commserv.dbo.CommCellClientConfig AS cccc ON ccscc.clientname=cccc.Client AND cccc.ClientStatus='installed'
        LEFT JOIN commserv.dbo.CommCellStoragePolicy AS ccsp ON ccsp.clientname=ccscc.clientname AND ccsp.idataagent=ccscc.idataagent AND ccsp.backupset=ccscc.backupset AND ccsp.subclient=ccscc.subclient AND ccsp.hardwarecompress!='Unknown'

        WHERE EXISTS(SELECT jobid FROM commserv.dbo.CommCellBackupInfo WHERE ccscc.clientname=clientname AND ccscc.idataagent=idataagent) 
        AND EXISTS(SELECT scheduleId FROM commserv.dbo.CommCellBkScheduleForSubclients WHERE clientname=ccscc.clientname AND idaagent=ccscc.idataagent)

        ORDER BY ccscc.clientname DESC, ccscc.idataagent DESC, ccscc.instance DESC, ccscc.backupset DESC, ccscc.subclient DESC
        """
        ret = self.fetch_all(storage_policy_sql)
        # 可用客户端
        client_list = [client["client_name"] for client in self.get_clients_info()]

        storage_policy_list = []
        pre_clientname = ""
        pre_idataagent = ""
        pre_instance = ""
        pre_backupset = ""
        pre_subclient = ""

        # 客户端 应用类型
        for c in ret:
            # 不在选择agents列表 不展示 默认都展示
            if selected_agents and c[1] not in selected_agents:
                continue
            # 去重
            if c[0] == pre_clientname and c[1] == pre_idataagent and c[2] == pre_instance and c[3] == pre_backupset and \
                    c[4] == pre_subclient:
                continue

            # 在指定客户端列表内
            if c[0] in selected_clients or not selected_clients:
                # 判断 实例 或 备份集
                type = ""
                if "File System" in c[1] or "Virtual" in c[1] or "Big Data Apps" in c[1]:
                    type = c[3]

                if "Oracle" in c[1] or "SQL Server" in c[1] or "MySQL" in c[1] or "Exchange Database" in c[1]:
                    type = c[2]

                # 数据库没有实例 或者 文件系统没有备份集
                if not type:
                    continue
                if c[0] in client_list:
                    storage_policy_list.append({
                        "clientname": c[0],
                        "idataagent": c[1],
                        "instance": c[2],
                        "backupset": c[3],
                        "subclient": c[4],
                        "storage_policy": c[5] if c[5] else "无",
                        "type": type
                    })
                pre_clientname = c[0]
                pre_idataagent = c[1]
                pre_instance = c[2]
                pre_backupset = c[3]
                pre_subclient = c[4]

        # 排序
        final_list = []
        for ci in client_list:
            for sp in storage_policy_list:
                if ci == sp["clientname"]:
                    final_list.append(sp)
        return final_list

    def get_schedule_policy(self, selected_clients=[], selected_agents=[]):
        """
        获取计划策略
            文件系统 MySQL -> 文件夹
            Oracle SQL Server -> 实例
            VMware -> vmname

            selected_clients 指定客户端列表
            selected_agents 指定应用列表
        """
        schedule_policy_sql = """SELECT ccscc.clientname, ccscc.idataagent, ccscc.instance, ccscc.backupset, ccscc.subclient, ccsfs.scheduleId, ccsfs.scheduePolicy, ccsfs.scheduleName, ccsfs.scheduletask, ccsfs.schedbackuptype, ccsfs.schedpattern,
        ccsfs.schedinterval,ccsfs.schedbackupday,ccsfs.schednextbackuptime,ccsfs.schednextbackuptime
        FROM (SELECT clientname, idataagent, instance, backupset, subclient FROM commserv.dbo.CommCellSubClientConfig WHERE backupset!='Indexing BackupSet' AND subclient !='(command line)') AS ccscc
        LEFT JOIN commserv.dbo.CommCellBkScheduleForSubclients AS ccsfs ON ccsfs.clientname=ccscc.clientname AND ccsfs.instance=ccscc.instance AND ccsfs.idaagent=ccscc.idataagent AND ccsfs.backupset=ccscc.backupset AND ccsfs.subclient=ccscc.subclient

        WHERE EXISTS(SELECT jobid FROM commserv.dbo.CommCellBackupInfo WHERE ccscc.clientname=clientname AND ccscc.idataagent=idataagent) 
        AND EXISTS(SELECT scheduleId FROM commserv.dbo.CommCellBkScheduleForSubclients WHERE clientname=ccscc.clientname AND idaagent=ccscc.idataagent)

        ORDER BY ccscc.clientname DESC, ccscc.idataagent DESC, ccscc.instance DESC, ccscc.backupset DESC, ccscc.subclient DESC, ccsfs.scheduePolicy DESC, ccsfs.schedbackuptype DESC
        """
        ret = self.fetch_all(schedule_policy_sql)
        # 可用客户端
        client_list = [client["client_name"] for client in self.get_clients_info()]

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

        schedule_policy_list = []
        pre_clientname = ""
        pre_idataagent = ""
        pre_instance = ""
        pre_backupset = ""
        pre_subclient = ""
        # 计划策略 备份类型
        pre_schedule_policy = ""
        pre_schedule_backuptype = ""
        pre_schedpattern = ""

        # 客户端 应用类型
        for c in ret:
            schedule_policy_name = c[6] if c[6] else "无"
            # 不在选择agents列表 不展示 默认都展示
            if selected_agents and c[1] not in selected_agents:
                continue
            # 去重
            if c[0] == pre_clientname and c[1] == pre_idataagent and c[2] == pre_instance and c[3] == pre_backupset \
                    and c[4] == pre_subclient and schedule_policy_name == pre_schedule_policy and c[9] == pre_schedule_backuptype and c[
                10] == pre_schedpattern:
                continue

            # 在指定客户端列表内
            if c[0] in selected_clients or not selected_clients:
                # 判断 实例 或 备份集
                type = ""
                if "File System" in c[1] or "Virtual" in c[1] or "Big Data Apps" in c[1]:
                    type = c[3]

                if "Oracle" in c[1] or "SQL Server" in c[1] or "MySQL" in c[1] or "Exchange Database" in c[1]:
                    type = c[2]

                # 数据库没有实例 或者 文件系统没有备份集
                if not type:
                    continue

                    # 处理schedbackupday
                schedbackupday = ""
                schedinterval = ""
                if c[10] == "Weekly":
                    for day in c[12].split(" "):
                        if day:
                            schedbackupday += "/" + \
                                              schedbackupday_chz[day] if day in schedbackupday_chz.keys(
                            ) else day
                    schedbackupday = schedbackupday[1:]

                    # 重复schedinterval
                    if c[11] == "Every 0":
                        schedinterval = "不重复"
                    else:
                        schedinterval = c[11].replace("Every", "每") + "周"

                if c[10] == "One time":
                    schedbackupday = "仅一次"  # 具体时间

                    if c[11] == "Every 0":
                        schedinterval = "不重复"
                    else:
                        schedinterval = c[11].replace("Every", "每") + "次"

                if c[10] == "Daily":
                    schedbackupday = "每天"

                    if c[11] == "Every 0":
                        schedinterval = "不重复"
                    else:
                        schedinterval = c[11].replace("Every", "每") + "天"

                if c[10] in ["Monthly", "Monthly relative"]:
                    schedbackupday = "每月第{0}天".format(c[12])

                    if c[11] == "Every 0":
                        schedinterval = "不重复"
                    else:
                        schedinterval = c[11].replace("Every", "每") + "个月"

                if c[10] in ["Yearly", "Yearly relative"]:
                    year_list = c[12].split(" of ")
                    schedbackupday = "每年{0}{1}日".format(
                        month_chz[year_list[1]] if year_list[1] in month_chz.keys() else year_list[1], year_list[0])

                    if c[11] == "Every 0":
                        schedinterval = "不重复"
                    else:
                        schedinterval = c[11].replace("Every", "每") + "年"

                schedpattern = period_chz[c[10]] if c[10] in period_chz.keys() else c[10]
                schedbackuptype = type_chz[c[9]] if c[9] in type_chz.keys() else c[9]

                if c[0] in client_list:
                    schedule_policy_list.append({
                        "clientname": c[0],
                        "idataagent": c[1],
                        "instance": c[2],
                        "backupset": c[3],
                        "subclient": c[4],
                        "type": type,
                        # 计划策略
                        "scheduleId": c[5],
                        "scheduePolicy": schedule_policy_name if schedule_policy_name else "",
                        "scheduleName": c[7],
                        "scheduletask": c[8],
                        "schedbackuptype": schedbackuptype if schedbackuptype else "",
                        "schedpattern": schedpattern if schedpattern else "",
                        "schedinterval": schedinterval,
                        "schedbackupday": schedbackupday,
                        "schednextbackuptime": c[14].strftime("%Y-%m-%d %H:%M:%S") if c[14] else "",
                    })
                pre_clientname = c[0]
                pre_idataagent = c[1]
                pre_instance = c[2]
                pre_backupset = c[3]
                pre_subclient = c[4]
                pre_schedule_policy = schedule_policy_name
                pre_schedule_backuptype = c[9]
                pre_schedpattern = c[10]
        # 排序
        final_list = []
        for ci in client_list:
            for sp in schedule_policy_list:
                if ci == sp["clientname"]:
                    final_list.append(sp)
        return final_list

    def get_sla(self, selected_clients=[], selected_agents=[]):
        """
        获取备份状态： 备份状态、辅助拷贝状态
            selected_clients 指定客户端列表
            selected_agents 指定应用列表
        """
        status_list = {
            "Running": "运行", "Waiting": "等待", "Pending": "阻塞", "Suspend": "终止", "Completed": "正常",
            "Failed": "失败", "Failed to Start": "启动失败", "Killed": "杀掉",
            "Completed w/ one or more errors": "已完成，但有一个或多个错误",
            "Completed w/ one or more warnings": "已完成，但有一个或多个警告", "Success": "成功","PartialSuccess":"部分完成"
        }

        backup_status_sql = """SELECT clientname, idataagent, instance, backupset, subclient, startdate, jobstatus, jobid
        FROM commserv.dbo.CommCellBackupInfo
        ORDER BY startdate DESC
        """

        schedule_policy_sql = """SELECT clientname,idaagent,instance,backupset,subclient, count(*) count from commserv.dbo.CommCellBkScheduleForSubclients
        group by clientname,instance,idaagent,backupset,subclient
        """

        rpo_sql = """SELECT clientname, idataagent, instance, backupset, subclient, max(startdate) startdate
        FROM commserv.dbo.CommCellBackupInfo where jobstatus in ('Success','Completed') group by clientname, idataagent, instance, backupset, subclient 
                """

        backup_status = self.fetch_all(backup_status_sql)
        duplicated_subclients, client_list = self.get_duplicated_subclients()
        schedule_policy = self.fetch_all(schedule_policy_sql)
        rpo_date=self.fetch_all(rpo_sql)

        backup_status_list = []
        for ds in duplicated_subclients:
            # 在指定客户端列表内
            if ds["clientname"] in selected_clients or not selected_clients:  # selected_clients为空
                # 添加一条空的
                # 判断 实例 或 备份集
                type = ""
                # 备份内容
                if "File System" in ds['idataagent'] or "Virtual" in ds['idataagent'] or "Big Data Apps" in ds[
                    'idataagent']:
                    type = ds['backupset']
                if "Oracle" in ds['idataagent'] or "SQL Server" in ds['idataagent'] or "MySQL" in ds[
                    'idataagent'] or "Exchange Database" in ds['idataagent']:
                    type = ds['instance']

                # 数据库没有实例 或者 文件系统没有备份集
                if not type:
                    continue
                mystatus = {
                    "clientname": ds["clientname"],
                    "idataagent": ds["idataagent"],
                    "instance": ds["instance"],
                    "backupset": ds["backupset"],
                    "subclient": ds["subclient"],
                    "startdate": "无",
                    "bk_status": "无",
                    "type": type,
                    "policy":"未配置",
                    "rpo":"",
                    "rposec": 0,
                    "percent":0
                }

                timenow = datetime.datetime.now() - timedelta(days=30)
                countall = 0
                countsuccess = 0
                percent = 0
                #最近一次是否成功、近30天备份成功率
                for bs in backup_status:
                    isfrist = True
                    if bs[0] == ds["clientname"] and bs[1] == ds["idataagent"] and bs[2] == ds["instance"] and bs[3] == ds[
                        "backupset"] and bs[4] == ds["subclient"]:
                        bk_status = bs[6]
                        try:
                            bk_status = status_list[bk_status]
                        except:
                            pass
                        if isfrist:
                            mystatus["startdate"]= bs[5]
                            mystatus["bk_status"]= bk_status if bk_status else "无"
                            isfrist = False
                        if bs[5]>timenow:
                            if bs[6]!="Running" and bs[6]!="Waiting" and bs[6]!="Pending" and bs[6]!="Suspend":
                                countall = countall+1
                            if bs[6]=="Completed" or bs[6]=="Completed w/ one or more errors" or bs[6]=="Completed w/ one or more warnings" or bs[6]=="Success" or bs[6]=="PartialSuccess":
                                countsuccess=countsuccess+1
                        else:
                            break
                try:
                    percent=round(countsuccess/countall*100,2)
                except:
                    pass
                mystatus["percent"] = percent

                #是否有计划策略
                for sp in schedule_policy:
                    if sp[0] == ds["clientname"] and sp[1] == ds["idataagent"] and sp[2] == ds["instance"] and sp[3] == ds["backupset"] and sp[4] == ds["subclient"]:

                        count = sp[5]
                        if count>0:
                            mystatus["policy"] ="已配置"
                        break
                #rpo
                for rd in rpo_date:
                    if rd[0] == ds["clientname"] and rd[1] == ds["idataagent"] and rd[2] == ds["instance"] and rd[3] == ds["backupset"] and rd[4] == ds["subclient"]:
                        try:
                            totalsec=(datetime.datetime.now()-rd[5]).total_seconds()
                            totalsec = int(totalsec)
                            sec = 0
                            min = 0
                            hour=0
                            day=0
                            min,sec = divmod(totalsec, 60)
                            if min>=60:
                                hour, min = divmod(min, 60)
                                if hour>=24:
                                    day, hour = divmod(hour, 24)
                            strrpo =""
                            if day>0:
                                strrpo += str(day) + "天"
                            if hour>0 and day<=30:
                                strrpo += str(hour) + "小时"
                            if min>0  and day<1:
                                strrpo += str(min) + "分"
                            if sec > 0 and day < 1:
                                strrpo += str(sec) + "秒"

                            mystatus["rpo"] = strrpo
                            mystatus["rposec"] = totalsec
                        except Exception as e:
                            print(e)
                        break
                backup_status_list.append(mystatus)

        # 排序
        final_list = []
        for ci in client_list:
            for bs in backup_status_list:
                if ci == bs["clientname"]:
                    final_list.append(bs)
        return final_list

    def get_clients_name(self):
        clients_sql = """SELECT [ClientId],[Client],[NetworkInterface],[OS [Version]]],[Hardware],[GalaxyRelease],[InstallTime] FROM [commserv].[dbo].[CommCellClientConfig] where ClientStatus='installed'"""
        ret = self.fetch_all(clients_sql)
        clientname_list = []
        for c in ret:
            clientname_list.append({
                "client_id": c[0],
                "client_name": c[1],
            })
        return clientname_list

    def get_cv_joblist(self, startdate, enddate, clientid, jobstatus):
        status_list = {"Running": "运行", "Waiting": "等待", "Pending": "阻塞", "Completed": "正常", "Success": "成功",
                       "PartialSuccess": "部分成功",
                       "Failed": "失败", "Failed to Start": "启动失败",
                       "Completed w/ one or more errors": "已完成，但有一个或多个错误",
                       "Completed w/ one or more warnings": "已完成，但有一个或多个警告"}
        job_sql = ""
        if clientid:
            clientname_sql = """SELECT [Client] FROM [commserv].[dbo].[CommCellClientConfig] WHERE ClientId={CliendId} AND ClientStatus='installed'""".format(CliendId=clientid)
            content = self.fetch_all(clientname_sql)
            clientname = content[0][0]
            if jobstatus != "":
                if jobstatus == "others":
                    jobstatus_list = ('Running', 'Waiting', 'Pending', 'Completed', 'Success', 'PartialSuccess',
                                  'Completed w/ one or more errors', 'Completed w/ one or more warnings', 'Failed', 'Failed to Start')
                    job_sql = """SELECT [jobid],[clientname],[idataagent],[instance],[backupset],[subclient],[data_sp],[backuplevel],[incrlevel],[jobstatus],[jobfailedreason],[startdate],[enddate],[totalBackupSize],[jobfailedreason]
                                FROM [commserv].[dbo].[CommCellBackupInfo] WHERE enddate >= '{startdate}' AND enddate <= '{enddate}' AND clientname = '{clientname}' AND jobstatus not in {jobstatus}
                                ORDER BY [startdate] DESC""".format(startdate=startdate, enddate=enddate, clientname=clientname,jobstatus=jobstatus_list)
                else:
                    if jobstatus == "run":
                        jobstatus_list = ('Running', 'Waiting', 'Pending')
                    elif jobstatus == "success":
                        jobstatus_list = ('Completed', 'Success')
                    elif jobstatus == "warn":
                        jobstatus_list = ('PartialSuccess', 'Completed w/ one or more errors', 'Completed w/ one or more warnings')
                    elif jobstatus == "failed":
                        jobstatus_list = ('Failed', 'Failed to Start')
                    job_sql = """SELECT [jobid],[clientname],[idataagent],[instance],[backupset],[subclient],[data_sp],[backuplevel],[incrlevel],[jobstatus],[jobfailedreason],[startdate],[enddate],[totalBackupSize],[jobfailedreason]
                                FROM [commserv].[dbo].[CommCellBackupInfo] WHERE enddate >= '{startdate}' AND enddate <= '{enddate}' AND clientname = '{clientname}' AND jobstatus in {jobstatus}
                                ORDER BY [startdate] DESC""".format(startdate=startdate, enddate=enddate, clientname=clientname,jobstatus=jobstatus_list)

            elif jobstatus == "":
                job_sql = """SELECT [jobid],[clientname],[idataagent],[instance],[backupset],[subclient],[data_sp],[backuplevel],[incrlevel],[jobstatus],[jobfailedreason],[startdate],[enddate],[totalBackupSize],[jobfailedreason]
                            FROM [commserv].[dbo].[CommCellBackupInfo] WHERE enddate >= '{startdate}' AND enddate <= '{enddate}' AND clientname = '{clientname}'
                            ORDER BY [startdate] DESC""".format(startdate=startdate, enddate=enddate, clientname=clientname)
        elif clientid == "" and jobstatus != "":
            if jobstatus == "others":
                jobstatus_list = ('Running', 'Waiting', 'Pending', 'Completed', 'Success', 'PartialSuccess',
                                  'Completed w/ one or more errors', 'Completed w/ one or more warnings', 'Failed', 'Failed to Start')
                job_sql = """SELECT [jobid],[clientname],[idataagent],[instance],[backupset],[subclient],[data_sp],[backuplevel],[incrlevel],[jobstatus],[jobfailedreason],[startdate],[enddate],[totalBackupSize],[jobfailedreason]
                            FROM [commserv].[dbo].[CommCellBackupInfo] WHERE enddate >= '{startdate}' AND enddate <= '{enddate}' AND jobstatus not in {jobstatus}
                            ORDER BY [startdate] DESC""".format(startdate=startdate, enddate=enddate, jobstatus=jobstatus_list)
            else:
                if jobstatus == "run":
                    jobstatus_list = ('Running', 'Waiting', 'Pending')
                elif jobstatus == "success":
                    jobstatus_list = ('Completed', 'Success')
                elif jobstatus == "warn":
                    jobstatus_list = ('PartialSuccess', 'Completed w/ one or more errors', 'Completed w/ one or more warnings')
                elif jobstatus == "failed":
                    jobstatus_list = ('Failed', 'Failed to Start')
                job_sql = """SELECT [jobid],[clientname],[idataagent],[instance],[backupset],[subclient],[data_sp],[backuplevel],[incrlevel],[jobstatus],[jobfailedreason],[startdate],[enddate],[totalBackupSize],[jobfailedreason]
                            FROM [commserv].[dbo].[CommCellBackupInfo] WHERE enddate >= '{startdate}' AND enddate <= '{enddate}' AND jobstatus in {jobstatus}
                            ORDER BY [startdate] DESC""".format(startdate=startdate, enddate=enddate, jobstatus=jobstatus_list)
        else:
            job_sql = """SELECT [jobid],[clientname],[idataagent],[instance],[backupset],[subclient],[data_sp],[backuplevel],[incrlevel],[jobstatus],[jobfailedreason],[startdate],[enddate],[totalBackupSize],[jobfailedreason]
                        FROM [commserv].[dbo].[CommCellBackupInfo] WHERE enddate >= '{startdate}' AND enddate <= '{enddate}'
                        ORDER BY [startdate] DESC""".format(startdate=startdate, enddate=enddate)

        content = self.fetch_all(job_sql)
        job_list = []
        show_job_status_num = {}
        jobstatus_label = ""
        job_run_num = 0
        job_success_num = 0
        job_warn_num = 0
        job_failed_num = 0
        job_other_num = 0
        for i in content:
            job_status = i[9]
            if job_status in status_list:
                job_status = status_list[job_status]
                if job_status == '运行' or job_status == '等待' or job_status == '阻塞':
                    jobstatus_label = 'label label-sm label-success'
                    job_run_num += 1
                elif job_status == '正常' or job_status == '成功':
                    job_success_num += 1
                    jobstatus_label = 'label label-sm label-success'
                elif job_status == '已完成，但有一个或多个错误' or job_status == '已完成，但有一个或多个警告' or job_status == '部分成功':
                    job_warn_num += 1
                    jobstatus_label = 'label label-sm label-warning'
                elif job_status == '失败' or job_status == '启动失败':
                    jobstatus_label = 'label label-sm label-danger'
                    job_failed_num += 1
            else:
                job_status = job_status
                job_other_num += 1
                jobstatus_label = 'label label-sm label-default'

            job_list.append({
                "jobid": i[0],
                "clientname": i[1],
                "idataagent": i[2],
                "instance": i[3],
                "backupset": i[4],
                "subclient": i[5],
                "data_sp": i[6],
                "backuplevel": i[7],
                "incrlevel": i[8],
                "jobstatus": job_status,
                "jobstatus_label": jobstatus_label,
                "jobfailedreason": i[10],
                "startdate": i[11].strftime('%Y-%m-%d %H:%M:%S') if i[11] else "",
                "enddate": i[12].strftime('%Y-%m-%d %H:%M:%S') if i[12] else "",
                "totalBackupSize": i[13],
                "jobfailedreason": i[14],
            })

        show_job_status_num['job_run_num'] = job_run_num
        show_job_status_num['job_success_num'] = job_success_num
        show_job_status_num['job_warn_num'] = job_warn_num
        show_job_status_num['job_failed_num'] = job_failed_num

        return job_list, show_job_status_num

    def get_cv_joblist_daily(self):
        job_sql = """select CONVERT(BIGINT,DATEDIFF(MI,'1970-01-01 00:00:00.000', CONVERT(varchar(10),startdate,120))) * 60000 startdate,round(sum(totalbackupsize)/1024.00/1024/1024,2) from [commserv].[dbo].[CommCellBackupInfo]  where startdate>dateadd(year,-1,getdate())
                    group by CONVERT(varchar(10),startdate,120) order by startdate"""

        content = self.fetch_all(job_sql)
        job_list = []
        for i in content:
            job_list.append([i[0],float(i[1])])

        return job_list

    def get_cv_jobbytype(self, startdate, enddate, clientid, jobstatus):
        job_sql = ""
        if clientid:
            clientname_sql = """SELECT [Client] FROM [commserv].[dbo].[CommCellClientConfig] WHERE ClientId={CliendId} AND ClientStatus='installed'""".format(CliendId=clientid)
            content = self.fetch_all(clientname_sql)
            clientname = content[0][0]
            if jobstatus != "":
                if jobstatus == "others":
                    jobstatus_list = ('Running', 'Waiting', 'Pending', 'Completed', 'Success', 'PartialSuccess',
                                  'Completed w/ one or more errors', 'Completed w/ one or more warnings', 'Failed', 'Failed to Start')
                    job_sql = """SELECT [idataagent],round(sum(totalBackupSize)/1024.00/1024/1024,2),count(*)
                                FROM [commserv].[dbo].[CommCellBackupInfo] WHERE enddate >= '{startdate}' AND enddate <= '{enddate}' AND clientname = '{clientname}' AND jobstatus not in {jobstatus} group by [idataagent]
                                ORDER BY [idataagent] DESC""".format(startdate=startdate, enddate=enddate, clientname=clientname,jobstatus=jobstatus_list)
                else:
                    if jobstatus == "run":
                        jobstatus_list = ('Running', 'Waiting', 'Pending')
                    elif jobstatus == "success":
                        jobstatus_list = ('Completed', 'Success')
                    elif jobstatus == "warn":
                        jobstatus_list = ('PartialSuccess', 'Completed w/ one or more errors', 'Completed w/ one or more warnings')
                    elif jobstatus == "failed":
                        jobstatus_list = ('Failed', 'Failed to Start')
                    job_sql = """SELECT [idataagent],round(sum(totalBackupSize)/1024.00/1024/1024,2),count(*)
                                FROM [commserv].[dbo].[CommCellBackupInfo] WHERE enddate >= '{startdate}' AND enddate <= '{enddate}' AND clientname = '{clientname}' AND jobstatus in {jobstatus} group by [idataagent]
                                ORDER BY [idataagent] DESC""".format(startdate=startdate, enddate=enddate, clientname=clientname,jobstatus=jobstatus_list)

            elif jobstatus == "":
                job_sql = """SELECT [idataagent],round(sum(totalBackupSize)/1024.00/1024/1024,2),count(*)
                            FROM [commserv].[dbo].[CommCellBackupInfo] WHERE enddate >= '{startdate}' AND enddate <= '{enddate}' AND clientname = '{clientname}' group by [idataagent]
                            ORDER BY [idataagent] DESC""".format(startdate=startdate, enddate=enddate, clientname=clientname)
        elif clientid == "" and jobstatus != "":
            if jobstatus == "others":
                jobstatus_list = ('Running', 'Waiting', 'Pending', 'Completed', 'Success', 'PartialSuccess',
                                  'Completed w/ one or more errors', 'Completed w/ one or more warnings', 'Failed', 'Failed to Start')
                job_sql = """SELECT [idataagent],round(sum(totalBackupSize)/1024.00/1024/1024,2),count(*)
                            FROM [commserv].[dbo].[CommCellBackupInfo] WHERE enddate >= '{startdate}' AND enddate <= '{enddate}' AND jobstatus not in {jobstatus} group by [idataagent]
                            ORDER BY [idataagent] DESC""".format(startdate=startdate, enddate=enddate, jobstatus=jobstatus_list)
            else:
                if jobstatus == "run":
                    jobstatus_list = ('Running', 'Waiting', 'Pending')
                elif jobstatus == "success":
                    jobstatus_list = ('Completed', 'Success')
                elif jobstatus == "warn":
                    jobstatus_list = ('PartialSuccess', 'Completed w/ one or more errors', 'Completed w/ one or more warnings')
                elif jobstatus == "failed":
                    jobstatus_list = ('Failed', 'Failed to Start')
                job_sql = """SELECT [idataagent],round(sum(totalBackupSize)/1024.00/1024/1024,2),count(*)
                            FROM [commserv].[dbo].[CommCellBackupInfo] WHERE enddate >= '{startdate}' AND enddate <= '{enddate}' AND jobstatus in {jobstatus}  group by [idataagent]
                            ORDER BY [idataagent] DESC""".format(startdate=startdate, enddate=enddate, jobstatus=jobstatus_list)
        else:
            job_sql = """SELECT [idataagent],round(sum(totalBackupSize)/1024.00/1024/1024,2),count(*)
                        FROM [commserv].[dbo].[CommCellBackupInfo] WHERE enddate >= '{startdate}' AND enddate <= '{enddate}'  group by [idataagent]
                        ORDER BY [idataagent] DESC""".format(startdate=startdate, enddate=enddate)

        content = self.fetch_all(job_sql)
        idataagent_list=[]
        totalBackupSize_list = []
        totalBackupTimes_list = []
        for i in content:
            idataagent_list.append(i[0])
            totalBackupSize_list.append(float(i[1]))
            totalBackupTimes_list.append(i[2])

        return {"idataagent_list":idataagent_list,"totalBackupSize_list":totalBackupSize_list,"totalBackupTimes_list":totalBackupTimes_list}

    def display_error_job_list(self, startdate, enddate, clientid):
        status_list = {"Running": "运行", "Waiting": "等待", "Pending": "阻塞", "Completed": "正常", "Success": "成功",
                       "PartialSuccess": "部分成功",
                       "Failed": "失败", "Failed to Start": "启动失败",
                       "Completed w/ one or more errors": "已完成，但有一个或多个错误",
                       "Completed w/ one or more warnings": "已完成，但有一个或多个警告"}
        jobstatus_label = ""
        #告警信息
        if clientid:
            clientname_sql = """SELECT [Client] FROM [commserv].[dbo].[CommCellClientConfig] WHERE ClientId={CliendId} AND ClientStatus='installed'""".format(CliendId=clientid)
            content = self.fetch_all(clientname_sql)
            clientname = content[0][0]
            job_sql = """SELECT [jobid],[clientname],[idataagent],[instance],[backupset],[subclient],[data_sp],[backuplevel],[incrlevel],[jobstatus],[jobfailedreason],[startdate],[enddate],[totalBackupSize]
                        FROM [commserv].[dbo].[CommCellBackupInfo] WHERE jobfailedreason <>'' AND enddate >= '{startdate}' AND enddate <= '{enddate}' AND  clientname = '{clientname}'
                    ORDER BY [startdate] DESC""".format(startdate=startdate, enddate=enddate, clientname=clientname)
        else:
            job_sql = """SELECT [jobid],[clientname],[idataagent],[instance],[backupset],[subclient],[data_sp],[backuplevel],[incrlevel],[jobstatus],[jobfailedreason],[startdate],[enddate],[totalBackupSize]
                        FROM [commserv].[dbo].[CommCellBackupInfo] WHERE jobfailedreason <>'' AND enddate >= '{startdate}' AND enddate <= '{enddate}'
                    ORDER BY [startdate] DESC""".format(startdate=startdate, enddate=enddate)

        content = self.fetch_all(job_sql)
        error_job_list = []
        for i in content:
            job_status = i[9]
            if job_status in status_list:
                job_status = status_list[job_status]
                if job_status == '已完成，但有一个或多个错误' or job_status == '已完成，但有一个或多个警告' or job_status == '部分成功':
                    jobstatus_label = 'label label-sm label-warning'
                elif job_status == '失败' or job_status == '启动失败':
                    jobstatus_label = 'label label-sm label-danger'
            else:
                job_status = job_status
                jobstatus_label = 'label label-sm label-default'

            error_job_list.append({
                "jobid": i[0],
                "clientname": i[1],
                "idataagent": i[2],
                "instance": i[3],
                "backupset": i[4],
                "subclient": i[5],
                "data_sp": i[6],
                "backuplevel": i[7],
                "incrlevel": i[8],
                "jobstatus": job_status,
                "jobstatus_label": jobstatus_label,
                "jobfailedreason": i[10],
                "startdate": i[11].strftime('%Y-%m-%d %H:%M:%S') if i[11] else "",
                "enddate": i[12].strftime('%Y-%m-%d %H:%M:%S') if i[12] else "",
                "totalBackupSize": i[13],
            })
        return error_job_list

    def get_duplicated_subclients(self):
        client_list = [client["client_name"] for client in self.get_clients_info()]
        subclient_sql = """SELECT [clientname],[idataagent],[instance],[backupset],[subclient]
        FROM [commserv].[dbo].[CommCellSubClientConfig] 
        WHERE [backupset]!='Indexing BackupSet' AND [subclient]!='(command line)' {0}
        ORDER BY [clientname] DESC, [idataagent] DESC, [instance] DESC, [backupset] DESC, [subclient] DESC""".format(
            "AND [clientname] IN ({0})".format(str(client_list)[1:-1]) if client_list else ""
        )

        ret = self.fetch_all(subclient_sql)
        pre_clientname = ""
        pre_idataagent = ""
        pre_instance = ""
        pre_backupset = ""
        pre_subclient = ""

        duplicated_subclient_list = []
        # 客户端 应用类型
        for c in ret:
            # 去重
            if c[0] == pre_clientname and c[1] == pre_idataagent and c[2] == pre_instance and c[3] == pre_backupset and \
                    c[4] == pre_subclient:
                continue
            duplicated_subclient_list.append({
                "clientname": c[0],
                "idataagent": c[1],
                "instance": c[2],
                "backupset": c[3],
                "subclient": c[4],
            })
            pre_clientname = c[0]
            pre_idataagent = c[1]
            pre_instance = c[2]
            pre_backupset = c[3]
            pre_subclient = c[4]

        return duplicated_subclient_list, client_list

    def get_duplicated_aux_copy(self):
        auxcopy_sql = """SELECT DISTINCT [jobId], [auxCopyJobId], [status], [copiedTime]
        FROM [commserv].[dbo].[JMJobDataStats]
        WHERE [auxCopyJobId]<>0
        ORDER BY [copiedTime] DESC"""
        aux_copy_list = []
        aux_copy = self.fetch_all(auxcopy_sql)
        pre_ac = ""
        for ac in aux_copy:
            if pre_ac != ac[0]:
                aux_copy_list.append({
                    "jobId": ac[0],
                    "auxCopyJobId": ac[1],
                    "status": "成功" if ac[2] == 100 else "失败",
                    "copiedTime": ac[3],
                })
            pre_ac = ac[0]
        return aux_copy_list


if __name__ == '__main__':
    credit = {
        "SQLServerHost": "192.168.100.222\COMMVAULT",
        "SQLServerUser": "sa_cloud",
        "SQLServerPasswd": "1qaz@WSX",
        "SQLServerDataBase": "CommServ",
    }
    dm = CVApi(credit)
    dm.get_backup_status()

