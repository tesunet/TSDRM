var FormWizard = function () {


    return {
        //main function to initiate the module
        init: function () {
            if (!jQuery().bootstrapWizard) {
                return;
            }

            var form = $('#submit_form');


            var handleTitle = function (index, state) {
                var total = $("ul.steps").find('li').length;
                var current = index + 1;

                // set done steps
                jQuery('li', $('#form_wizard_1')).removeClass("done");
                var li_list = $("ul.steps").find('li');
                var donenum = index
                if (state == "END")
                    donenum = index + 1
                for (var i = 0; i < donenum; i++) {
                    jQuery(li_list[i]).addClass("done");
                }

                if (current == 1) {
                    $('#form_wizard_1').find('.button-previous').hide();
                } else {
                    $('#form_wizard_1').find('.button-previous').show();
                }

                if (current >= total) {
                    $('#form_wizard_1').find('.button-next').hide();
                    $('#form_wizard_1').find('.button-submit').show();
                } else {
                    $('#form_wizard_1').find('.button-next').show();
                    $('#form_wizard_1').find('.button-submit').hide();
                }
                if (state == "RUN") {
                    $('#form_wizard_1').find('.button-previous').hide();
                    $('#form_wizard_1').find('.button-next').hide();
                    $('#form_wizard_1').find('.button-submit').hide();
                }
                if (state == "END") {
                    $('#form_wizard_1').find('.button-previous').hide();
                    $('#form_wizard_1').find('.button-next').hide();
                    $('#form_wizard_1').find('.button-submit').hide();
                }
                $('#li' + current.toString() + ' a').tab("show")
                App.scrollTo($('.page-title'));
            }

            var next1 = function () {
                var myrestoreTime = ""
                if ($("input[name='optionsRadios']:checked").val() == "2" && $('#datetimepicker').val() != "")
                    myrestoreTime = $('#datetimepicker').val()
                $.ajax({
                    type: "POST",
                    dataType: 'json',
                    url: "../../filecrossnext/",
                    data:
                        {
                            restoreTime: myrestoreTime,
                            steprunid: $('#steprunid').val(),
                            stepindex: "1"
                        },
                    success: function (data) {
                        if (data["res"] == "执行成功。") {
                            $('#steprunid').val(data["data"]);
                            $('#steprunid2').val(data["nextdata"]);
                            $('#steprunstate1').val(data["steprunstate"]);
                            if (data["data"] == data["nextdata"]) {
                                //原步骤界面
                                $('#divtable').hide();
                                $('#radio1').prop("disabled", "disabled");
                                $('#radio2').prop("disabled", "disabled");
                                $('#datetimepicker').prop("readonly", "readonly");
                                //同步确认界面
                                if ($("input[name='optionsRadios']:checked").val() == "1") {
                                    $("input[name='optionsRadios1'][value='1']").prop("checked", true);
                                    $("input[name='optionsRadios1'][value='2']").prop("checked", false);
                                } else {
                                    $("input[name='optionsRadios1'][value='1']").prop("checked", false);
                                    $("input[name='optionsRadios1'][value='2']").prop("checked", true);
                                }
                                $('#datetimepicker_check').val($('#datetimepicker').val())
                                //新步骤界面
                                $('#instancename').removeProp("readonly");
                                $('#currentvm').removeProp("readonly");
                                $('#description').removeProp("readonly");
                                $("#bt_select").show();
                                $("#templatediv").addClass("input-group")
                                $("#clone").show();
                                $("#refresh").show();
                                $("#bt_ip").show();
                                $("#bt_hostname").show();
                                $("#bt_installcv").show();
                                $("#bt_registercv").show();
                                $("#bt_adddisk").show();
                                $("#bt_shutdown").show();
                                $("#bt_reboot").show();
                                $("#bt_startup").show();

                                if ($("#id").val() == "0") {
                                    $("#div1").show();
                                    $("#div2").hide();
                                    $("#div3").hide();
                                }
                                else {
                                    $.ajax({
                                        type: "POST",
                                        url: "../../getsinglevm/",
                                        dataType: 'json',
                                        data: {id: $("#id").val()},
                                        success: function (data) {
                                            $("#bt_select").hide();
                                            $("#templatediv").removeClass("input-group")
                                            $('#instancename').prop("readonly", "readonly");
                                            $('#currentvm').prop("readonly", "readonly");
                                            $('#description').prop("readonly", "readonly");
                                            $("#onstate").hide();
                                            $("#offstate").hide();
                                            $("#template_name").val(data["template_template_name"]);
                                            $("#id").val(data["id"]);
                                            $("#poolid").val(data["pool_id"]);
                                            $("#template_id").val(data["template_id"]);
                                            $("#uuid").val(data["uuid"]);
                                            $("#cpu_").val(data["cpu"]);
                                            $("#memory_").val(data["memory"]);
                                            $("#disk_").val(data["disks"]);
                                            $("#name").val(data["template_name"]);
                                            $("#ip").val(data["ip"]);
                                            $("#hostname").val(data["hostname"]);
                                            $("#clone_tag").val(data["clone"]);
                                            $("#datacenter").val(data["datacenter"]);
                                            $("#cluster").val(data["cluster"]);
                                            $("#instancename").val(data["instance_name"]);
                                            $("#currentvm").val(data["name"]);
                                            var name = data["name"];
                                            var poolid = data["pool_id"]
                                            if (data.clone == "0") {
                                                $("#div1").hide();
                                                $("#div2").show();
                                                $("#div3").hide();

                                                $.ajax({
                                                    type: "POST",
                                                    url: "../../get_progress/",
                                                    dataType: 'json',
                                                    data: {
                                                        poolid: data["pool_id"],
                                                        name: data["template_name"],
                                                        id: data["id"]
                                                    },
                                                    success: function (data) {
                                                        if (data["state"] == "3") {
                                                            $("#uuid").val(data["uuid"]);
                                                            $("#div1").hide();
                                                            $("#div2").hide();
                                                            $("#div3").show();

                                                            $("#clone_tag").val("1");
                                                            $.ajax({
                                                                type: "POST",
                                                                url: "../../get_vm_state/",
                                                                dataType: 'json',
                                                                data: {poolid: poolid, name: name},
                                                                success: function (data) {
                                                                    if (data['state'] == "poweredOn") {
                                                                        $("#onstate").show();
                                                                        $("#offstate").hide();
                                                                    } else if (data['state'] == "poweredOff") {
                                                                        $("#onstate").hide();
                                                                        $("#offstate").show();
                                                                    } else {
                                                                        $("#onstate").hide();
                                                                        $("#offstate").hide();
                                                                        alert('未定位到当前虚机');
                                                                    }
                                                                }
                                                            });
                                                        } else {
                                                            $("#progress").attr("style", "width: " + data["progress"] + "%;");

                                                        }
                                                    },
                                                })
                                            }
                                            else {
                                                $("#div1").hide();
                                                $("#div2").hide();
                                                $("#div3").show();
                                                $.ajax({
                                                    type: "POST",
                                                    url: "../../get_vm_state/",
                                                    dataType: 'json',
                                                    data: {poolid: poolid, name: name},
                                                    success: function (data) {
                                                        if (data['state'] == "poweredOn") {
                                                            $("#onstate").show();
                                                            $("#offstate").hide();
                                                        } else if (data['state'] == "poweredOff") {
                                                            $("#onstate").hide();
                                                            $("#offstate").show();
                                                        } else {
                                                            $("#onstate").hide();
                                                            $("#offstate").hide();
                                                            alert('未定位到当前虚机');
                                                        }
                                                    }
                                                });
                                            }
                                        }
                                    });
                                }

                                handleTitle(1, "EDIT");
                            }
                            else {
                                handleTitle(0, "RUN");
                            }
                            for (var i = 0; i < data["scriptrunslist"].length; i++) {
                                $("#se_2").append('<option value="' + data["scriptrunslist"][i]["script_id"] + '">' + data["scriptrunslist"][i]["script_code"] + '</option>')
                            }
                        }
                        else
                            alert(data["res"]);
                    },
                    error: function (e) {
                        alert("执行失败，请于管理员联系。");
                    }
                });
            }
            var next2 = function () {
                $.ajax({
                    type: "POST",
                    dataType: 'json',
                    url: "../../filecrossnext/",
                    data:
                        {
                            steprunid: $('#steprunid').val(),
                            stepindex: "2"
                        },
                    success: function (data) {
                        if (data["res"] == "执行成功。") {
                            $('#steprunid').val(data["data"]);
                            $('#steprunid3').val(data["nextdata"]);
                            $('#steprunstate2').val(data["steprunstate"]);
                            if (data["data"] == data["nextdata"]) {
                                //原步骤界面
                                $('#instancename').prop("readonly", "readonly");
                                $('#currentvm').prop("readonly", "readonly");
                                $('#description').prop("readonly", "readonly");
                                $("#bt_select").hide();
                                $("#templatediv").removeClass("input-group")
                                $("#clone").hide();
                                $("#refresh").hide();
                                $("#bt_ip").hide();
                                $("#bt_hostname").hide();
                                $("#bt_installcv").hide();
                                $("#bt_registercv").hide();
                                $("#bt_adddisk").hide();
                                $("#bt_shutdown").hide();
                                $("#bt_reboot").hide();
                                $("#bt_startup").hide();
                                //新步骤界面
                                $('#destClient').removeProp("disabled");
                                handleTitle(2, "EDIT");
                            }
                            else {
                                handleTitle(1, "RUN");
                            }
                            for (var i = 0; i < data["scriptrunslist"].length; i++) {
                                $("#se_3").append('<option value="' + data["scriptrunslist"][i]["script_id"] + '">' + data["scriptrunslist"][i]["script_code"] + '</option>')
                            }
                        }
                        else
                            alert(data["res"]);
                    },
                    error: function (e) {
                        alert("执行失败，请于管理员联系。");
                    }
                });
            }
            var next3 = function () {
                $.ajax({
                    type: "POST",
                    dataType: 'json',
                    url: "../../filecrossnext/",
                    data:
                        {
                            destClient: $('#destClient').val(),
                            steprunid: $('#steprunid').val(),
                            stepindex: "3"
                        },
                    success: function (data) {
                        if (data["res"] == "执行成功。") {
                            $('#steprunid').val(data["data"]);
                            $('#steprunid4').val(data["nextdata"]);
                            $('#steprunstate3').val(data["steprunstate"]);
                            if (data["data"] == data["nextdata"]) {
                                //原步骤界面
                                $('#destClient').prop("disabled", "disabled");
                                //同步确认界面
                                $('#destClient_check').val($('#destClient').val())
                                //新步骤界面
                                $('#radio3').removeProp("disabled");
                                $('#radio4').removeProp("disabled");
                                $('#radio5').removeProp("disabled");
                                $('#radio6').removeProp("disabled");
                                $('#mypath').removeProp("readonly");
                                $('#fs_se_1').removeProp("disabled");
                                $('#selectfile').show();
                                handleTitle(3, "EDIT");
                            }
                            else {
                                handleTitle(2, "RUN");
                            }
                            for (var i = 0; i < data["scriptrunslist"].length; i++) {
                                $("#se_4").append('<option value="' + data["scriptrunslist"][i]["script_id"] + '">' + data["scriptrunslist"][i]["script_code"] + '</option>')
                            }
                        }
                        else
                            alert(data["res"]);
                    },
                    error: function (e) {
                        alert("执行失败，请于管理员联系。");
                    }
                });
            }
            var next4 = function () {
                var iscover = $("input[name='overwrite']:checked").val();
                var mypath = "same"
                if ($("input[name='path']:checked").val() == "2")
                    mypath = $('#mypath').val()
                var treeObj = $.fn.zTree.getZTreeObj("treeDemo");
                var nodes = treeObj.getCheckedNodes(true);
                var selectedfile = ""
                $("#fs_se_1 option").each(function () {
                        var txt = $(this).val();
                        selectedfile = selectedfile + txt + "*!-!*"
                    }
                );
                $.ajax({
                    type: "POST",
                    dataType: 'json',
                    url: "../../filecrossnext/",
                    data:
                        {
                            iscover: iscover,
                            mypath: mypath,
                            selectedfile: selectedfile,
                            steprunid: $('#steprunid').val(),
                            stepindex: "4"
                        },
                    success: function (data) {
                        if (data["res"] == "执行成功。") {
                            $('#steprunid').val(data["data"]);
                            $('#steprunid5').val(data["nextdata"]);
                            $('#steprunstate4').val(data["steprunstate"]);
                            if (data["data"] == data["nextdata"]) {
                                //原步骤界面
                                $('#radio3').prop("disabled", "disabled");
                                $('#radio4').prop("disabled", "disabled");
                                $('#radio5').prop("disabled", "disabled");
                                $('#radio6').prop("disabled", "disabled");
                                $('#mypath').prop("readonly", "readonly")
                                $('#fs_se_1').prop("disabled", "disabled");
                                $('#selectfile').hide();
                                //同步确认界面
                                if ($("input[name='overwrite']:checked").val() == "TRUE") {
                                    $("input[name='overwrite1'][value='TRUE']").prop("checked", true);
                                    $("input[name='overwrite1'][value='FALSE']").prop("checked", false);
                                } else {
                                    $("input[name='overwrite1'][value='TRUE']").prop("checked", false);
                                    $("input[name='overwrite1'][value='FALSE']").prop("checked", true);
                                }
                                if ($("input[name='path']:checked").val() == "1") {
                                    $("input[name='path1'][value='1']").prop("checked", true);
                                    $("input[name='path1'][value='2']").prop("checked", false);
                                } else {
                                    $("input[name='path1'][value='1']").prop("checked", false);
                                    $("input[name='path1'][value='2']").prop("checked", true);
                                }
                                $('#mypath_check').val($('#mypath').val())
                                handleTitle(4, "EDIT");
                            }
                            else {
                                handleTitle(3, "RUN");
                            }
                            for (var i = 0; i < data["scriptrunslist"].length; i++) {
                                $("#se_5").append('<option value="' + data["scriptrunslist"][i]["script_id"] + '">' + data["scriptrunslist"][i]["script_code"] + '</option>')
                            }
                        }
                        else
                            alert(data["res"]);
                    },
                    error: function (e) {
                        alert("执行失败，请于管理员联系。");
                    }
                });
            }
            var next5 = function () {
                if ($("input[name='optionsRadios1']:checked").val() == "2" && $('#datetimepicker_check').val() == "")
                    alert("请输入时间。");
                else {
                    if ($('#destClient_check').val() == "")
                        alert("请选择目标客户端。");
                    else {
                        if ($("input[name='path1']:checked").val() == "2" && $('#mypath_check').val() == "")
                            alert("请输入指定路径。");
                        else {
                            var myrestoreTime = ""
                            if ($("input[name='optionsRadios1']:checked").val() == "2" && $('#datetimepicker_check').val() != "")
                                myrestoreTime = $('#datetimepicker_check').val()
                            var iscover = $("input[name='overwrite1']:checked").val();

                            var mypath = "same"
                            if ($("input[name='path1']:checked").val() == "2")
                                mypath = $('#mypath').val()
                            var treeObj = $.fn.zTree.getZTreeObj("treeDemo");
                            var nodes = treeObj.getCheckedNodes(true);
                            var selectedfile = ""
                            $("#fs_se_1 option").each(function () {
                                    var txt = $(this).val();
                                    selectedfile = selectedfile + txt + "*!-!*"
                                }
                            );
                            $.ajax({
                                type: "POST",
                                dataType: 'json',
                                url: "../../filecrossnext/",
                                data:
                                    {
                                        instanceName: $('#instanceName').val(),
                                        sourceClient: $('#sourceClient_check').val(),
                                        destClient: $('#destClient_check').val(),
                                        restoreTime: myrestoreTime,
                                        iscover: iscover,
                                        mypath: mypath,
                                        selectedfile: selectedfile,
                                        steprunid: $('#steprunid').val(),
                                        stepindex: "5"
                                    },
                                success: function (data) {
                                    if (data["res"] == "执行成功。") {
                                        $('#steprunid').val(data["data"]);
                                        $('#steprunid6').val(data["nextdata"]);
                                        $('#steprunstate5').val(data["steprunstate"]);
                                        if (data["data"] == data["nextdata"]) {
                                            //新步骤界面
                                            $('#checkservice').removeProp("disabled");
                                            handleTitle(5, "EDIT");
                                        }
                                        else {
                                            handleTitle(4, "RUN");
                                        }
                                        for (var i = 0; i < data["scriptrunslist"].length; i++) {
                                            $("#se_6").append('<option value="' + data["scriptrunslist"][i]["script_id"] + '">' + data["scriptrunslist"][i]["script_code"] + '</option>')
                                        }
                                    }
                                    else
                                        alert(data["res"]);
                                },
                                error: function (e) {
                                    alert("执行失败，请于管理员联系。");
                                }
                            });
                        }
                    }
                }
            }
            var next6 = function () {
                var checkservice = "FALSE"
                if ($('#checkservice').is(':checked'))
                    checkservice = "TRUE"
                $.ajax({
                    type: "POST",
                    dataType: 'json',
                    url: "../../filecrossnext/",
                    data:
                        {
                            checkservice: checkservice,
                            steprunid: $('#steprunid').val(),
                            stepindex: "6"
                        },
                    success: function (data) {
                        if (data["res"] == "执行成功。") {
                            $('#steprunid').val(data["data"]);
                            $('#steprunid7').val(data["nextdata"]);
                            $('#steprunstate6').val(data["steprunstate"]);
                            if (data["data"] == data["nextdata"]) {
                                //原步骤界面
                                $('#checkservice').prop("disabled", "disabled");
                                //新步骤界面
                                $('#checkapp').removeProp("disabled");
                                handleTitle(6, "EDIT");
                            }
                            else {
                                handleTitle(5, "RUN");
                            }
                        }
                        else
                            alert(data["res"]);
                    },
                    error: function (e) {
                        alert("执行失败，请于管理员联系。");
                    }
                });
            }

            var previous2 = function () {
                $.ajax({
                    type: "POST",
                    dataType: 'json',
                    url: "../../filecrossprevious/",
                    data:
                        {
                            steprunid: $('#steprunid').val(),
                        },
                    success: function (data) {
                        if (data["res"] == "执行成功。") {
                            $('#steprunid').val(data["data"]);
                            //新步骤界面
                            $('#divtable').show();
                            $('#radio1').removeProp("disabled");
                            $('#radio2').removeProp("disabled");
                            $('#datetimepicker').removeProp("readonly");
                            //原步骤界面
                            $('#instancename').prop("readonly", "readonly");
                            $('#currentvm').prop("readonly", "readonly");
                            $('#description').prop("readonly", "readonly");
                            $("#bt_select").hide();
                            $("#templatediv").removeClass("input-group")
                            $("#clone").hide();
                            $("#refresh").hide();
                            $("#bt_ip").hide();
                            $("#bt_hostname").hide();
                            $("#bt_installcv").hide();
                            $("#bt_registercv").hide();
                            $("#bt_adddisk").hide();
                            $("#bt_shutdown").hide();
                            $("#bt_reboot").hide();
                            $("#bt_startup").hide();
                            $('#steprunstate1').val("EDIT")
                            handleTitle(0, "EDIT");
                        }
                        else
                            alert(data["res"]);
                    },
                    error: function (e) {
                        alert("执行失败，请于管理员联系。");
                    }
                });
            }

            var previous3 = function () {
                $.ajax({
                    type: "POST",
                    dataType: 'json',
                    url: "../../filecrossprevious/",
                    data:
                        {
                            steprunid: $('#steprunid').val(),
                        },
                    success: function (data) {
                        if (data["res"] == "执行成功。") {
                            $('#steprunid').val(data["data"]);
                            //新步骤界面
                            $('#instancename').removeProp("readonly");
                            $('#currentvm').removeProp("readonly");
                            $('#description').removeProp("readonly");
                            $("#bt_select").show();
                            $("#templatediv").addClass("input-group")
                            $("#clone").show();
                            $("#refresh").show();
                            $("#bt_ip").show();
                            $("#bt_hostname").show();
                            $("#bt_installcv").show();
                            $("#bt_registercv").show();
                            $("#bt_adddisk").show();
                            $("#bt_shutdown").show();
                            $("#bt_reboot").show();
                            $("#bt_startup").show();
                            if ($("#id").val() == "0") {
                                $("#div1").show();
                                $("#div2").hide();
                                $("#div3").hide();
                            }
                            else {
                                $.ajax({
                                    type: "POST",
                                    url: "../../getsinglevm/",
                                    dataType: 'json',
                                    data: {id: $("#id").val()},
                                    success: function (data) {
                                        $("#bt_select").hide();
                                        $("#templatediv").removeClass("input-group")
                                        $('#instancename').prop("readonly", "readonly");
                                        $('#currentvm').prop("readonly", "readonly");
                                        $('#description').prop("readonly", "readonly");
                                        $("#onstate").hide();
                                        $("#offstate").hide();
                                        $("#template_name").val(data["template_template_name"]);
                                        $("#id").val(data["id"]);
                                        $("#poolid").val(data["pool_id"]);
                                        $("#template_id").val(data["template_id"]);
                                        $("#uuid").val(data["uuid"]);
                                        $("#cpu_").val(data["cpu"]);
                                        $("#memory_").val(data["memory"]);
                                        $("#disk_").val(data["disks"]);
                                        $("#name").val(data["template_name"]);
                                        $("#ip").val(data["ip"]);
                                        $("#hostname").val(data["hostname"]);
                                        $("#clone_tag").val(data["clone"]);
                                        $("#datacenter").val(data["datacenter"]);
                                        $("#cluster").val(data["cluster"]);
                                        $("#instancename").val(data["instance_name"]);
                                        $("#currentvm").val(data["name"]);
                                        var name = data["name"];
                                        var poolid = data["pool_id"]
                                        if (data.clone == "0") {
                                            $("#div1").hide();
                                            $("#div2").show();
                                            $("#div3").hide();

                                            $.ajax({
                                                type: "POST",
                                                url: "../../get_progress/",
                                                dataType: 'json',
                                                data: {
                                                    poolid: data["pool_id"],
                                                    name: data["template_name"],
                                                    id: data["id"]
                                                },
                                                success: function (data) {
                                                    if (data["state"] == "3") {
                                                        $("#uuid").val(data["uuid"]);
                                                        $("#div1").hide();
                                                        $("#div2").hide();
                                                        $("#div3").show();

                                                        $("#clone_tag").val("1");
                                                        $.ajax({
                                                            type: "POST",
                                                            url: "../../get_vm_state/",
                                                            dataType: 'json',
                                                            data: {poolid: poolid, name: name},
                                                            success: function (data) {
                                                                if (data['state'] == "poweredOn") {
                                                                    $("#onstate").show();
                                                                    $("#offstate").hide();
                                                                } else if (data['state'] == "poweredOff") {
                                                                    $("#onstate").hide();
                                                                    $("#offstate").show();
                                                                } else {
                                                                    $("#onstate").hide();
                                                                    $("#offstate").hide();
                                                                    alert('未定位到当前虚机');
                                                                }
                                                            }
                                                        });
                                                    } else {
                                                        $("#progress").attr("style", "width: " + data["progress"] + "%;");

                                                    }
                                                },
                                            })
                                        }
                                        else {
                                            $("#div1").hide();
                                            $("#div2").hide();
                                            $("#div3").show();
                                            $.ajax({
                                                type: "POST",
                                                url: "../../get_vm_state/",
                                                dataType: 'json',
                                                data: {poolid: poolid, name: name},
                                                success: function (data) {
                                                    if (data['state'] == "poweredOn") {
                                                        $("#onstate").show();
                                                        $("#offstate").hide();
                                                    } else if (data['state'] == "poweredOff") {
                                                        $("#onstate").hide();
                                                        $("#offstate").show();
                                                    } else {
                                                        $("#onstate").hide();
                                                        $("#offstate").hide();
                                                        alert('未定位到当前虚机');
                                                    }
                                                }
                                            });
                                        }
                                    }
                                });
                            }
                            //原步骤界面
                            $('#destClient').prop("disabled", "disabled");

                            $('#steprunstate2').val("EDIT")
                            handleTitle(1, "EDIT");
                        }
                        else
                            alert(data["res"]);
                    },
                    error: function (e) {
                        alert("执行失败，请于管理员联系。");
                    }
                });
            }

            var previous4 = function () {
                $.ajax({
                    type: "POST",
                    dataType: 'json',
                    url: "../../filecrossprevious/",
                    data:
                        {
                            steprunid: $('#steprunid').val(),
                        },
                    success: function (data) {
                        if (data["res"] == "执行成功。") {
                            $('#steprunid').val(data["data"]);
                            //新步骤界面
                            $('#destClient').removeProp("disabled");
                            //原步骤界面
                            $('#radio3').prop("disabled", "disabled");
                            $('#radio4').prop("disabled", "disabled");
                            $('#radio5').prop("disabled", "disabled");
                            $('#radio6').prop("disabled", "disabled");
                            $('#mypath').prop("readonly", "readonly")
                            $('#fs_se_1').prop("disabled", "disabled");
                            $('#selectfile').hide();

                            $('#steprunstate3').val("EDIT")
                            handleTitle(2, "EDIT");
                        }
                        else
                            alert(data["res"]);
                    },
                    error: function (e) {
                        alert("执行失败，请于管理员联系。");
                    }
                });
            }

            var previous5 = function () {
                $.ajax({
                    type: "POST",
                    dataType: 'json',
                    url: "../../filecrossprevious/",
                    data:
                        {
                            steprunid: $('#steprunid').val(),
                        },
                    success: function (data) {
                        if (data["res"] == "执行成功。") {
                            $('#steprunid').val(data["data"]);
                            //新步骤界面
                            $('#radio3').removeProp("disabled");
                            $('#radio4').removeProp("disabled");
                            $('#radio5').removeProp("disabled");
                            $('#radio6').removeProp("disabled");
                            $('#mypath').removeProp("readonly");
                            $('#fs_se_1').removeProp("disabled");
                            $('#selectfile').show();

                            $('#steprunstate4').val("EDIT")
                            handleTitle(3, "EDIT");
                        }
                        else
                            alert(data["res"]);
                    },
                    error: function (e) {
                        alert("执行失败，请于管理员联系。");
                    }
                });
            }

            var previous6 = function () {
                $.ajax({
                    type: "POST",
                    dataType: 'json',
                    url: "../../filecrossprevious/",
                    data:
                        {
                            steprunid: $('#steprunid').val(),
                        },
                    success: function (data) {
                        if (data["res"] == "执行成功。") {
                            $('#steprunid').val(data["data"]);
                            //原步骤界面
                            $('#checkservice').prop("disabled", "disabled");

                            $('#steprunstate5').val("EDIT")
                            handleTitle(4, "EDIT");
                        }
                        else
                            alert(data["res"]);

                    },
                    error: function (e) {
                        alert("执行失败，请于管理员联系。");
                    }
                });
            }

            var previous7 = function () {
                $.ajax({
                    type: "POST",
                    dataType: 'json',
                    url: "../../filecrossprevious/",
                    data:
                        {
                            steprunid: $('#steprunid').val(),
                        },
                    success: function (data) {
                        if (data["res"] == "执行成功。") {
                            $('#steprunid').val(data["data"]);
                            //新步骤界面
                            $('#checkservice').removeProp("disabled");
                            //原步骤界面
                            $('#checkapp').prop("disabled", "disabled");


                            $('#steprunstate6').val("EDIT")
                            handleTitle(5, "EDIT");
                        }
                        else
                            alert(data["res"]);
                    },
                    error: function (e) {
                        alert("执行失败，请于管理员联系。");
                    }
                });
            }


            // default form wizard
            $('#form_wizard_1').bootstrapWizard({
                'nextSelector': '.button-next',
                'previousSelector': '.button-previous',
                onTabClick: function (tab, navigation, index, clickedIndex) {
                    if ($('#steprunid').val() != $('#steprunid' + (clickedIndex + 1).toString()).val()) {
                        $('#form_wizard_1').find('.button-previous').hide();
                        $('#form_wizard_1').find('.button-submit').hide();
                        $('#form_wizard_1').find('.button-next').hide();
                        App.scrollTo($('.page-title'));
                    } else {
                        if ($('#steprunid').val() == $('#steprunid1').val()) {
                            handleTitle(0, $('#steprunstate1').val());
                        }
                        if ($('#steprunid').val() == $('#steprunid2').val()) {
                            handleTitle(1, $('#steprunstate2').val());
                        }
                        if ($('#steprunid').val() == $('#steprunid3').val()) {
                            handleTitle(2, $('#steprunstate3').val());
                        }
                        if ($('#steprunid').val() == $('#steprunid4').val()) {
                            handleTitle(3, $('#steprunstate4').val());
                        }
                        if ($('#steprunid').val() == $('#steprunid5').val()) {
                            handleTitle(4, $('#steprunstate5').val());
                        }
                        if ($('#steprunid').val() == $('#steprunid6').val()) {
                            handleTitle(5, $('#steprunstate6').val());
                        }
                        if ($('#steprunid').val() == $('#steprunid7').val()) {
                            handleTitle(6, $('#steprunstate7').val());
                        }
                        if ($('#steprunid').val() == "0") {
                            handleTitle(6, "END");
                        }
                    }

                },
                onNext: function (tab, navigation, index) {
                    if (index == 1) {
                        next1()
                    }
                    if (index == 2) {
                        next2()
                    }
                    if (index == 3) {
                        next3()
                    }
                    if (index == 4) {
                        next4()
                    }
                    if (index == 5) {
                        next5()
                    }
                    if (index == 6) {
                        next6()
                    }
                },
                onPrevious: function (tab, navigation, index) {
                    if (index == 0) {
                        previous2()
                    }
                    if (index == 1) {
                        previous3()
                    }
                    if (index == 2) {
                        previous4()
                    }
                    if (index == 3) {
                        previous5()
                    }
                    if (index == 4) {
                        previous6()
                    }
                    if (index == 5) {
                        previous7()
                    }
                    handleTitle(tab, navigation, index);
                },
                onTabShow: function (tab, navigation, index) {
                    var total = navigation.find('li').length;
                    var current = index + 1;
                    var $percent = (current / total) * 100;
                    $('#form_wizard_1').find('.progress-bar').css({
                        width: $percent + '%'
                    });
                }
            });
            $('#form_wizard_1 .button-submit').click(function () {
                var checkapp = "FALSE"
                if ($('#checkapp').is(':checked'))
                    checkapp = "TRUE"
                $.ajax({
                    type: "POST",
                    dataType: 'json',
                    url: "../../filecrossfinish/",
                    data:
                        {
                            checkapp: checkapp,
                            steprunid: $('#steprunid').val(),
                        },
                    success: function (data) {
                        if (data["res"] == "执行成功。") {
                            $('#steprunid').val("0");
                            //原步骤界面
                            $('#checkapp').prop("disabled", "disabled");
                            $('#form_wizard_1').find('.button-previous').hide();
                            $('#form_wizard_1').find('.button-submit').hide();
                            alert("流程结束。");
                            return true
                        }
                        else
                            alert(data["res"]);
                        return false
                    },
                    error: function (e) {
                        alert("执行失败，请于管理员联系。");
                        return false
                    }
                });
            }).hide();
            if ($('#steprunid').val() == $('#steprunid1').val()) {
                handleTitle(0, $('#steprunstate1').val());
            }
            if ($('#steprunid').val() == $('#steprunid2').val()) {
                handleTitle(1, $('#steprunstate2').val());
            }
            if ($('#steprunid').val() == $('#steprunid3').val()) {
                handleTitle(2, $('#steprunstate3').val());
            }
            if ($('#steprunid').val() == $('#steprunid4').val()) {
                handleTitle(3, $('#steprunstate4').val());
            }
            if ($('#steprunid').val() == $('#steprunid5').val()) {
                handleTitle(4, $('#steprunstate5').val());
            }
            if ($('#steprunid').val() == $('#steprunid6').val()) {
                handleTitle(5, $('#steprunstate6').val());
            }
            if ($('#steprunid').val() == $('#steprunid7').val()) {
                handleTitle(6, $('#steprunstate7').val());
            }
            if ($('#steprunid').val() == "0") {
                handleTitle(6, "END");
            }

        }

    };

}();

