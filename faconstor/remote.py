"""
paramiko, pywinrm实现windows/linux脚本调用
linux下脚本语法错误,或者命令不存在等没有通过stderr变量接收到，只能添加判断条件；
windows下可以接收到错误信息并作出判断；
"""
import paramiko
import winrm
import socket
import requests
import datetime
from winrm.exceptions import WinRMTransportError, WinRMOperationTimeoutError
from requests.exceptions import ConnectionError


###############################################################
# 为实现 WINDOWS下执行脚本时长超时设置，对wimrm中相关类进行重写。#
###############################################################
# 重写Protocol类
class Protocol(winrm.protocol.Protocol):
    def get_command_output(self, shell_id, command_id):
        """
        Get the Output of the given shell and command
        @param string shell_id: The shell id on the remote machine.
         See #open_shell
        @param string command_id: The command id on the remote machine.
         See #run_command
        #@return [Hash] Returns a Hash with a key :exitcode and :data.
         Data is an Array of Hashes where the cooresponding key
        #   is either :stdout or :stderr.  The reason it is in an Array so so
         we can get the output in the order it ocurrs on
        #   the console.
        """
        stdout_buffer, stderr_buffer = [], []
        command_done = False

        ############################################################################
        # 限时6*60s                                                                #
        #   程序反复查看相应，如果相应成功，且在超时时限内则命令成功，否则报超时异常。 #
        #   获取响应的时长较长。                                                    #
        ############################################################################
        return_code = -1
        limited_seconds = 6 * 60
        start_time = datetime.datetime.now()
        while not command_done:
            print('get the response from windows...')
            try:
                stdout, stderr, return_code, command_done = \
                    self._raw_get_command_output(shell_id, command_id)
                stdout_buffer.append(stdout)
                stderr_buffer.append(stderr)
            except WinRMOperationTimeoutError as e:
                # this is an expected error when waiting for a long-running process, just silently retry
                pass

            end_time = datetime.datetime.now()
            delta_time = end_time - start_time
            total_seconds = delta_time.total_seconds()
            if total_seconds > limited_seconds:
                raise WinRMOperationTimeoutError()
        return b''.join(stdout_buffer), b''.join(stderr_buffer), return_code


# 重写Session类
class Session(winrm.Session):
    # TODO implement context manager methods
    def __init__(self, target, auth, **kwargs):
        username, password = auth
        self.url = self._build_url(target, kwargs.get('transport', 'plaintext'))
        self.protocol = Protocol(self.url,
                                 username=username, password=password, **kwargs)


class ServerByPara(object):
    def __init__(self, cmd, host, user, password, system_choice):
        self.cmd = cmd
        self.client = paramiko.SSHClient()
        self.host = host
        self.user = user
        self.pwd = password
        self.system_choice = system_choice

    def exec_linux_cmd(self, succeedtext):
        data_init = ''
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(hostname=self.host, username=self.user, password=self.pwd, timeout=5)
        except TimeoutError as e:
            print("连接服务器失败")
            return {
                "exec_tag": 1,
                "data": "连接服务器失败 {0}".format(e),
                "log": "连接服务器失败",
            }
        try:
            stdin, stdout, stderr = self.client.exec_command(self.cmd, get_pty=True, timeout=6 * 60)
            if stderr.readlines():
                exec_tag = 1
                for data in stderr.readlines():
                    data_init += data
                log = ""
            else:
                exec_tag = 0
                log = ""

                try:
                    for data in stdout.readlines():
                        data_init += data

                    if "command not found" in data_init:  # 命令不存在
                        exec_tag = 1
                        log = "命令不存在"
                    elif "syntax error" in data_init:  # 语法错误
                        exec_tag = 1
                        log = "语法错误"
                    elif "No such file or directory" in data_init:  # 脚本不存在
                        exec_tag = 1
                        log = "脚本不存在"
                    elif succeedtext is not None:
                        if succeedtext not in data_init:
                            exec_tag = 1
                            log = "未匹配"
                except:
                    exec_tag = 0  # 不抛错
                    log = "编码错误"
                    data_init = "编码错误"
        except socket.timeout as e:
            print("脚本执行超时")
            return {
                "exec_tag": 1,
                "data": "脚本执行超时",
                "log": "脚本执行超时",
            }

        return {
            "exec_tag": exec_tag,
            "data": data_init,
            "log": log,
        }

    def exec_win_cmd(self, succeedtext):
        data_init = ""
        log = ""

        try:
            s = Session(self.host, auth=(self.user, self.pwd))
            ret = s.run_cmd(self.cmd)
        except (ConnectionError, WinRMOperationTimeoutError, WinRMTransportError) as e:
            if type(e) == WinRMOperationTimeoutError:
                print("脚本执行超时")
                exec_tag = 1
                data = "脚本执行超时 {0}".format(e)
                log = "脚本执行超时"
            elif type(e) in [ConnectionError, WinRMTransportError]:
                print("连接windows失败")
                exec_tag = 1
                data = "连接windows失败 {0}".format(e)
                log = "连接windows失败"
            else:
                print("执行windows脚本发生异常错误")
                exec_tag = 1
                data = "执行windows脚本发生异常错误 {0}".format(e)
                log = "执行windows脚本发生异常错误"

            return {
                "exec_tag": exec_tag,
                "data": data,
                "log": log,
            }
        else:
            if ret.std_err.decode():
                exec_tag = 1
                for data in ret.std_err.decode().split("\r\n"):
                    data_init += data
                log = ""
            else:
                exec_tag = 0
                for data in ret.std_out.decode().split("\r\n"):
                    data_init += data
                if succeedtext is not None:
                    if succeedtext not in data_init:
                        exec_tag = 1
                        log = "未匹配"

            return {
                "exec_tag": exec_tag,
                "data": data_init,
                "log": log,
            }

    def run(self, succeedtext):
        if self.system_choice == "Linux":
            result = self.exec_linux_cmd(succeedtext)
        else:
            result = self.exec_win_cmd(succeedtext)
        print(result)
        return result

# if __name__ == '__main__':
# server_obj = ServerByPara(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
#     server_obj = ServerByPara(r"C:\Users\Administrator\Desktop\test_python.bat", "192.168.100.151", "administrator","tesunet@2017", "Windows")
# server_obj = ServerByPara(r"/root/Desktop/test06.sh hello", "47.95.195.90", "root","!zxcvbn123", "Linux")
#     server_obj = ServerByPara(r"cat /root/Desktop/script_log.txt", "47.95.195.90", "root","!zxcvbn123", "Linux")
#
# server_obj.run("")
