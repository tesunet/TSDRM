# -*- coding: utf-8 -*-

import atexit
from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim
import ssl
import sys
import time
import textwrap
import re
import requests


requests.packages.urllib3.disable_warnings()
ssl._create_default_https_context = ssl._create_unverified_context


class VM_API(object):
    def __init__(self, vchost, user, password, port=443):
        self.msg = ""
        self.vchost = vchost
        self.user = user
        self.password = password
        self.port = port
        self.service_instance = connect.SmartConnect(host=self.vchost,
                                                     user=self.user,
                                                     pwd=self.password,
                                                     port=int(self.port))
        atexit.register(connect.Disconnect, self.service_instance)
        self.content = self.service_instance.RetrieveContent()
        self._spinner = self._create_char_spinner()

    def getdatacenterlist(self, curdcname=None):
        datacenterlist = []
        content = self.content
        children = content.rootFolder.childEntity
        for child in children:  # Iterate though DataCenters
            if curdcname is None or curdcname == dc.name:
                dc = child
                dcname = dc.name
                datacenterlist.append({"dcname": dcname})
        return datacenterlist

    def getclusterlist(self, curdcname=None, curcluster=None):
        clusterlist = []
        content = self.content
        datacenters = content.rootFolder.childEntity
        for dc in datacenters:  # Iterate though DataCenters
            if curdcname is None or curdcname == dc.name:
                dcname = dc.name
                clusters = dc.hostFolder.childEntity
                for cluster in clusters:  # Iterate through the clusters in the DC
                    if curcluster is None or curcluster == cluster.name:
                        clustername = cluster.name
                        clusterlist.append({"dcname": dcname, "clustername": clustername})
        return clusterlist

    def gethostlist(self, curdcname=None, curcluster=None, curhostname=None):
        hostlist = []
        content = self.content
        datacenters = content.rootFolder.childEntity
        for dc in datacenters:  # Iterate though DataCenters
            if curdcname is None or curdcname == dc.name:
                dcname = dc.name
                clusters = dc.hostFolder.childEntity
                for cluster in clusters:  # Iterate through the clusters in the DC
                    if curcluster is None or curcluster == cluster.name:
                        clustername = cluster.name
                        try:
                            hosts = cluster.host  # Variable to make pep8 compliance
                            for host in hosts:  # Iterate through Hosts in the Cluster
                                if curhostname is None or curhostname == host.summary.config.name:
                                    hostname = host.summary.config.name
                                    hostlist.append(
                                        {"dcname": dcname, "clustername": clustername, "hostname": hostname})
                        except:
                            pass
        return hostlist

    def getvmlist(self, curdcname=None, curcluster=None, curhostname=None, curvmname=None):
        vmlist = []
        content = self.content
        datacenters = content.rootFolder.childEntity
        for dc in datacenters:  # Iterate though DataCenters
            if curdcname is None or curdcname == dc.name:
                dcname = dc.name
                clusters = dc.hostFolder.childEntity
                for cluster in clusters:  # Iterate through the clusters in the DC
                    if curcluster is None or curcluster == cluster.name:
                        clustername = cluster.name
                        try:
                            hosts = cluster.host  # Variable to make pep8 compliance
                            for host in hosts:  # Iterate through Hosts in the Cluster
                                if curhostname is None or curhostname == host.summary.config.name:
                                    hostname = host.summary.config.name
                                    vms = host.vm
                                    for vm in vms:  # Iterate through each VM on the host
                                        if curvmname is None or curvmname == vm.summary.config.name:
                                            myvm = {}
                                            myvm["dcname"] = dcname
                                            myvm["clustername"] = clustername
                                            myvm["hostname"] = hostname
                                            myvm["vmname"] = vm.summary.config.name
                                            myvm["guest"] = vm.summary.config.guestFullName
                                            myvm["uuid"] = vm.summary.config.uuid
                                            myvm["state"] = vm.summary.runtime.powerState
                                            if vm.summary.guest is not None:
                                                myvm["ip"] = vm.summary.guest.ipAddress
                                            myvm["memory"] = vm.summary.config.memorySizeMB
                                            myvm["cpu"] = vm.summary.config.numCpu
                                            capacity = 0
                                            try:
                                                for dev in vm.config.hardware.device:
                                                    if hasattr(dev.backing, 'fileName'):
                                                        try:
                                                            capacity += dev.capacityInKB
                                                        except:
                                                            pass
                                            except:
                                                pass
                                            myvm["capacity"] = capacity / 1024 / 1024
                                            mytask = []
                                            for task in vm.recentTask:
                                                state = None
                                                try:
                                                    state = task.info.state
                                                except:
                                                    pass
                                                startTime = None
                                                try:
                                                    startTime = task.info.startTime
                                                except:
                                                    pass
                                                completeTime = None
                                                try:
                                                    completeTime = task.info.completeTime
                                                except:
                                                    pass
                                                progress = None
                                                try:
                                                    progress = task.info.progress
                                                except:
                                                    pass
                                                descriptionId = None
                                                try:
                                                    descriptionId = task.info.descriptionId
                                                except:
                                                    pass
                                                key = None
                                                try:
                                                    key = task.info.key
                                                except:
                                                    pass
                                                mytask.append({"state": state, "startTime": startTime,
                                                               "completeTime": completeTime, "progress": progress,
                                                               "descriptionId": descriptionId, "key": key})
                                            myvm["task"] = mytask
                                            vmlist.append(myvm)
                        except:
                            pass
        return vmlist

    def get_obj(self, vimtype, name=None):
        """
        Return an object by name, if name is None the
        first found object is returned
        """
        content = self.content
        obj = None
        container = content.viewManager.CreateContainerView(
            content.rootFolder, vimtype, True)
        for c in container.view:
            if name:
                if c.name == name:
                    obj = c
                    break
            else:
                obj = c
                break

        return obj

    def clone_vm(self, template, vm_name, datacenter_name, cluster_name, power_on=True, datastore_name=None):
        """
        Clone a VM from a template/VM, datacenter_name, vm_folder, datastore_name
        cluster_name, resource_pool, and power_on are all optional.
        """

        # if none git the first one
        content = self.content
        template = self.get_obj([vim.VirtualMachine], template)

        datacenter = self.get_obj([vim.Datacenter], datacenter_name)
        destfolder = datacenter.vmFolder
        if datastore_name:
            datastore = self.get_obj([vim.Datastore], datastore_name)
        else:
            datastore = self.get_obj([vim.Datastore], template.datastore[0].info.name)

        # if None, get the first one
        cluster = None
        clusters = datacenter.hostFolder.childEntity
        for mycluster in clusters:  # Iterate through the clusters in the DC
            if cluster_name:
                if cluster_name == mycluster.name:
                    cluster = mycluster
                    break
            else:
                cluster = mycluster
                break
        resource_pool = cluster.resourcePool

        # set relospec
        relospec = vim.vm.RelocateSpec()
        relospec.datastore = datastore
        relospec.pool = resource_pool

        clonespec = vim.vm.CloneSpec()
        clonespec.location = relospec
        clonespec.powerOn = power_on
        task = template.Clone(folder=destfolder, name=vm_name, spec=clonespec)
        return task

    def wait_for_disk(self,vm,disknum):
        """ wait for a vCenter task to finish """
        task_done = False
        i=0
        while not task_done:
            time.sleep(1)
            vm_config_str = vm.layout.__str__()
            com = re.compile('vim.vm.FileLayout.DiskLayout')
            newdisknum = int(len(com.findall(vm_config_str))) - 2
            if newdisknum>disknum:
                return newdisknum
            if i>60:
                return -9

    def add_disk(self, vmname, disk_type, disk_size, uuid=None):
        # connect this thing

        vm = None
        if uuid:
            search_index = self.service_instance.content.searchIndex
            vm = search_index.FindByUuid(None, uuid, True)
        elif vmname:
            vm = self.get_obj(self.content, [vim.VirtualMachine], vmname)

        if vm:
            spec = vim.vm.ConfigSpec()
            # get all disks on a VM, set unit_number to the next available
            unit_number = 0
            for dev in vm.config.hardware.device:
                if hasattr(dev.backing, 'fileName'):
                    unit_number = int(dev.unitNumber) + 1
                    # unit_number 7 reserved for scsi controller
                    if unit_number == 7:
                        unit_number += 1
                    if unit_number >= 16:
                        print("we don't support this many disks")
                        return
                if isinstance(dev, vim.vm.device.VirtualSCSIController):
                    controller = dev
            # add disk here
            dev_changes = []
            new_disk_kb = int(disk_size) * 1024 * 1024
            disk_spec = vim.vm.device.VirtualDeviceSpec()
            disk_spec.fileOperation = "create"
            disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            disk_spec.device = vim.vm.device.VirtualDisk()
            disk_spec.device.backing = \
                vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
            if disk_type == 'thin':
                disk_spec.device.backing.thinProvisioned = True
            disk_spec.device.backing.diskMode = 'persistent'
            disk_spec.device.unitNumber = unit_number
            disk_spec.device.capacityInKB = new_disk_kb
            disk_spec.device.controllerKey = controller.key
            dev_changes.append(disk_spec)
            spec.deviceChange = dev_changes
            vm.ReconfigVM_Task(spec=spec)

            vm_config_str = vm.layout.__str__()
            com = re.compile('vim.vm.FileLayout.DiskLayout')
            disknum = int(len(com.findall(vm_config_str))) - 2

            return self.wait_for_disk(vm,disknum)


    def execute_program(self, vm_uuid, vm_username, vm_password, path, arguments):
        """
        Simple command-line program for executing a process in the VM without the
        network requirement to actually access it.
        """
        try:
            content = self.content
            vm = content.searchIndex.FindByUuid(None, vm_uuid, True)
            tools_status = vm.guest.toolsStatus
            if (tools_status == 'toolsNotInstalled' or
                    tools_status == 'toolsNotRunning'):
                self.msg = "VMwareTools is either not running or not installed. Rerun the script after verifying that VMwareTools is running"
                return False
            creds = vim.vm.guest.NamePasswordAuthentication(
                username=vm_username, password=vm_password
            )

            try:
                pm = content.guestOperationsManager.processManager

                ps = vim.vm.guest.ProcessManager.ProgramSpec(programPath=path, arguments=arguments)
                res = pm.StartProgramInGuest(vm, creds, ps)

                if res > 0:
                    self.msg = "Program executed, PID is %d" % res
                    return res
                else:
                    self.msg = "unknown"
                    return False

            except IOError as e:
                self.msg = str(e)
        except vmodl.MethodFault as error:
            self.msg = "Caught vmodl fault : " + error.msg
            return False
        self.msg = "unknown"
        return False

    def wait_for_tasks(self, tasks):
        """Given the service instance si and tasks, it returns after all the
       tasks are complete
       """
        property_collector = self.service_instance.content.propertyCollector
        task_list = [str(task) for task in tasks]
        # Create filter
        obj_specs = [vmodl.query.PropertyCollector.ObjectSpec(obj=task)
                     for task in tasks]
        property_spec = vmodl.query.PropertyCollector.PropertySpec(type=vim.Task,
                                                                   pathSet=[],
                                                                   all=True)
        filter_spec = vmodl.query.PropertyCollector.FilterSpec()
        filter_spec.objectSet = obj_specs
        filter_spec.propSet = [property_spec]
        pcfilter = property_collector.CreateFilter(filter_spec, True)
        try:
            version, state = None, None
            # Loop looking for updates till the state moves to a completed state.
            while len(task_list):
                update = property_collector.WaitForUpdates(version)
                for filter_set in update.filterSet:
                    for obj_set in filter_set.objectSet:
                        task = obj_set.obj
                        for change in obj_set.changeSet:
                            if change.name == 'info':
                                state = change.val.state
                            elif change.name == 'info.state':
                                state = change.val
                            else:
                                continue

                            if not str(task) in task_list:
                                continue

                            if state == vim.TaskInfo.State.success:
                                # Remove task from taskList
                                task_list.remove(str(task))
                            elif state == vim.TaskInfo.State.error:
                                raise task.info.error
                # Move to next version
                version = update.version
        finally:
            if pcfilter:
                pcfilter.Destroy()

    def reboot_vm(self, uuid, name, ip):
        if not self.service_instance:
            raise SystemExit("Unable to connect to host with supplied info.")
        VM = None
        if uuid:
            VM = self.service_instance.content.searchIndex.FindByUuid(None, uuid,
                                                                      True,
                                                                      True)
        elif name:
            VM = self.service_instance.content.searchIndex.FindByDnsName(None, name,
                                                                         True)
        elif ip:
            VM = self.service_instance.content.searchIndex.FindByIp(None, ip, True)

        if VM is None:
            raise SystemExit("Unable to locate VirtualMachine.")

        print("Found: {0}".format(VM.name))
        print("The current powerState is: {0}".format(VM.runtime.powerState))
        TASK = VM.ResetVM_Task()
        self.wait_for_tasks([TASK])
        print("its done.")
        return VM.name, VM.runtime.powerState

    def _create_char_spinner(self):
        """Creates a generator yielding a char based spinner.
        """
        while True:
            for c in '|/-\\':
                yield c

    def spinner(self, label=''):
        """Prints label with a spinner.

        When called repeatedly from inside a loop this prints
        a one line CLI spinner.
        """
        sys.stdout.write("\r\t%s %s" % (label, self._spinner.__next__()))
        sys.stdout.flush()

    def answer_vm_question(self, virtual_machine):
        print("\n")
        choices = virtual_machine.runtime.question.choice.choiceInfo
        default_option = None
        if virtual_machine.runtime.question.choice.defaultIndex is not None:
            ii = virtual_machine.runtime.question.choice.defaultIndex
            default_option = choices[ii]
        choice = None
        while choice not in [o.key for o in choices]:
            print("VM power on is paused by this question:\n\n")
            print("\n".join(textwrap.wrap(
                virtual_machine.runtime.question.text, 60)))
            for option in choices:
                print("\t %s: %s " % (option.key, option.label))
            if default_option is not None:
                print("default (%s): %s\n" % (default_option.label, default_option.key))
            choice = input("\nchoice number: ").strip()
            print("...")
        return choice

    def power_off_vm(self, name):
        vm = None
        entity_stack = self.content.rootFolder.childEntity
        while entity_stack:
            entity = entity_stack.pop()

            if entity.name == name:
                vm = entity
                del entity_stack[0:len(entity_stack)]
            elif hasattr(entity, 'childEntity'):
                entity_stack.extend(entity.childEntity)
            elif isinstance(entity, vim.Datacenter):
                entity_stack.append(entity.vmFolder)

        if not isinstance(vm, vim.VirtualMachine):
            print("could not find a virtual machine with the name %s" % name)
            sys.exit(-1)

        print("Found VirtualMachine: %s Name: %s" % (vm, vm.name))

        if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
            # using time.sleep we just wait until the power off action
            # is complete. Nothing fancy here.
            print("powering off...")
            task = vm.PowerOff()
            while task.info.state not in [vim.TaskInfo.State.success,
                                          vim.TaskInfo.State.error]:
                time.sleep(1)
            print("power is off.")
        # print(sys.exit(0))

    def power_on_vm(self, name):
        vm = None
        entity_stack = self.content.rootFolder.childEntity
        while entity_stack:
            entity = entity_stack.pop()

            if entity.name == name:
                vm = entity
                del entity_stack[0:len(entity_stack)]
            elif hasattr(entity, 'childEntity'):
                entity_stack.extend(entity.childEntity)
            elif isinstance(entity, vim.Datacenter):
                entity_stack.append(entity.vmFolder)

        if not isinstance(vm, vim.VirtualMachine):
            print("could not find a virtual machine with the name %s" % name)
            sys.exit(-1)

        print("Found VirtualMachine: %s Name: %s" % (vm, vm.name))

        # Sometimes we don't want a task to block execution completely
        # we may want to execute or handle concurrent events. In that case we can
        # poll our task repeatedly and also check for any run-time issues. This
        # code deals with a common problem, what to do if a VM question pops up
        # and how do you handle it in the API?
        print("powering on VM %s" % vm.name)
        if vm.runtime.powerState != vim.VirtualMachinePowerState.poweredOn:
            # now we get to work... calling the vSphere API generates a task...
            task = vm.PowerOn()

            # We track the question ID & answer so we don't end up answering the same
            # questions repeatedly.
            answers = {}
            while task.info.state not in [vim.TaskInfo.State.success,
                                          vim.TaskInfo.State.error]:

                # we'll check for a question, if we find one, handle it,
                # Note: question is an optional attribute and this is how pyVmomi
                # handles optional attributes. They are marked as None.
                if vm.runtime.question is not None:
                    question_id = vm.runtime.question.id
                    if question_id not in answers.keys():
                        answers[question_id] = self.answer_vm_question(vm)
                        vm.AnswerVM(question_id, answers[question_id])

                # create a spinning cursor so people don't kill the script...
                self.spinner(task.info.state)

            if task.info.state == vim.TaskInfo.State.error:
                # some vSphere errors only come with their class and no other message
                print("error type: %s" % task.info.error.__class__.__name__)
                print("found cause: %s" % task.info.error.faultCause)
                for fault_msg in task.info.error.faultMessage:
                    print(fault_msg.key)
                    print(fault_msg.message)
                sys.exit(-1)

        # print(sys.exit(0))

    def destroy_vm(self, uuid, name, ip):
        if not self.service_instance:
            raise SystemExit("Unable to connect to host with supplied info.")
        VM = None
        if uuid:
            VM = self.service_instance.content.searchIndex.FindByUuid(None, uuid,
                                                   True,
                                                   False)
        elif name:
            VM = self.service_instance.content.searchIndex.FindByDnsName(None, name,
                                                      True)
        elif ip:
            VM = self.service_instance.content.searchIndex.FindByIp(None, ip, True)

        if VM is None:
            raise SystemExit("Unable to locate VirtualMachine.")

        print("Found: {0}".format(VM.name))
        print("The current powerState is: {0}".format(VM.runtime.powerState))
        if format(VM.runtime.powerState) == "poweredOn":
            print("Attempting to power off {0}".format(VM.name))
            TASK = VM.PowerOffVM_Task()
            self.wait_for_tasks([TASK])
            print("{0}".format(TASK.info.state))

        print("Destroying VM from vSphere.")
        TASK = VM.Destroy_Task()
        self.wait_for_tasks([TASK])
        print("Done.")


