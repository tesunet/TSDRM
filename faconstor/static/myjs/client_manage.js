function inArray(search, array) {
    for (var i in array) {
        if (JSON.stringify(array[i]) == JSON.stringify(search)) {
            return true;
        }
    }
    return false;
}

function displayAgentParams(agent_type) {
    if (agent_type.indexOf("Oracle") != -1) {
        $('#cv_orcl').show();
        $('#cv_filesystem').hide();
        $('#cv_mssql').hide();
        $('#cv_select_file').hide();
    } else if (agent_type.indexOf("File System") != -1) {
        $('#cv_orcl').hide();
        $('#cv_filesystem').show();
        $('#cv_mssql').hide();
        $('#cv_select_file').show();
    } else if (agent_type.indexOf("SQL Server") != -1) {
        $('#cv_orcl').hide();
        $('#cv_filesystem').hide();
        $('#cv_mssql').show();
        $('#cv_select_file').hide();
    }
}


//主机
function getClientree() {
    $.ajax({
        type: 'POST',
        dataType: 'json',
        url: '../get_client_tree/',
        data: {
            'id': $("#id").val(),
        },
        success: function (data) {
            if (data.ret == 0) {
                alert(data.data)
            }
            else {
                $('#tree_client').jstree({
                    'core': {
                        "themes": {
                            "responsive": false
                        },
                        "check_callback": true,
                        'data': data.data
                    },

                    "types": {
                        "NODE": {
                            "icon": false
                        },
                        "CLIENT": {
                            "icon": false
                        }
                    },
                    "contextmenu":$('#is_superuser').val()=="True"?{
                        "items": {
                            "create": null,
                            "rename": null,
                            "remove": null,
                            "ccp": null,
                            "新建节点": {
                                "label": "新建节点",
                                "action": function (data) {
                                    var inst = jQuery.jstree.reference(data.reference),
                                        obj = inst.get_node(data.reference);
                                    if (obj.type == "CLIENT") {
                                        alert("无法在客户端下新建节点。");
                                    } else {
                                        $("#title").text("新建");
                                        $("#id").val("0");
                                        $("#pid").val(obj.id);
                                        $("#my_type").val("NODE");
                                        $("#node_name").val("");
                                        $("#node_pname").val(obj.data["name"]);
                                        $("#node_remark").val("");

                                        $("#client").hide();
                                        $("#node").show();
                                        $("#node_save").show()
                                        $("#client_save").hide()
                                    }
                                }
                            },
                            "新建客户端": {
                                "label": "新建客户端",
                                "action": function (data) {
                                    var inst = jQuery.jstree.reference(data.reference),
                                        obj = inst.get_node(data.reference);
                                    if (obj.type == "CLIENT") {
                                        alert("无法在客户端下新建客户端。");
                                    } else {
                                        $('#tabcheck2').attr("style", "color: #cbd5dd");
                                        $("#tabcheck2").parent().attr("style", "pointer-events:none;");
                                        $("#tabcheck1").click();
                                        $("#title").text("新建")
                                        $("#pname").val(obj.data["name"])
                                        $("#id").val("0");
                                        $("#pid").val(obj.id);
                                        $("#my_type").val("CLIENT");
                                        $("#host_ip").val("");
                                        $("#host_name").val("");
                                        $("#os").val("");
                                        $("#username").val("");
                                        $("#password").val("");
                                        $("#remark").val("");
                                        $('#param_se').empty();

                                        $("#client").show()
                                        $("#node").hide()
                                        $("#node_save").hide()
                                        $("#client_save").show()
                                    }
                                }
                            },
                            "删除": {
                                "label": "删除",
                                "action": function (data) {
                                    var inst = jQuery.jstree.reference(data.reference),
                                        obj = inst.get_node(data.reference);
                                    if (obj.children.length > 0)
                                        alert("节点下还有其他节点或客户端，无法删除。");
                                    else {
                                        if (confirm("确定要删除？删除后不可恢复。")) {
                                            $.ajax({
                                                type: "POST",
                                                url: "../clientdel/",
                                                data:
                                                {
                                                    id: obj.id,
                                                },
                                                success: function (data) {
                                                    if (data == 1) {
                                                        inst.delete_node(obj);
                                                        alert("删除成功！");
                                                    } else
                                                        alert("删除失败，请于管理员联系。");
                                                },
                                                error: function (e) {
                                                    alert("删除失败，请于管理员联系。");
                                                }
                                            });
                                        }
                                    }
                                }
                            },

                        }
                    }:{"items": {
                            "create": null,
                            "rename": null,
                            "remove": null,
                            "ccp": null,
                        }},
                    "plugins": ["contextmenu", "dnd", "types", "role"]
                })
                    .on('move_node.jstree', function (e, data) {
                        var moveid = data.node.id;
                        if (data.old_parent == "#") {
                            alert("根节点禁止移动。");
                            location.reload()
                        } else {
                            if (data.parent == "#") {
                                alert("禁止新建根节点。");
                                location.reload()
                            } else {
                                $.ajax({
                                    type: "POST",
                                    url: "../client_move/",
                                    data:
                                    {
                                        id: data.node.id,
                                        parent: data.parent,
                                        old_parent: data.old_parent,
                                        position: data.position,
                                        old_position: data.old_position,
                                    },
                                    success: function (data) {
                                        if (data == "重名") {
                                            alert("目标节点下存在重名。");
                                            location.reload()
                                        } else {
                                            if (data == "客户端") {
                                                alert("不能移动至客户端下。");
                                                location.reload()
                                            } else {
                                                if (data != "0") {
                                                    if (selectid == moveid) {
                                                        var res = data.split('^')
                                                        $("#pid").val(res[1])
                                                        $("#pname").val(res[0])
                                                        $("#node_pname").val(res[0])
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    error: function (e) {
                                        alert("移动失败，请于管理员联系。");
                                        location.reload()
                                    }
                                });


                            }
                        }
                    })
                    .bind('select_node.jstree', function (event, data) {
                        $("#form_div").show();
                        var type = data.node.original.type;

                        $("#id").val(data.node.id);
                        $("#pid").val(data.node.parent);
                        $("#my_type").val(type);
                        $("#title").text(data.node.data.name);
                        $('#pname').val(data.node.data.pname);
                        if (type == "CLIENT") {
                            $('#tabcheck2').removeAttr("style", "color: #cbd5dd");
                            $("#tabcheck2").parent().removeAttr("style", "pointer-events:none;");
                            $("#tabcheck1").click();
                            $.ajax({
                                type: "POST",
                                dataType: 'json',
                                url: "../get_client_detail/",
                                data: {
                                    id: data.node.id,
                                },
                                success: function (data) {
                                    if (data.ret == 1) {
                                        //基础信息
                                        $("#host_ip").val(data.data.host_ip);
                                        $("#host_name").val(data.data.host_name);
                                        $("#os").val(data.data.os);
                                        $("#username").val(data.data.username);
                                        $("#password").val(data.data.password);
                                        $("#remark").val(data.data.remark);
                                        // 动态参数
                                        $('#param_se').empty();
                                        var variable_param_list = data.data.variable_param_list;
                                        for (var i = 0; i < variable_param_list.length; i++) {
                                            $('#param_se').append('<option value="' + variable_param_list[i].variable_name + '">' + variable_param_list[i].param_name + ':' + variable_param_list[i].variable_name + ':' + variable_param_list[i].param_value + '</option>');
                                        }

                                        //cv信息
                                        if (JSON.stringify(data.cvinfo) != '{}') {
                                            $("#tabcheck2_1").click();
                                            $("#div_creatcv").hide();
                                            $("#div_cv").show();
                                            $("#cv_del").show();
                                            $("#cv_id").val(data.cvinfo.id);
                                            $("#cvclient_type").val(data.cvinfo.type);
                                            if ($("#cvclient_type").val() == "2") {
                                                $("#sourcediv").hide();
                                            }
                                            else {
                                                $("#sourcediv").show();
                                            }
                                            $("#cvclient_utils_manage").val(data.cvinfo.utils_id);
                                            getCvClient();
                                            getCvDestination();
                                            $("#cvclient_source").val(data.cvinfo.client_id);
                                            getCvAgenttype();
                                            $("#cvclient_agentType").val(data.cvinfo.agentType);
                                            getCvInstance()
                                            $("#cvclient_instance").val(data.cvinfo.instanceName);
                                            if (data.cvinfo.destination_id == data.cvinfo.id) {
                                                $("#cvclient_destination").val('self');
                                            }
                                            else {
                                                $("#cvclient_destination").val(data.cvinfo.destination_id);
                                            }

                                            // oracle
                                            $("#cvclient_copy_priority").val(data.cvinfo.copy_priority);
                                            $("#cvclient_db_open").val(data.cvinfo.db_open);
                                            $("#cvclient_log_restore").val(data.cvinfo.log_restore);
                                            $("#cvclient_data_path").val(data.cvinfo.data_path);
                                            // File System
                                            var overWrite = data.cvinfo.overWrite;
                                            var destPath = data.cvinfo.destPath;
                                            var sourcePaths = data.cvinfo.sourcePaths;
                                            if (overWrite == "True") {
                                                $('input[name="cv_overwrite"]:last').prop("checked", true);
                                            } else {
                                                $('input[name="cv_overwrite"]:first').prop("checked", true);
                                            }

                                            if (destPath == "same") {
                                                $('input[name="cv_path"]:first').prop("checked", true);
                                            } else {
                                                $('input[name="cv_path"]:last').prop("checked", true);
                                                $('#cv_mypath').val(destPath);
                                            }

                                            $('#cv_fs_se_1').empty();
                                            for (var i = 0; i < sourcePaths.length; i++) {
                                                $('#cv_fs_se_1').append("<option value='" + sourcePaths[i] + "'>" + sourcePaths[i] + "</option>");
                                            }
                                            // 加载tree
                                            try {
                                                if ($('#cvclient_agentType').val().indexOf("File System") != -1) {
                                                    getFileTree();
                                                    if ($('#cvclient_type').val() == 2) { // 目标端
                                                        $('#cv_select_file').hide();
                                                    } else {
                                                        $('#cv_select_file').show();
                                                    }
                                                }
                                            } catch (e) { }

                                            // SQL Server
                                            var mssqlOverWrite = data.cvinfo.mssqlOverWrite;
                                            if (mssqlOverWrite == "False") {
                                                $('#cv_isoverwrite').prop("checked", false);
                                            } else {
                                                $('#cv_isoverwrite').prop("checked", true);
                                            }

                                            get_cv_detail();
                                            if ($("#cvclient_type").val() == "1" || $("#cvclient_type").val() == "3") {
                                                $("#tabcheck2_2").parent().show();
                                                $("#tabcheck2_3").parent().show();
                                                $("#tabcheck2_4").parent().show();
                                            } else {
                                                $("#tabcheck2_2").parent().hide();
                                                $("#tabcheck2_3").parent().hide();
                                                $("#tabcheck2_4").parent().hide();
                                            }

                                            // 应用类型 -> 参数展示
                                            displayAgentParams(data.cvinfo.agentType);

                                            /**
                                             * 默认时间
                                             */
                                            $('#cv_r_datetimepicker').val("");
                                            $("input[name='optionsRadios'][value='1']").prop("checked", true);
                                            $("input[name='optionsRadios'][value='2']").prop("checked", false);
                                        }
                                        else {
                                            $("#div_creatcv").show();
                                            $("#div_cv").hide();
                                            $("#cv_del").hide();
                                        }

                                    }
                                    else {
                                        $("#host_id").val("0");
                                        $("#host_ip").val("");
                                        $("#host_name").val("");
                                        $("#os").val("");
                                        $("#username").val("");
                                        $("#password").val("");
                                        $("#remark").val("");
                                        $('#param_se').empty();
                                        alert(data.info);
                                    }
                                },
                                error: function (e) {
                                    alert("页面出现错误，请于管理员联系。");
                                }
                            });
                            $("#client").show()
                            $("#node").hide()
                        }
                        if (type == "NODE") {
                            $("#node_pname").val(data.node.data.pname)
                            $("#node_name").val(data.node.data.name)
                            $("#node_remark").val(data.node.data.remark)
                            $("#client").hide()
                            $("#node").show()
                        }
                        if (data.node.id == "1" || data.node.id == "2" || data.node.id == "3") {
                            $("#node_save").hide()
                            $("#client_save").hide()
                        } else {
                            $("#node_save").show()
                            $("#client_save").show()
                        }
                    });
            }
        }
    });
}

//commvault
function get_cv_detail() {
    $.ajax({
        type: "POST",
        dataType: 'json',
        url: "../get_cv_process/",
        data:
        {
            id: $("#id").val(),
        },
        success: function (data) {
            //流程
            var processtext = ""
            for (var i = 0; i < data["process"].length; i++) {
                processtext += "<div  class='form-group'><button onclick=\"runCVProcess(" + data["process"][i].process_id + ",'1')\"  type='button' class=' btn  green'>流程:" + data["process"][i].process_name + "</button> ";
                processtext += "</div>"
            }
            $("#cv_processdiv").empty();
            $("#cv_processdiv").append(processtext);
        },
        error: function (e) {
            ;
        }
    });

    var table = $('#cv_backup_his').DataTable();
    table.ajax.url("../client_cv_get_backup_his?id=" + $('#cv_id').val()
    ).load();
    // 目标客户端
    var dest_client = $('#cvclient_destination').val();
    if (dest_client == "self") {
        dest_client = $('#cv_id').val();
    }
    var table1 = $('#cv_restore_his').DataTable();
    table1.ajax.url("../client_cv_get_restore_his?id=" + dest_client
    ).load();

    $('#cv_r_sourceClient').val($("#cvclient_source").find("option:selected").text());
    $('#cv_r_destClient').val($('#cvclient_destination').val());

    // Oracle
    $('#cv_r_copy_priority').val($('#cvclient_copy_priority').val());
    $('#cv_r_db_open').val($('#cvclient_db_open').val());
    $('#cv_r_log_restore').val($('#cvclient_log_restore').val());
    $('#cv_r_data_path').val($('#cvclient_data_path').val());

    // SQL Server
    if ($('#cv_isoverwrite').is(':checked')) {
        $('#cv_r_isoverwrite').prop("checked", true);
    } else {
        $('#cv_r_isoverwrite').prop("checked", false);
    }

    // File System
    // cv_overwrite cv_path  cv_mypath cv_fs_se_1
    // cv_r_overwrite cv_r_path cv_r_mypath cv_r_fs_se_1
    var cv_overwrite = $('input[name="cv_overwrite"]:checked').val();
    if (cv_overwrite == "TRUE") {
        $('input[name="cv_r_overwrite"]:last').prop("checked", true);
    } else {
        $('input[name="cv_r_overwrite"]:first').prop("checked", true);
    }
    var cv_path = $('input[name="cv_path"]:checked').val();
    var cv_mypath = $('#cv_mypath').val();
    if (cv_path == 1) {  // 相同文件
        $('input[name="cv_r_path"]:first').prop("checked", true);
    } else {
        $('input[name="cv_r_path"]:last').prop("checked", true);
        $('#cv_r_mypath').val(cv_mypath);
    }
    var cv_fs_se_1 = $('#cv_fs_se_1').html();
    $('#cv_r_fs_se_1').empty().append(cv_fs_se_1);
}

function getCvInstance() {
    $("#cvclient_instance").empty();
    try {
        var clientdata = JSON.parse($("#cvclient_client_info").val());
        var instancelist = [];
        for (var i = 0; i < clientdata.length; i++) {
            if (clientdata[i].clientid == $("#cvclient_source").val() && clientdata[i].agent == $("#cvclient_agentType").val()) {
                if (instancelist.indexOf(clientdata[i].instance) == -1) {
                    instancelist.push(clientdata[i].instance);
                }
            }
        }
        for (var i = 0; i < instancelist.length; i++) {
            $("#cvclient_instance").append('<option value="' + instancelist[i] + '">' + instancelist[i] + '</option>');
        }
    } catch (e){
        console.log(e)
    }

}

function getCvAgenttype() {
    $("#cvclient_agentType").empty();
    try {
        var clientdata = JSON.parse($("#cvclient_client_info").val());
        var agentlist = [];
        for (var i = 0; i < clientdata.length; i++) {
            if (clientdata[i].clientid == $("#cvclient_source").val()) {
                if (agentlist.indexOf(clientdata[i].agent) == -1) {
                    agentlist.push(clientdata[i].agent);
                }
            }
        }
        for (var i = 0; i < agentlist.length; i++) {
            $("#cvclient_agentType").append('<option value="' + agentlist[i] + '">' + agentlist[i] + '</option>');
        }
    } catch (e){
        console.log(e)
    }

    getCvInstance();
}

function getCvClient() {
    $("#cvclient_source").empty();
    var utildata = JSON.parse($("#cvclient_utils_manage_info").val());
    for (var i = 0; i < utildata.length; i++) {
        if (utildata[i].utils_manage == $("#cvclient_utils_manage").val()) {
            var clientlist = [];
            for (var j = 0; j < utildata[i].instance_list.length; j++) {
                var client = { "clientid": utildata[i].instance_list[j].clientid, "clientname": utildata[i].instance_list[j].clientname };
                if (!inArray(client, clientlist)) {
                    clientlist.push(client);
                }
            }
            for (var j = 0; j < clientlist.length; j++) {
                $("#cvclient_source").append('<option value="' + clientlist[j].clientid + '">' + clientlist[j].clientname + '</option>');
            }
            $("#cvclient_client_info").val(JSON.stringify(utildata[i].instance_list))
            break;
        }
    }
    getCvAgenttype();
}

function getCvDestination() {
    $("#cvclient_destination").empty();
    $("#cv_r_destClient").empty();

    var destinationdata = JSON.parse($("#cvclient_u_destination").val());
    for (var i = 0; i < destinationdata.length; i++) {
        if (destinationdata[i].utilid == $("#cvclient_utils_manage").val()) {
            for (var j = 0; j < destinationdata[i].destination_list.length; j++) {
                $("#cvclient_destination").append('<option value="' + destinationdata[i].destination_list[j].id + '">' + destinationdata[i].destination_list[j].name + '</option>');
                $("#cv_r_destClient").append('<option value="' + destinationdata[i].destination_list[j].id + '">' + destinationdata[i].destination_list[j].name + '</option>');
            }
            break;
        }
    }
    $("#cvclient_destination").append('<option value="self">' + "本机" + '</option>');
    $("#cv_r_destClient").append('<option value="self">' + "本机" + '</option>');
}

function getCvinfo() {
    $.ajax({
        type: 'POST',
        dataType: 'json',
        url: '../get_cvinfo/',
        success: function (data) {
            for (var i = 0; i < data.u_destination.length; i++) {
                $("#cvclient_utils_manage").append('<option value="' + data.u_destination[i].utilid + '">' + data.u_destination[i].utilname + '</option>');
            }
            $("#cvclient_utils_manage_info").val(JSON.stringify(data.data))
            $("#cvclient_u_destination").val(JSON.stringify(data.u_destination))
            getCvClient();
            getCvDestination();
            $('#loading').hide();
            $('#showdata').show();
        }
    });

}

function getFileTree() {
    var setting = {
        async: {
            enable: true,
            url: '../get_file_tree/',
            autoParam: ["id"],
            otherParam: { "cv_id": $('#cv_id').val() },
            dataFilter: filter
        },
        check: {
            enable: true,
            chkStyle: "checkbox",               //多选
            chkboxType: { "Y": "s", "N": "ps" }  //不级联父节点选择
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

    $.fn.zTree.init($("#cv_fs_tree"), setting);
}
/**
 * 流程模态框
 * @param {*} processid
 * @param {*} process_type
 */
function runCVProcess(processid, process_type) {
    /**
     * 自动化恢复流程
     */
    $("#static").modal({ backdrop: "static" });
    $('#recovery_time').datetimepicker({
        format: 'yyyy-mm-dd hh:ii:ss',
        pickerPosition: 'top-right'
    });
    // 写入当前时间
    var myDate = new Date();
    $("#run_time").val(myDate.toLocaleString());
    $("#processid").val(processid);
    $("#process_type").val(process_type);

}


function runprocess(processid, process_type) {
    $("#static").modal({ backdrop: "static" });
    $('#recovery_time').datetimepicker({
        format: 'yyyy-mm-dd hh:ii:ss',
        pickerPosition: 'top-right'
    });
    // 写入当前时间
    var myDate = new Date();
    $("#run_time").val(myDate.toLocaleString());
    $("#processid").val(processid);
    $("#process_type").val(process_type);
}



$(document).ready(function () {
    //主机
    $(".tabbed>ul>li").click(function () {
        var aa = this.firstElementChild;
        aa.click();
    });
    $('#loading').show();
    $('#showdata').hide();

    getClientree();

    $('#node_save').click(function () {
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../client_node_save/",
            data: {
                id: $("#id").val(),
                pid: $("#pid").val(),
                node_name: $("#node_name").val(),
                node_remark: $("#node_remark").val(),
            },
            success: function (data) {
                if (data.ret == 1) {
                    if ($("#id").val() == "0") {
                        $('#tree_client').jstree('create_node', $("#pid").val(), {
                            "text": "<i class='jstree-icon jstree-themeicon fa fa-folder icon-state-warning icon-lg jstree-themeicon-custom'></i>" + $("#node_name").val(),
                            "id": data.nodeid,
                            "type": "NODE",
                            "data": { "remark": $("#node_remark").val(), "name": $("#node_name").val(), "pname": $("#pname").val() },
                            "icon": false,
                        }, "last", false, false);
                        $("#id").val(data.nodeid)
                        $('#tree_client').jstree('deselect_all')
                        $('#tree_client').jstree('select_node', $("#id").val(), true)
                    }
                    else {
                        var curnode = $('#tree_client').jstree('get_node', $("#id").val());
                        var newtext = curnode.text.replace(curnode.data["name"], $("#node_name").val())
                        curnode.text = newtext
                        curnode.data["remark"] = $("#node_remark").val()
                        curnode.data["name"] = $("#node_name").val()
                        $('#tree_client').jstree('set_text', $("#id").val(), newtext);
                    }
                }
                alert(data.info);
            },
            error: function (e) {
                alert("页面出现错误，请于管理员联系。");
            }
        });
    });
    $('#client_save').click(function () {
        var params_list = [];

        // 构造参数Map>> Array (动态参数)
        $('#param_se option').each(function () {
            // 构造单个参数信息
            var txt_param_list = $(this).text().split(":");
            var val_param = $(this).prop("value");
            var param_dict = {
                "param_name": txt_param_list[0],
                "variable_name": val_param,
                "param_value": txt_param_list[2]
            };
            params_list.push(param_dict)
        });

        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../client_client_save/",
            data: {
                id: $("#id").val(),
                pid: $("#pid").val(),
                host_ip: $("#host_ip").val(),
                host_name: $("#host_name").val(),
                os: $("#os").val(),
                username: $("#username").val(),
                password: $("#password").val(),
                remark: $("#remark").val(),
                config: JSON.stringify(params_list)
            },
            success: function (data) {
                if (data.ret == 1) {
                    if ($("#id").val() == "0") {
                        $('#tree_client').jstree('create_node', $("#pid").val(), {
                            "text": $("#host_name").val(),
                            "id": data.nodeid,
                            "type": "CLIENT",
                            "data": { "remark": $("#node_remark").val(), "name": $("#node_name").val(), "pname": $("#pname").val() },
                            "icon": false,
                        }, "last", false, false);
                        $("#id").val(data.nodeid)
                        $('#tree_client').jstree('deselect_all')
                        $('#tree_client').jstree('select_node', $("#id").val(), true)
                        $('#tabcheck2').removeAttr("style", "color: #cbd5dd");
                        $("#tabcheck2").parent().removeAttr("style", "pointer-events:none;");
                    }
                    else {
                        var curnode = $('#tree_client').jstree('get_node', $("#id").val());
                        var newtext = curnode.text.replace(curnode.data["name"], $("#host_name").val())
                        curnode.text = newtext
                        curnode.data["name"] = $("#host_name").val()
                        $('#tree_client').jstree('set_text', $("#id").val(), newtext);
                    }
                    $("#title").val($("#node_name").val())
                }
                alert(data.info);
            },
            error: function (e) {
                alert("页面出现错误，请于管理员联系。");
            }
        });
    });

    $('#param_se').contextmenu({
        target: '#context-menu2',
        onItem: function (context, e) {
            if ($(e.target).text() == "新增") {
                $('#param_operate').val('new');

                // 清空所有子节点
                $('#params').empty();

                // 新增节点
                $("#params").append(
                    '<div class="form-group">' +
                    '<label class="col-md-2 control-label"><span style="color:red; "></span>参数名称</label>' +
                    '<div class="col-md-10">' +
                    '<input id="param_name" type="text" name="param_name" class="form-control" placeholder="">' +
                    '<div class="form-control-focus"></div>' +
                    '</div>' +
                    '</div>' +
                    '<div class="form-group">' +
                    '<label class="col-md-2 control-label"><span style="color:red; "></span>变量设置</label>' +
                    '<div class="col-md-10">' +
                    '<input id="variable_name" type="text" name="variable_name" class="form-control" placeholder="">' +
                    '<div class="form-control-focus"></div>' +
                    '</div>' +
                    '</div>' +
                    '<div class="form-group">' +
                    '<label class="col-md-2 control-label"><span style="color:red; "></span>参数值</label>' +
                    '<div class="col-md-10">' +
                    '<input id="param_value" type="text" name="param_value" class="form-control" placeholder="">' +
                    '<div class="form-control-focus"></div>' +
                    '</div>' +
                    '</div>'
                );

                $("button#param_edit").click();
            }
            if ($(e.target).text() == "修改") {
                $('#param_operate').val('edit');
                if ($("#param_se").find('option:selected').length == 0)
                    alert("请选择要修改的参数。");
                else {
                    if ($("#param_se").find('option:selected').length > 1)
                        alert("修改时请不要选择多条记录。");
                    else {
                        var alpha_param = $("#param_se").val();
                        var params_t = $("#param_se").find('option:selected').text();

                        var params_t_list = params_t.split(":");

                        var txt_param = params_t_list[0];
                        var v_param = params_t_list[2];

                        $("#params").empty();
                        $("#params").append(
                            '<div class="form-group">' +
                            '<label class="col-md-2 control-label"><span style="color:red; "></span>参数名称</label>' +
                            '<div class="col-md-10">' +
                            '<input id="param_name" type="text" name="param_name" value="' + txt_param + '" class="form-control" placeholder="">' +
                            '<div class="form-control-focus"></div>' +
                            '</div>' +
                            '</div>' +
                            '<div class="form-group">' +
                            '<label class="col-md-2 control-label"><span style="color:red; "></span>变量设置</label>' +
                            '<div class="col-md-10">' +
                            '<input id="variable_name" readonly type="text" name="variable_name" value="' + alpha_param + '" class="form-control" placeholder="">' +
                            '<div class="form-control-focus"></div>' +
                            '</div>' +
                            '</div>' +
                            '<div class="form-group">' +
                            '<label class="col-md-2 control-label"><span style="color:red; "></span>参数值</label>' +
                            '<div class="col-md-10">' +
                            '<input id="param_value" type="text" name="param_value" value="' + v_param + '" class="form-control" placeholder="">' +
                            '<div class="form-control-focus"></div>' +
                            '</div>' +
                            '</div>'
                        );
                        $("button#param_edit").click();
                    }
                }

            }
            if ($(e.target).text() == "删除") {
                $('#param_operate').val('delete');
                if ($("#param_se").find('option:selected').length == 0)
                    alert("请选择要删除的参数。");
                else {
                    if (confirm("确定要删除该参数吗？")) {
                        $("#param_se").find('option:selected').remove();
                    }
                }
            }
        }
    });
    $('#params_save').click(function () {
        var param_operate = $('#param_operate').val();
        var param_name = $('#param_name').val();
        var variable_name = $('#variable_name').val();
        var param_value = $('#param_value').val();

        if (param_operate == "new") {
            $('#param_se').append('<option value="' + variable_name + '">' + param_name + ':' + variable_name + ':' + param_value + '</option>');
        }
        if (param_operate == "edit") {
            // 指定value的option修改text
            $('#param_se option[value="' + variable_name + '"]').text(param_name + ':' + variable_name + ':' + param_value);
        }
        $("#static01").modal("hide");
    });

    //cv
    getCvinfo();
    $('#creatcv').click(function () {  // 创建commvault保护
        $("#div_creatcv").hide();
        $("#div_cv").show();
        $("#cv_del").hide();
        $("#tabcheck2_1").click();
        $("#tabcheck2_2").parent().hide();
        $("#tabcheck2_3").parent().hide();
        $("#tabcheck2_4").parent().hide();

        $("#cv_id").val("0");
        $("#cvclient_type").val("1");

        /**
         * 创建commvault保护时
         * 新建要清除目录
         * 新建要隐藏选择目录按钮
         * 新建要清除树
         */
        $('#cv_select_file').hide();
        try {
            $.fn.zTree.getZTreeObj("cv_fs_tree").destroy();
        } catch(e){}
        $('#cv_fs_se_1').empty();
        $('#cvclient_agentType').change();  // 主从触发更改操作
    });

    $("#cvclient_utils_manage").change(function () {
        getCvClient();
        getCvDestination();
        // 应用类型 -> 参数展示
        var cv_agent = $('#cvclient_agentType').val();
        displayAgentParams(cv_agent);
    });
    $("#cvclient_source").change(function () {
        getCvAgenttype();
        // 应用类型 -> 参数展示
        var cv_agent = $('#cvclient_agentType').val();
        displayAgentParams(cv_agent);
    });
    $("#cvclient_agentType").change(function () {
        getCvInstance();

        var cv_agent = $(this).val();
        console.log(cv_agent);
        // 应用类型 -> 参数展示
        displayAgentParams(cv_agent);
    });
    $("#cvclient_type").change(function () {
        if ($("#cvclient_type").val() == "2") {
            $("#sourcediv").hide();
        }
        else {
            $("#sourcediv").show();
        }
    });

    $('#cv_save').click(function () {
        var cv_iscover = $("input[name='cv_overwrite']:checked").val();
        var cv_mypath = "same"
        if ($("input[name='cv_path']:checked").val() == "2") {
            cv_mypath = $('#cv_mypath').val()
        }
        var cv_selectedfile = ""
        $("#cv_fs_se_1 option").each(function () {
            var txt = $(this).val();
            cv_selectedfile = cv_selectedfile + txt + "*!-!*"
        });
        var mssql_iscover = "FALSE"
        if ($('#cv_isoverwrite').is(':checked')) {
            mssql_iscover = "TRUE"
        }
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../client_cv_save/",
            data: {
                id: $("#id").val(),
                cv_id: $("#cv_id").val(),
                cvclient_type: $("#cvclient_type").val(),
                cvclient_utils_manage: $("#cvclient_utils_manage").val(),
                cvclient_source: $("#cvclient_source").val(),
                cvclient_clientname: $("#cvclient_source").find("option:selected").text(),
                cvclient_agentType: $("#cvclient_agentType").val(),
                cvclient_instance: $("#cvclient_instance").val(),
                cvclient_destination: $("#cvclient_destination").val(),

                // Oracle
                cvclient_copy_priority: $("#cvclient_copy_priority").val(),
                cvclient_db_open: $("#cvclient_db_open").val(),
                cvclient_log_restore: $("#cvclient_log_restore").val(),
                cvclient_data_path: $("#cvclient_data_path").val(),

                // File System
                cv_iscover: cv_iscover,
                cv_mypath: cv_mypath,
                cv_selectedfile: cv_selectedfile,

                // SQL Server
                mssql_iscover: mssql_iscover
            },
            success: function (data) {
                if (data.ret == 1) {
                    if ($("#cv_id").val() == "0") {
                        $("#cv_id").val(data.cv_id);
                        $("#cv_del").show();
                        if ($("#cvclient_type").val() == "1" || $("#cvclient_type").val() == "3") {
                            $("#tabcheck2_2").parent().show();
                            $("#tabcheck2_3").parent().show();
                            $("#tabcheck2_4").parent().show();
                        }
                        else {
                            $("#tabcheck2_2").parent().hide();
                            $("#tabcheck2_3").parent().hide();
                            $("#tabcheck2_4").parent().hide();
                        }
                        var curnode = $('#tree_client').jstree('get_node', $("#id").val());
                        var newtext = "<img src = '/static/pages/images/cv.png' height='24px'> " + curnode.text
                        $('#tree_client').jstree('set_text', $("#id").val(), newtext);
                    }
                    if ($("#cvclient_type").val() == "2" || $("#cvclient_type").val() == "3") {
                        var destinationdata = JSON.parse($("#cvclient_u_destination").val());
                        for (var i = 0; i < destinationdata.length; i++) {
                            if (destinationdata[i].utilid == $("#cvclient_utils_manage").val()) {
                                var cur_destination = { "name": $("#cvclient_source").find("option:selected").text(), "id": data.cv_id }
                                if (!inArray(cur_destination, destinationdata[i].destination_list)) {
                                    destinationdata[i].destination_list.push(cur_destination);
                                    $("#cvclient_u_destination").val(JSON.stringify(destinationdata));
                                    $("#cvclient_destination").append('<option value="' + data.cv_id + '">' + $("#cvclient_source").find("option:selected").text() + '</option>');
                                    $("#cv_r_destClient").append('<option value="' + data.cv_id + '">' + $("#cvclient_source").find("option:selected").text() + '</option>');
                                }
                                break;
                            }
                        }
                    }
                    get_cv_detail();
                    // 加载tree
                    try {
                        if ($('#cvclient_agentType').val().indexOf("File System") != -1) {
                            getFileTree();
                            if ($('#cvclient_type').val() == 2) { // 目标端
                                $('#cv_select_file').hide();
                            } else {
                                $('#cv_select_file').show();
                            }
                        }
                    } catch (e) { }
                }
                alert(data.info);
            },
            error: function (e) {
                alert("页面出现错误，请于管理员联系。");
            }
        });
    });
    $('#cv_del').click(function () {
        if (confirm("确定要删除？删除后不可恢复。")) {
            $.ajax({
                type: "POST",
                url: "../client_cv_del/",
                data:
                {
                    id: $("#cv_id").val(),
                },
                success: function (data) {
                    if (data == 1) {
                        $("#div_creatcv").show();
                        $("#div_cv").hide();
                        $("#cv_del").hide();
                        var curnode = $('#tree_client').jstree('get_node', $("#id").val());
                        var newtext = curnode.text.replace("<img src = '/static/pages/images/cv.png' height='24px'> ", "")
                        $('#tree_client').jstree('set_text', $("#id").val(), newtext);

                        if ($("#cvclient_type").val() == "2" || $("#cvclient_type").val() == "3") {
                            var destinationdata = JSON.parse($("#cvclient_u_destination").val());
                            for (var i = 0; i < destinationdata.length; i++) {
                                if (destinationdata[i].utilid == $("#cvclient_utils_manage").val()) {
                                    for (var j = 0; j < destinationdata[i].destination_list.length; j++) {
                                        if (destinationdata[i].destination_list[j].id == $("#cv_id").val()) {
                                            destinationdata[i].destination_list.splice(j, 1)
                                            $("#cvclient_u_destination").val(JSON.stringify(destinationdata));

                                            break;
                                        }
                                    }
                                    $("#cvclient_destination option[value='" + $("#cv_id").val() + "']").remove();
                                    $("#cv_r_destClient option[value='" + $("#cv_id").val() + "']").remove();
                                    break;
                                }
                            }

                        }
                        alert("删除成功！");
                    } else
                        alert("删除失败，请于管理员联系。");
                },
                error: function (e) {
                    alert("删除失败，请于管理员联系。");
                }
            });
        }
    })

    $('#cv_backup_his').dataTable({
        "bAutoWidth": true,
        "bProcessing": true,
        "bSort": false,
        "destroy": true,
        //"ajax": "../../oraclerecoverydata?origin_id=" + origin_id,
        "columns": [
            { "data": "jobId" },
            { "data": "jobType" },
            { "data": "Level" },
            { "data": "StartTime" },
            { "data": "LastTime" },
            { "data": null },
        ],
        "columnDefs": [{
            "targets": -1,
            "data": null,
            "defaultContent": "<button  id='select' title='选择'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-check'></i></button>"
        }],

        "oLanguage": {
            "sLengthMenu": "&nbsp;&nbsp;每页显示 _MENU_ 条记录",
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
    $('#cv_backup_his tbody').on('click', 'button#select', function () {
        $('#tabcheck2_3').click();
        var table = $('#cv_backup_his').DataTable();
        var data = table.row($(this).parents('tr')).data();
        var pre_last_time = "";
        try {
            pre_last_time = table.row($(this).parents('tr').next()).data().LastTime;
        } catch (e) {
            //..
        }
        $('#cv_r_pre_restore_time').val(pre_last_time);
        $("#cv_r_datetimepicker").val(data.LastTime);
        $("input[name='optionsRadios'][value='1']").prop("checked", false);
        $("input[name='optionsRadios'][value='2']").prop("checked", true);
        $("#cv_r_browseJobId").val(data.jobId);
        $("#cv_r_data_sp").val(data.data_sp);
    });

    $('#cv_restore_his').dataTable({
        "bAutoWidth": true,
        "bProcessing": true,
        "bSort": false,
        "destroy": true,
        //"ajax": "../../oraclerecoverydata?origin_id=" + origin_id,
        "columns": [
            { "data": "jobid" },
            { "data": "jobType" },
            { "data": "starttime" },
            { "data": "endtime" },
            { "data": "jobstatus" }
        ],

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
    $('#cv_r_datetimepicker').datetimepicker({
        format: 'yyyy-mm-dd hh:ii:ss',
        pickerPosition: 'top-right'
    });

    $('#cv_r_recovery').click(function () {
        if ($("input[name='optionsRadios']:checked").val() == "2" && $('#cv_r_datetimepicker').val() == "")
            alert("请输入时间。");
        else {
            if ($('#cv_r_destClient').val() == "")
                alert("请选择目标客户端。");
            else {
                if (confirm('是否确定启动自主恢复？')){
                    var myrestoreTime = "";
                    if ($("input[name='optionsRadios']:checked").val() == "2" && $('#cv_r_datetimepicker').val() != "") {
                        myrestoreTime = $('#cv_r_datetimepicker').val();
                    }
                    var destClient = $('#cv_r_destClient option:selected').text().trim();
                    if ($('#cv_r_destClient').val() == "self") {
                        destClient = $('#cv_r_sourceClient').val()
                    }

                    // 区分应用
                    var agent = $("#cvclient_agentType").val();
                    if (agent.indexOf("Oracle") != -1) {
                        $.ajax({
                            type: "POST",
                            url: "../../client_cv_recovery/",
                            data: {
                                cv_id: $('#cv_id').val(),
                                sourceClient: $('#cv_r_sourceClient').val(),
                                destClient: destClient,
                                restoreTime: myrestoreTime,
                                browseJobId: $("#cv_r_browseJobId").val(),
                                // 判断是oracle还是oracle rac
                                agent: agent,
                                data_path: $("#cv_r_data_path").val(),
                                copy_priority: $("#cv_r_copy_priority").val(),
                                data_sp: $("#cv_r_data_sp").val(),
                            },
                            success: function (data) {
                                alert(data);
                                var table1 = $('#cv_restore_his').DataTable();
                                table1.ajax.reload();
                            },
                            error: function (e) {
                                alert("恢复失败，请于客服联系。");
                            }
                        });
                    } else if (agent.indexOf('File System') != -1) {
                        if ($("input[name='cv_r_path']:checked").val() == "2" && $('#cv_r_mypath').val() == "")
                            alert("请输入指定路径。");
                        else {
                            var iscover = $("input[name='cv_r_overwrite']:checked").val();
                            var mypath = "same"
                            if ($("input[name='cv_r_path']:checked").val() == "2")
                                mypath = $('#cv_r_mypath').val()
                            var selectedfile = ""
                            $("#cv_r_fs_se_1 option").each(function () {
                                var txt = $(this).val();
                                selectedfile = selectedfile + txt + "*!-!*"
                            });
                            $.ajax({
                                type: "POST",
                                url: "../../client_cv_recovery/",
                                data: {
                                    cv_id: $('#cv_id').val(),
                                    sourceClient: $('#cv_r_sourceClient').val(),
                                    destClient: destClient,
                                    restoreTime: myrestoreTime,
                                    browseJobId: $("#cv_r_browseJobId").val(),
                                    agent: agent,

                                    iscover: iscover,
                                    mypath: mypath,
                                    selectedfile: selectedfile,
                                },
                                success: function (data) {
                                    alert(data);
                                    var table1 = $('#cv_restore_his').DataTable();
                                    table1.ajax.reload();
                                },
                                error: function (e) {
                                    alert("恢复失败，请于客服联系。");
                                }
                            });
                        }
                    } else if (agent.indexOf('SQL Server') != -1) {
                        var mssql_iscover = "FALSE"
                        if ($('#cv_r_isoverwrite').is(':checked')) {
                            mssql_iscover = "TRUE"
                        }
                        $.ajax({
                            type: "POST",
                            url: "../../client_cv_recovery/",
                            data: {
                                cv_id: $('#cv_id').val(),
                                sourceClient: $('#cv_r_sourceClient').val(),
                                destClient: destClient,
                                restoreTime: myrestoreTime,
                                browseJobId: $("#cv_r_browseJobId").val(),
                                agent: agent,

                                mssql_iscover: mssql_iscover,
                            },
                            success: function (data) {
                                alert(data);
                                var table1 = $('#cv_restore_his').DataTable();
                                table1.ajax.reload();
                            },
                            error: function (e) {
                                alert("恢复失败，请于客服联系。");
                            }
                        });
                    }
                }
            }
        }
    });

    /*
        自主恢复
            参数
    */
    $('#navtabs2 a').on("click", function () {
        var a_id = $(this).prop('id');
        if (a_id == 'tabcheck2_3') {
            var agent_type = $('#cvclient_agentType').val();
            if (agent_type.indexOf("Oracle") != -1) {
                $('#cv_r_orcl').show();
                $('#cv_r_mssql').hide();
                $('#cv_r_filesystem').hide();
            } else if (agent_type.indexOf("SQL Server") != -1) {
                $('#cv_r_mssql').show();
                $('#cv_r_orcl').hide();
                $('#cv_r_filesystem').hide();
            } else if (agent_type.indexOf("File System") != -1) {
                $('#cv_r_mssql').hide();
                $('#cv_r_orcl').hide();
                $('#cv_r_filesystem').show();
            } else {
                $('#cv_r_mssql').hide();
                $('#cv_r_orcl').hide();
                $('#cv_r_filesystem').hide();
            }
        }
    });

    $('#cv_selectpath').click(function () {
        $('#cv_fs_se_1').empty();
        var cv_fs_tree = $.fn.zTree.getZTreeObj("cv_fs_tree");
        var nodes = cv_fs_tree.getCheckedNodes(true);
        for (var k = 0, length = nodes.length; k < length; k++) {
            var halfCheck = nodes[k].getCheckStatus();
            if (!halfCheck.half) {
                $("#cv_fs_se_1").append("<option value='" + nodes[k].id + "'>" + nodes[k].id + "</option>");
            }
        }
        if (nodes.length == 0)
            $("#cv_fs_se_1").append("<option value=''></option>");
    })


});
/**
 * 启动流程
 */
$("#confirm").click(function () {
    if($("#confirmtext")!="确认启动流程") {
        alert("请在文本框内输入\"确认启动流程\"");
    }
    else{
        var process_id = $("#processid").val();
        // File System
        var iscover = $("input[name='cv_r_overwrite']:checked").val();
        var mypath = "same"
        if ($("input[name='cv_r_path']:checked").val() == "2") {
            mypath = $('#cv_r_mypath').val()
        }
        var selectedfile = "";
        $("#cv_r_fs_se_1 option").each(function () {
            var txt = $(this).val();
            selectedfile = selectedfile + txt + "*!-!*"
        });
        // SQL Server
        var mssql_iscover = "FALSE"
        if ($('#cv_r_isoverwrite').is(':checked')) {
            mssql_iscover = "TRUE"
        }
        // 目标端
        var std = $('#cv_r_destClient').val();
        if (std == "self") {
            std = $("#cv_id").val();
        }
        // 非邀请流程启动
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../cv_oracle_run/",
            data:
                {
                    processid: process_id,
                    run_person: $("#run_person").val(),
                    run_time: $("#run_time").val(),
                    run_reason: $("#run_reason").val(),

                    pri: $("#cv_id").val(),
                    std: std,
                    agent_type: $("#cvclient_agentType").val(),
                    recovery_time: $("#cv_r_datetimepicker").val(),
                    browseJobId: $("#cv_r_browseJobId").val(),

                    data_path: $("#cv_r_data_path").val(),
                    copy_priority: $("#cv_r_copy_priority").val(),
                    db_open: $("#cv_r_db_open").val(),
                    log_restore: $("#cv_r_log_restore").val(),

                    // SQL Server
                    mssql_iscover: mssql_iscover,

                    // File System
                    iscover: iscover,
                    mypath: mypath,
                    selectedfile: selectedfile,
                },
            success: function (data) {
                if (data["res"] == "新增成功。") {
                    alert("流程启动成功。");
                    $("#static").modal("hide");
                    window.open(data["data"], "_blank");
                } else
                    alert(data["res"]);
            },
            error: function (e) {
                alert("流程启动失败，请于管理员联系。");
            }
        });
    }
});