var setting = {
    async: {
        enable: true,
        url: '../../getfiletree/',
        autoParam: ["id"],
        otherParam: {"clientName": $('#sourceClient').val()},
        dataFilter: filter
    },
    check: {
        enable: true,
        chkStyle: "checkbox",               //多选
        chkboxType: {"Y": "s", "N": "ps"}  //不级联父节点选择
    },
    view: {
        showLine: false
    },

};

function filter(treeId, parentNode, childNodes) {
    if (!childNodes) return null;
    for (var i = 0, l = childNodes.length; i < l; i++) {
        childNodes[i].name = childNodes[i].name.replace(/\.n/g, '.');
    }
    return childNodes;
}

jQuery(document).ready(function () {

    //第一步，选择恢复时间点
    $('#sample_1').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../../filerecoverydata?clientName=" + $('#sourceClient').val(),
        "columns": [
            {"data": "jobId"},
            {"data": "jobType"},
            {"data": "Level"},
            {"data": "StartTime"},
            {"data": "LastTime"},
            {"data": null},
        ],

        "columnDefs": [{
            "targets": -1,
            "data": null,
            "defaultContent": "<button  id='select' title='选择'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-check'></i></button>"
        }],

        "oLanguage": {
            "sLengthMenu": "&nbsp;&nbsp;每页显示 _MENU_ 条记录",
            "sZeroRecords": "抱歉， 没有找到",
            "sInfo": "从 _START_ 到 _END_ /共 _TOTAL_ 条数据",
            "sInfoEmpty": '',
            "sInfoFiltered": "(从 _MAX_ 条数据中检索)",
            "sSearch": "搜索",
            "oPaginate": {
                "sFirst": "首页",
                "sPrevious": "前一页",
                "sNext": "后一页",
                "sLast": "尾页"
            },
            "sZeroRecords": "没有检索到数据",

        }
    });
    $('#sample_1 tbody').on('click', 'button#select', function () {
        var table = $('#sample_1').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $("#datetimepicker").val(data.LastTime);
        $("input[name='optionsRadios'][value='1']").prop("checked", false);
        $("input[name='optionsRadios'][value='2']").prop("checked", true);
    });

    if ($('#datetimepicker').val() == "") {
        $("input[name='optionsRadios'][value='1']").prop("checked", true);
        $("input[name='optionsRadios'][value='2']").prop("checked", false);
    } else {
        $("input[name='optionsRadios'][value='1']").prop("checked", false);
        $("input[name='optionsRadios'][value='2']").prop("checked", true);
    }
    if ($('#steprunid').val() != $('#steprunid1').val() || $('#steprunstate1').val() == "RUN") {

        $('#divtable').hide();
        $('#radio1').prop("disabled", "disabled");
        $('#radio2').prop("disabled", "disabled");
        $('#datetimepicker').prop("readonly", "readonly");

    }
    $('#datetimepicker').datetimepicker({
        format: 'yyyy-mm-dd hh:ii:ss',
    });


    //第二步，创建恢复资源
    $('#sample_2').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../../getvmtemplate/",
        "columns": [
            {"data": "id"},
            {"data": "template_name"},
            {"data": "name"},
            {"data": "description"},
            {"data": null}
        ],

        "columnDefs": [{
            "targets": -1,
            "data": null,
            "defaultContent": "<button  id='select' title='选择'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-check'></i></button>"
        }],
        "oLanguage": {
            "sLengthMenu": "&nbsp;&nbsp;每页显示 _MENU_ 条记录",
            "sZeroRecords": "抱歉， 没有找到",
            "sInfo": "从 _START_ 到 _END_ /共 _TOTAL_ 条数据",
            "sInfoEmpty": '',
            "sInfoFiltered": "(从 _MAX_ 条数据中检索)",
            "sSearch": "搜索",
            "oPaginate": {
                "sFirst": "首页",
                "sPrevious": "前一页",
                "sNext": "后一页",
                "sLast": "尾页"
            },
            "sZeroRecords": "没有检索到数据",

        }
    });

    $('#sample_2 tbody').on('click', 'button#select', function () {
        var table = $('#sample_2').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $("#datacenter").empty();
        $("#template_name").val(data.template_name);
        $("#cpu_").val(data.cpu);
        $("#memory_").val(data.memory);
        $("#disk_").val(data.disks);
        $("#name").val(data.name);
        $("#poolid").val(data.pool_id);
        $("#template_id").val(data.id);
        $("#system").val(data.system);
        $("#datacenter").val(data.datacenter);
        $("#cluster").val(data.cluster);
        $('#static1').modal('hide');
    });

    if ($('#steprunid').val() != $('#steprunid2').val() || $('#steprunstate2').val() == "RUN") {
        $('#instancename').prop("readonly", "readonly");
        $('#currentvm').prop("readonly", "readonly");
        $('#description').prop("readonly", "readonly");
        $("#bt_select").hide();
        $("#templatediv").removeClass("input-group")
        $("#clone").hide();
        $("#refresh").hide();
        $("#bt_ip").hide();
        $("#bt_hostname").hide();
        $("#bt_installcv").hide();
        $("#bt_registercv").hide();
        $("#bt_adddisk").hide();
        $("#bt_shutdown").hide();
        $("#bt_reboot").hide();
        $("#bt_startup").hide();


    }

    if ($("#id").val() == "") {
        $("#clone_tag").val("0");
        $("#div1").show();
        $("#div2").hide();
        $("#div3").hide();
        $("#id").val("0")
    }
    else {
        $.ajax({
            type: "POST",
            url: "../../getsinglevm/",
            dataType: 'json',
            data: {id: $("#id").val()},
            success: function (data) {
                $("#bt_select").hide();
                $("#templatediv").removeClass("input-group");
                $('#instancename').prop("readonly", "readonly");
                $('#currentvm').prop("readonly", "readonly");
                $('#description').prop("readonly", "readonly");
                $("#onstate").hide();
                $("#offstate").hide();
                $("#template_name").val(data["template_template_name"]);
                $("#id").val(data["id"]);
                $("#poolid").val(data["pool_id"]);
                $("#template_id").val(data["template_id"]);
                $("#uuid").val(data["uuid"]);
                $("#cpu_").val(data["cpu"]);
                $("#memory_").val(data["memory"]);
                $("#disk_").val(data["disks"]);
                $("#name").val(data["template_name"]);
                $("#ip").val(data["ip"]);
                $("#hostname").val(data["hostname"]);
                $("#clone_tag").val(data["clone"]);
                $("#datacenter").val(data["datacenter"]);
                $("#cluster").val(data["cluster"]);
                $("#instancename").val(data["instance_name"]);
                $("#currentvm").val(data["name"]);
                var name = data["name"];
                var poolid = data["pool_id"]
                if (data.clone == "0") {
                    $("#div1").hide();
                    $("#div2").show();
                    $("#div3").hide();

                    $.ajax({
                        type: "POST",
                        url: "../../get_progress/",
                        dataType: 'json',
                        data: {poolid: data["pool_id"], name: data["template_name"], id: data["id"]},
                        success: function (data) {
                            if (data["state"] == "3") {
                                $("#uuid").val(data["uuid"]);
                                $("#div1").hide();
                                $("#div2").hide();
                                $("#div3").show();

                                $("#clone_tag").val("1");
                                $.ajax({
                                    type: "POST",
                                    url: "../../get_vm_state/",
                                    dataType: 'json',
                                    data: {poolid: poolid, name: name},
                                    success: function (data) {
                                        if (data['state'] == "poweredOn") {
                                            $("#onstate").show();
                                            $("#offstate").hide();
                                        } else if (data['state'] == "poweredOff") {
                                            $("#onstate").hide();
                                            $("#offstate").show();
                                        } else {
                                            $("#onstate").hide();
                                            $("#offstate").hide();
                                            alert('未定位到当前虚机');
                                        }
                                    }
                                });
                            } else {
                                $("#progress").attr("style", "width: " + data["progress"] + "%;");

                            }
                        },
                    })
                }
                else {
                    $("#div1").hide();
                    $("#div2").hide();
                    $("#div3").show();
                    $.ajax({
                        type: "POST",
                        url: "../../get_vm_state/",
                        dataType: 'json',
                        data: {poolid: poolid, name: name},
                        success: function (data) {
                            if (data['state'] == "poweredOn") {
                                $("#onstate").show();
                                $("#offstate").hide();
                            } else if (data['state'] == "poweredOff") {
                                $("#onstate").hide();
                                $("#offstate").show();
                            } else {
                                $("#onstate").hide();
                                $("#offstate").hide();
                                alert('未定位到当前虚机');
                            }
                        }
                    });
                }
            }
        });


    }


    $("#refresh").click(function () {
        $.ajax({
            type: "POST",
            url: "../../get_progress/",
            dataType: 'json',
            data: {poolid: $("#poolid").val(), name: $("#name").val(), id: $("#id").val()},
            success: function (data) {
                if (data["state"] == "3") {
                    $("#uuid").val(data["uuid"]);
                    $("#div1").hide()
                    $("#div2").hide()
                    $("#div3").show()
                    $("#clone_tag").val("1");
                } else {
                    $("#progress").attr("style", "width: " + data["progress"] + "%;");

                }
            },
        })
    });

    $("#ipsave").click(function () {
        var table = $('#sample_1').DataTable();

        $.ajax({
            type: "POST",
            url: "../../vm_ipsave/",
            dataType: 'json',
            data: {
                id: $("#id").val(),
                uuid: $("#uuid").val(),
                poolid: $("#poolid").val(),
                path: $("#ip_path").val(),
                ip: $("#ip_ip").val(),
                mask: $("#ip_mask").val(),
                gateway: $("#ip_gateway").val(),
                dns: $("#ip_dns").val(),
                user: $("#ip_user").val(),
                password: $("#ip_password").val()
            },
            success: function (data) {
                if (data["value"] == "1") {

                    $("#ip").val($("#ip_ip").val());
                    table.ajax.reload();
                    alert(data["text"]);
                } else {
                    alert(data["text"]);

                }
            },
        })
    });

    $("#hostsave").click(function () {
        var table = $('#sample_1').DataTable();
        $.ajax({
            type: "POST",
            url: "../../vm_hostsave/",
            dataType: 'json',
            data: {
                id: $("#id").val(),
                uuid: $("#uuid").val(),
                poolid: $("#poolid").val(),
                path: $("#host_path").val(),
                hostname: $("#host_name").val(),
                user: $("#host_user").val(),
                password: $("#host_password").val()
            },
            success: function (data) {
                if (data["value"] == "1") {

                    $("#hostname").val($("#host_name").val());
                    table.ajax.reload();
                    alert(data["text"]);
                } else {
                    alert(data["text"]);

                }
            },
        })
    });
    $("#disksave").click(function () {
        var table = $('#sample_1').DataTable();
        $.ajax({
            type: "POST",
            url: "../../vm_disksave/",
            dataType: 'json',
            data: {
                id: $("#id").val(),
                name: $("#currentvm").val(),
                uuid: $("#uuid").val(),
                poolid: $("#poolid").val(),
                disksize: $("#disksize").val(),
                disktype: $("#disktype").val(),
                selectdisk: $("#selectdisk").val(),
                path: $("#disk_path").val(),
                user: $("#disk_user").val(),
                password: $("#disk_password").val()
            },
            success: function (data) {
                if (data["value"] == "1") {

                    $("#disk_").val(data["size"]);
                    table.ajax.reload();
                    alert(data["text"]);
                } else {
                    alert(data["text"]);

                }
            },
        })
    });
    $("#installcvsave").click(function () {
        var table = $('#sample_1').DataTable();
        $.ajax({
            type: "POST",
            url: "../../vm_installcvsave/",
            dataType: 'json',
            data: {
                id: $("#id").val(),
                uuid: $("#uuid").val(),
                poolid: $("#poolid").val(),
                hostname: $("#hostname").val(),
                path: $("#installcv_path").val(),
                user: $("#installcv_user").val(),
                password: $("#installcv_password").val()
            },
            success: function (data) {
                if (data["value"] == "1") {
                    alert(data["text"]);
                } else {
                    alert(data["text"]);

                }
            },
        })
    });
    $("#bt_registercv").click(function () {
        var table = $('#sample_1').DataTable();
        $.ajax({
            type: "POST",
            url: "../../registercvsave/",
            dataType: 'json',
            data: {hostname: $("#hostname").val()},
            success: function (data) {
                if (data["value"] == "1") {
                    alert(data["text"]);
                } else {
                    alert(data["text"]);

                }
            },
        })
    });

    $("#clone").click(function () {
        if ($("#template_id").val() == "") {
            alert("输入有误，请选择虚机模板。");
        }
        else {
            if ($("#instancename").val() == "") {
                alert("输入有误，请输入实例名称。");
            }
            else {
                if ($("#currentvm").val() == "") {
                    alert("输入有误，请输入新虚机名称。")
                }
                else {
                    $.ajax({
                        type: "POST",
                        dataType: 'json',
                        url: "../../clonevm/",
                        data: $('#submit_form').serialize(),
                        success: function (data) {
                            if (data["value"] == "1") {
                                $("#id").val(data["id"]);
                                $("#div1").hide();
                                $("#div2").show();
                                $("#div3").hide();
                            } else {
                                alert(data);

                            }
                        },
                        error: function (e) {
                            alert("克隆失败，请于客服联系。");
                        }
                    })
                }
            }
        }
    });

    $("#bt_shutdown").click(function () {
        $.ajax({
            type: "POST",
            url: "../../shutdownvm/",
            dataType: 'json',
            data: {
                currentvm: $("#currentvm").val(),
                poolid: $("#poolid").val(),
            },
            success: function (data) {
                alert(data['text']);
                $("#onstate").hide();
                $("#offstate").show();
            },
        });
    });

    $("#bt_reboot").click(function () {
        $.ajax({
            type: "POST",
            url: "../../rebootvm/",
            dataType: 'json',
            data: {
                uuid: $("#uuid").val(),
                hostname: $("#hostname").val(),
                poolid: $("#poolid").val(),
            },
            success: function (data) {
                alert(data['text']);
            },
        });
    });

    $("#bt_startup").click(function () {
        $.ajax({
            type: "POST",
            url: "../../poweronvm/",
            dataType: 'json',
            data: {
                currentvm: $("#currentvm").val(),
                poolid: $("#poolid").val(),
            },
            success: function (data) {
                alert(data['text']);
                $("#onstate").show();
                $("#offstate").hide();
            },
        });
    });

    //第三步，选择恢复资源
    $("#destClient").val($("#destClientvalue").val());
    if ($('#steprunid').val() != $('#steprunid3').val() || $('#steprunstate3').val() == "RUN") {
        $('#destClient').prop("disabled", "disabled");

    }

    $.fn.zTree.init($("#treeDemo"), setting);


    //第四步，输入参数
    $('#selectpath').click(function () {
        $('#fs_se_1').empty();
        $('#fs_se_1_check').empty();
        var treeObj = $.fn.zTree.getZTreeObj("treeDemo");
        var nodes = treeObj.getCheckedNodes(true);
        for (var k = 0, length = nodes.length; k < length; k++) {
            var halfCheck = nodes[k].getCheckStatus();
            if (!halfCheck.half) {
                $("#fs_se_1").append("<option value='\\" + nodes[k].id + "\\'>\\" + nodes[k].id + "\\</option>");
                $("#fs_se_1_check").append("<option value='\\" + nodes[k].id + "\\'>\\" + nodes[k].id + "\\</option>");
            }
        }
        if (nodes.length == 0) {
            $("#fs_se_1").append("<option value='\\'>\\</option>");
            $("#fs_se_1_check").append("<option value='\\'>\\</option>");
        }
    })
    if ($('#overwritevalue').val() == "TRUE") {
        $("input[name='overwrite'][value='TRUE']").prop("checked", true);
        $("input[name='overwrite'][value='FALSE']").prop("checked", false);
    } else {
        $("input[name='overwrite'][value='TRUE']").prop("checked", false);
        $("input[name='overwrite'][value='FALSE']").prop("checked", true);
    }
    if ($('#pathvalue').val() == "same") {
        $("input[name='path'][value='1']").prop("checked", true);
        $("input[name='path'][value='2']").prop("checked", false);
        $('#mypath').val("")
    } else {
        $("input[name='path'][value='1']").prop("checked", false);
        $("input[name='path'][value='2']").prop("checked", true);
        $('#mypath').val($('#pathvalue').val())
    }
    $('#fs_se_1_check').empty();
    $('#fs_se_1').empty();
    var selectedfile = $('#fs_se_1value').val();
    var files = selectedfile.split("*!-!*");
    var index = 0
    for (var i = 0; i < files.length; i++) {
        if (files[i] != "") {
            index = index + 1
            $("#fs_se_1").append("<option value='" + files[i] + "'>" + files[i] + "</option>");
            $("#fs_se_1_check").append("<option value='" + files[i] + "'>" + files[i] + "</option>");
        }
    }
    if (index == 0) {
        $("#fs_se_1").append("<option value='\\'>\\</option>");
        $("#fs_se_1_check").append("<option value='\\'>\\</option>");
    }

    if ($('#steprunid').val() != $('#steprunid4').val() || $('#steprunstate4').val() == "RUN") {
        $('#radio3').prop("disabled", "disabled");
        $('#radio4').prop("disabled", "disabled");
        $('#radio5').prop("disabled", "disabled");
        $('#radio6').prop("disabled", "disabled");
        $('#mypath').prop("readonly", "readonly");
        $('#fs_se_1').prop("disabled", "disabled");
        $('#selectfile').hide();


    }

    //第五步，提交任务
    if ($('#datetimepicker_check').val() == "") {
        $("input[name='optionsRadios1'][value='1']").prop("checked", true);
        $("input[name='optionsRadios1'][value='2']").prop("checked", false);
    } else {
        $("input[name='optionsRadios1'][value='1']").prop("checked", false);
        $("input[name='optionsRadios1'][value='2']").prop("checked", true);
    }
    $("#destClient_check").val($("#destClientvalue").val());
    if ($('#overwritevalue').val() == "TRUE") {
        $("input[name='overwrite1'][value='TRUE']").prop("checked", true);
        $("input[name='overwrite1'][value='FALSE']").prop("checked", false);
    } else {
        $("input[name='overwrite1'][value='TRUE']").prop("checked", false);
        $("input[name='overwrite1'][value='FALSE']").prop("checked", true);
    }
    if ($('#pathvalue').val() == "same") {
        $("input[name='path1'][value='1']").prop("checked", true);
        $("input[name='path1'][value='2']").prop("checked", false);
        $('#mypath_check').val("")
    } else {
        $("input[name='path1'][value='1']").prop("checked", false);
        $("input[name='path1'][value='2']").prop("checked", true);
        $('#mypath_check').val($('#pathvalue').val())
    }

    //第六步，启用灾备环境
    $('#checkservice').prop("checked", false);
    if ($('#checkservicevalue').val() == "TRUE")
        $('#checkservice').prop("checked", true);
    if ($('#steprunid').val() != $('#steprunid6').val() || $('#steprunstate6').val() == "RUN") {
        $('#checkservice').prop("disabled", "disabled");
    }

    //第七步，业务验证确认
    $('#checkapp').prop("checked", false);
    if ($('#checkappvalue').val() == "TRUE")
        $('#checkapp').prop("checked", true);
    if ($('#steprunid').val() != $('#steprunid7').val() || $('#steprunstate7').val() == "RUN") {
        $('#checkapp').prop("disabled", "disabled");
    }
    //脚本窗口
    $('#se_1').dblclick(function () {
        $("#b1").hide();
        if ($("#se_1").find('option:selected').length == 0) {
            alert("请至少选中一个脚本。")
        } else {
            if ($("#se_1").find('option:selected').length > 1) {
                alert("请不要选择多条记录。");
            } else {
                // 获取当前步骤脚本信息
                $("#static").modal({backdrop: "static"});
                $("#script_button").val($("#se_1").find('option:selected').val());

                var steprunid = $("#steprunid").val();
                var scriptid = $("#se_1").find('option:selected').val();
                $.ajax({
                    url: "/get_current_scriptinfo/",
                    type: "post",
                    data: {"steprunid": steprunid, "scriptid": scriptid},
                    success: function (data) {
                        $("#code").val(data.data["code"]);
                        $("#script_ip").val(data.data["ip"]);
                        $("#script_port").val(data.data["port"]);
                        $("#filename").val(data.data["filename"]);
                        $("#scriptpath").val(data.data["scriptpath"]);
                        $("#scriptstate").val(data.data["state"]);
                        $("#ontime").val(data.data["starttime"]);
                        $("#offtime").val(data.data["endtime"]);
                        $("#operator").val(data.data["operator"]);
                        if (data.data["show_button"] == 1) {
                            $("#b1").show();
                        } else {
                            $("#b1").hide();
                        }
                    }
                });
            }
        }

    });
    $('#se_2').dblclick(function () {
        $("#b1").hide();
        if ($("#se_2").find('option:selected').length == 0) {
            alert("请至少选中一个脚本。")
        } else {
            if ($("#se_2").find('option:selected').length > 1) {
                alert("请不要选择多条记录。");
            } else {
                $("#static").modal({backdrop: "static"});
                $("#script_button").val($("#se_2").find('option:selected').val());
                // 获取当前步骤脚本信息
                var steprunid = $("#steprunid").val();
                var scriptid = $("#se_2").find('option:selected').val();
                $.ajax({
                    url: "/get_current_scriptinfo/",
                    type: "post",
                    data: {"steprunid": steprunid, "scriptid": scriptid},
                    success: function (data) {
                        $("#code").val(data.data["code"]);
                        $("#script_ip").val(data.data["ip"]);
                        $("#script_port").val(data.data["port"]);
                        $("#filename").val(data.data["filename"]);
                        $("#scriptpath").val(data.data["scriptpath"]);
                        $("#scriptstate").val(data.data["state"]);
                        $("#ontime").val(data.data["starttime"]);
                        $("#offtime").val(data.data["endtime"]);
                        $("#operator").val(data.data["operator"]);
                        if (data.data["show_button"] == 1) {
                            $("#b1").show();
                        } else {
                            $("#b1").hide();
                        }
                    }
                });
            }
        }

    });
    $('#se_3').dblclick(function () {
        $("#b1").hide();
        if ($("#se_3").find('option:selected').length == 0) {
            alert("请至少选中一个脚本。")
        } else {
            if ($("#se_3").find('option:selected').length > 1) {
                alert("请不要选择多条记录。");
            } else {
                $("#static").modal({backdrop: "static"});
                $("#script_button").val($("#se_3").find('option:selected').val());
                // 获取当前步骤脚本信息
                var steprunid = $("#steprunid").val();
                var scriptid = $("#se_3").find('option:selected').val();
                $.ajax({
                    url: "/get_current_scriptinfo/",
                    type: "post",
                    data: {"steprunid": steprunid, "scriptid": scriptid},
                    success: function (data) {
                        $("#code").val(data.data["code"]);
                        $("#script_ip").val(data.data["ip"]);
                        $("#script_port").val(data.data["port"]);
                        $("#filename").val(data.data["filename"]);
                        $("#scriptpath").val(data.data["scriptpath"]);
                        $("#scriptstate").val(data.data["state"]);
                        $("#ontime").val(data.data["starttime"]);
                        $("#offtime").val(data.data["endtime"]);
                        $("#operator").val(data.data["operator"]);
                        if (data.data["show_button"] == 1) {
                            $("#b1").show();
                        } else {
                            $("#b1").hide();
                        }
                    }
                });
            }
        }

    });
    $('#se_4').dblclick(function () {
        $("#b1").hide();
        if ($("#se_4").find('option:selected').length == 0) {
            alert("请至少选中一个脚本。")

        } else {
            if ($("#se_4").find('option:selected').length > 1) {
                alert("请不要选择多条记录。");
            } else {
                $("#static").modal({backdrop: "static"});
                $("#script_button").val($("#se_4").find('option:selected').val());
                // 获取当前步骤脚本信息
                var steprunid = $("#steprunid").val();
                var scriptid = $("#se_4").find('option:selected').val();
                $.ajax({
                    url: "/get_current_scriptinfo/",
                    type: "post",
                    data: {"steprunid": steprunid, "scriptid": scriptid},
                    success: function (data) {
                        $("#code").val(data.data["code"]);
                        $("#script_ip").val(data.data["ip"]);
                        $("#script_port").val(data.data["port"]);
                        $("#filename").val(data.data["filename"]);
                        $("#scriptpath").val(data.data["scriptpath"]);
                        $("#scriptstate").val(data.data["state"]);
                        $("#ontime").val(data.data["starttime"]);
                        $("#offtime").val(data.data["endtime"]);
                        $("#operator").val(data.data["operator"]);
                        if (data.data["show_button"] == 1) {
                            $("#b1").show();
                        } else {
                            $("#b1").hide();
                        }
                    }
                });
            }
        }

    });
    $('#se_6').dblclick(function () {
        $("#static").modal({backdrop: "static"});
        $("#b1").hide();

        if ($("#se_6").find('option:selected').length == 0) {
            alert("请至少选中一个脚本。")

        } else {
            if ($("#se_6").find('option:selected').length > 1) {
                alert("请不要选择多条记录。");
            } else {
                $("#static").modal({backdrop: "static"});
                $("#script_button").val($("#se_6").find('option:selected').val());
                // 获取当前步骤脚本信息
                var steprunid = $("#steprunid").val();
                var scriptid = $("#se_6").find('option:selected').val();
                $.ajax({
                    url: "/get_current_scriptinfo/",
                    type: "post",
                    data: {"steprunid": steprunid, "scriptid": scriptid},
                    success: function (data) {
                        $("#code").val(data.data["code"]);
                        $("#script_ip").val(data.data["ip"]);
                        $("#script_port").val(data.data["port"]);
                        $("#filename").val(data.data["filename"]);
                        $("#scriptpath").val(data.data["scriptpath"]);
                        $("#scriptstate").val(data.data["state"]);
                        $("#ontime").val(data.data["starttime"]);
                        $("#offtime").val(data.data["endtime"]);
                        $("#operator").val(data.data["operator"]);
                        if (data.data["show_button"] == 1) {
                            $("#b1").show();
                        } else {
                            $("#b1").hide();
                        }
                    }
                });
            }
        }

    });

    // 手动执行脚本
    $("#exec").click(function () {
        var steprunid = $("#steprunid").val();
        var scriptid = $("#script_button").val();
        $.ajax({
            url: "/exec_script_by_hand/",
            type: "post",
            data: {"steprunid": steprunid, "scriptid": scriptid},
            success: function (data) {
                if (data.data["exec_tag"] == 0) {
                    alert("脚本执行成功！");
                } else {
                    alert("脚本执行失败！");
                }
            }
        });
    });

    // 跳过脚本
    $("#ignore").click(function () {
        var scriptid = $("#script_button").val();
        $.ajax({
            url: "/ignore_current_script/",
            type: "post",
            data: {"scriptid": scriptid},
            success: function (data) {
                alert(data.data);
                $('#static').modal('hide');
            }
        });
    });


    FormWizard.init();
});