# Start program
if __name__ == "__main__":
    newvm = VM_API('192.168.100.136', 'administrator', 'tesunet@2016')
    # newvm.destroy_vm("422383b8-27d8-39a3-f9de-1654bc2fd599", None, None)
    # print(newvm.execute_program("4223eb50-03bf-865c-3c99-5e0a5966d8c4", "root", "tesunet", "/root/host.sh", "modify_host"))
    # print(newvm.execute_program("4223eb50-03bf-865c-3c99-5e0a5966d8c4", "root", "tesunet", "/root/ip.sh", "192.168.100.70"))


    # vmlist = newvm.getdatacenterlist()
    # vmlist = newvm.getclusterlist()
    # vmlist = newvm.gethostlist(None,"192.168.100.10")
    # newvm.reboot_vm(None, "newclhost", None)
    # newvm.power_on_vm("testclone")

    # for vm in vmlist:
    #     print(vm)
    # task = newvm.clone_vm("newvm","new_new151","SHOffice","192.168.100.10")
    # task.info.descriptionId=='VirtualMachine.clone'
    # task.info.key=='task-3357'
    # print(111)
    # newvm.add_disk("newvm","thick","20","422311e2-e2d8-f6d8-e1e2-8dec96a166a3") # 564d3536-b03c-a5ac-8865-dc2ecefe0b1a
    # vm-name,uuid,disk-type(thick,thin),disk-size(GB)
    # print(newvm.execute_program( "422311e2-e2d8-f6d8-e1e2-8dec96a166a3", "administrator", "tesunet@2017", "E:\\ip.bat", "192.168.100.152 255.255.255.0 192.168.100.1 192.168.100.1"))
    # print(newvm.execute_program("422311e2-e2d8-f6d8-e1e2-8dec96a166a3", "administrator", "tesunet@2017", "E:\\hostname.bat",
    #                             "new152"))
    # print(newvm.msg)

