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

function selectAssociatedHost() {
    /**
     * 注册选中事件
     */
    $('select[id^="hosts_manage_"]').change(function () {
        // $('#host_div').show();
        var ribbon_id = $(this).prop("id").split("_").pop(),
            hosts_name = $(this).find('option:selected').text(),
            hosts_manage_id = $(this).val();
        $('#host_param_ribbon_' + ribbon_id).prev().text(hosts_name);
        $('#host_param_ribbon_' + ribbon_id).parent().prop('h_id', hosts_manage_id);  // 主机ID

        // 主机参数
        var hosts_manage_list = [],
            hosts_manage_id = $('#hosts_manage_' + ribbon_id).val();
        try {
            hosts_manage_list = JSON.parse($('#hosts_manage_list').val());
        } catch (e) {
        }
        $('#host_param_ribbon_' + ribbon_id).empty();
        for (var i = 0; i < hosts_manage_list.length; i++) {
            if (hosts_manage_id == hosts_manage_list[i]["id"]) {
                var host_param_list = hosts_manage_list[i]['host_param_list'];
                var host_param_html = '';
                for (var i = 0; i < host_param_list.length; i++) {
                    var params = host_param_list[i];
                    var pre_group_div = '',
                        aft_group_div = '';
                    if (i % 2 == 0) {  // 奇数(i+1)
                        pre_group_div = '<div class="form-group">\n';
                    } else {
                        aft_group_div = '</div>';
                    }
                    if (i == host_param_list.length - 1) {
                        aft_group_div = '</div>';
                    }
                    host_param_html += pre_group_div +
                        '    <label class="col-md-2 control-label" style="padding-left: 0;">' + params.param_name + '</label>\n' +
                        '    <div class="col-md-4">\n' +
                        '        <input id="' + params.variable_name + '" type="text" name="' + params.variable_name + '" class="form-control"\n' +
                        '               value="' + params.param_value + '"\n' +
                        '               >\n' +
                        '        <div class="form-control-focus"></div>\n' +
                        '    </div>\n' +
                        aft_group_div;
                }
                $('#host_param_ribbon_' + ribbon_id).append(host_param_html);
                break;
            }
        }
    });
}

/**
 * 流程实例表
 *  empty 新增时的空列表
 */
function getProcessInstancedata(host_id, empty = false) {
    if ($.fn.DataTable.isDataTable('#pro_config')) {
        $('#pro_config').dataTable().fnDestroy();
    }
    $('#pro_config').dataTable({
        "destory": true,
        "bAutoWidth": true,
        "bSort": true,
        "bProcessing": true,
        "ajax": "../get_pro_data/?host_id=" + host_id + "&empty=" + empty,
        "columns": [
            {"data": "id"},
            {"data": "name"},
            {"data": "process_name"},
            {"data": "associated_name"},
            {"data": null}
        ],
        "columnDefs": [{
            "targets": -1,
            "data": null,
            "width": "100px",
            "render": function (data, type, full) {
                return "<button  id='edit' title='编辑' data-toggle='modal' data-target='#static07' class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button>" +
                    "<button title='删除'  id='delrow' class='btn btn-xs btn-primary' type='button'><i class='fa fa-trash-o'></i></button>" +
                    "<button  id='setup' title='启动' data-toggle='modal' data-target='#static10' class='btn btn-xs btn-primary' type='button'><i class='fa fa-power-off'></i></button>";
            },
        }],
        "oLanguage": {
            "sLengthMenu": "每页显示 _MENU_ 条记录",
            "sInfo": "从 _START_ 到 _END_ /共 _TOTAL_ 条数据",
            "sInfoEmpty": "没有数据",
            "sInfoFiltered": "(从 _MAX_ 条数据中检索)",
            "sSearch": "搜索",
            "oPaginate": {
                "sFirst": "首页",
                "sPrevious": "前一页",
                "sNext": "后一页",
                "sLast": "尾页"
            },
            "sZeroRecords": "没有检索到数据",
        },
    });
    $('#pro_config tbody').on('click', 'button#delrow', function () {
        if (confirm("确定要删除该条数据？")) {
            var table = $('#pro_config').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $.ajax({
                type: "POST",
                url: "../pro_del/",
                data: {
                    pro_ins_id: data.id,
                },
                success: function (data) {
                    var status = data.status,
                        info = data.info;
                    if (status == 1) {
                        table.ajax.reload();
                    }
                    alert(info);
                },
                error: function (e) {
                    alert("删除失败，请于管理员联系。");
                }
            });

        }
    });
    $('#pro_config tbody').on('click', 'button#edit', function () {
        $('#pro_schedule').show();
        var table = $('#pro_config').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $('#p_id').val(data.id);
        $('#pro_ins').val(data.name);
        $('#pros').val(data.process_id);

        /**
         * 加载关联主机
         * 主机参数
         */
        var HOST = data.config.HOST,
            PROCESS = data.config.PROCESS,
            process_name = data.process_name;

        $('#associated_host_div').empty();
        $('#host_param_div').empty();
        // if (HOST.length > 0) {
        //     $('#host_div').show();
        // } else {
        //     $('#host_div').hide();
        // }
        for (var i = 0; i < HOST.length; i++) {
            var cur_host = HOST[i];
            // 关联主机
            //      供选主机的所有选项 以及选中selected选项
            var host_options_html = "";
            var hosts_manage_list = $('#hosts_manage_list').val();
            try {
                hosts_manage_list = JSON.parse(hosts_manage_list);
            } catch (e) {
                hosts_manage_list = [];
            }
            for (var M = 0; M < hosts_manage_list.length; M++) {
                if (cur_host['host_id'] == hosts_manage_list[M]['id']) {
                    host_options_html += '<option value="' + hosts_manage_list[M]['id'] + '" selected>' + hosts_manage_list[M]['host_name'] + '</option>';
                } else {
                    host_options_html += '<option value="' + hosts_manage_list[M]['id'] + '">' + hosts_manage_list[M]['host_name'] + '</option>';
                }
            }

            $('#associated_host_div').append(
                '<div class="form-group">' +
                '<label class="col-md-2 control-label">关联主机' + (i + 1) + '</label>\n' +
                '<div class="col-md-4">\n' +
                '    <input type="text" id="associated_host_id_' + (i + 1) + '" name="associated_host_id_' + (i + 1) + '" value="' + cur_host['host_uuid'] + '" hidden>\n' +
                '    <input type="text" id="associated_host_' + (i + 1) + '" name="associated_host_' + (i + 1) + '" class="form-control" value="' + cur_host['host_given_name'] + '" readonly>\n' +
                '    <div class="form-control-focus"></div>\n' +
                '</div>\n' +
                '<div class="col-md-2 control-label" style="text-align: center; color: #00B83F">\n' +
                '    <span><i class="fa fa-link fa-lg"></i></span>\n' +
                '</div>\n' +
                '<div class="col-md-4">\n' +
                '    <select name="hosts_manage_' + (i + 1) + '" id="hosts_manage_' + (i + 1) + '" class="form-control">\n' + host_options_html +
                '    </select>\n' +
                '    <div class="form-control-focus"></div>\n' +
                '</div>' +
                '</div>'
            );

            // 主机参数inner
            var host_params = cur_host['params'];
            var host_param_html = '';
            for (var j = 0; j < host_params.length; j++) {
                var params = host_params[j];
                var pre_group_div = '',
                    aft_group_div = '';
                if (j % 2 == 0) {  // 奇数(i+1)
                    pre_group_div = '<div class="form-group">\n';
                } else {
                    aft_group_div = '</div>';
                }
                if (j == params.length - 1) {
                    aft_group_div = '</div>';
                }
                host_param_html += pre_group_div +
                    '    <label class="col-md-2 control-label" style="padding-left: 0;">' + params.param_name + '</label>\n' +
                    '    <div class="col-md-4">\n' +
                    '        <input id="' + params.variable_name + '" type="text" name="' + params.variable_name + '" class="form-control"\n' +
                    '               value="' + params.param_value + '"\n' +
                    '               >\n' +
                    '        <div class="form-control-focus"></div>\n' +
                    '    </div>\n' +
                    aft_group_div;
            }

            // 主机参数wrapper
            $('#host_param_div').append('<div class="mt-element-ribbon bg-grey-steel" h_id="" style="margin:0">\n' +
                '    <div class="ribbon ribbon-border-hor ribbon-clip ribbon-color-primary">\n' +
                '        <div class="ribbon-sub ribbon-clip"></div>\n' +
                cur_host.host_name +
                '    </div>\n' +
                '    <div class="ribbon-content" id="host_param_ribbon_' + (i + 1) + '">\n' + host_param_html +
                '    </div>\n' +
                '</div>');
            $('#host_param_ribbon_' + (i + 1)).parent().prop('h_id', cur_host["host_id"]);  // 参数中匹配主机关系的依据
        }

        selectAssociatedHost();  // 注册选中事件
        $('select[id^="hosts_manage_"]').prop('disabled', true);
        /**
         * 加载流程参数
         */
        $('#pro_param_ribbon').empty();

        if (PROCESS.length > 0) {
            $('#process_div').show();

            var process_param_list = PROCESS[0]['params']
            var pro_param_html = '';
            for (var k = 0; k < process_param_list.length; k++) {
                var param = process_param_list[k];
                var pre_group_div = '',
                    aft_group_div = '';
                if (k % 2 == 0) {  // 奇数(i+1)
                    pre_group_div = '<div class="form-group">\n';
                } else {
                    aft_group_div = '</div>';
                }
                if (k == process_param_list.length - 1) {
                    aft_group_div = '</div>';
                }
                pro_param_html += pre_group_div +
                    '    <label class="col-md-2 control-label" style="padding-left: 0;">' + param.param_name + '</label>\n' +
                    '    <div class="col-md-4">\n' +
                    '        <input id="' + param.variable_name + '" type="text" name="' + param.variable_name + '" class="form-control"\n' +
                    '               value="' + param.param_value + '"\n' +
                    '               >\n' +
                    '        <div class="form-control-focus"></div>\n' +
                    '    </div>\n' +
                    aft_group_div;
            }
            $('#pro_param_ribbon').append(pro_param_html);
            // 流程名称
            $('#process_param_div .ribbon').text(process_name);
        } else {
            $('#process_div').hide();
        }

        /**
         * 如果当前流程实例已经配置成功，加载Commvault主机携带的参数
         */
        $('#cv_info').val('');
        $.ajax({
            type: 'POST',
            dataType: 'JSON',
            url: '../get_cv_params/',
            data: {
                'pro_ins_id': $('#p_id').val(),
            },
            success: function (data) {
                var cv_info = data.data;

                try {
                    cv_info = JSON.stringify(cv_info)
                } catch (e) {
                }

                $('#cv_info').val(cv_info);
            }
        });


    });
    $('#pro_config tbody').on('click', 'button#setup', function () {
        var table = $('#pro_config').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $("#qd_std").val('');
        $("#run_reason").val("");
        $("#qd_recovery_time").val("");
        $('#pro_ins_id').val(data.id);
        // 写入当前时间
        var myDate = new Date();
        $("#run_time").val(myDate.toLocaleString());
        $("input[name='qd_cv_recovery_time_redio_group'][value='1']").prop("checked", true);
        $("input[name='qd_cv_recovery_time_redio_group'][value='2']").prop("checked", false);

        /**
         * 如果当前流程实例已经配置成功，加载Commvault主机携带的参数
         */
        $.ajax({
            type: 'POST',
            dataType: 'JSON',
            url: '../get_cv_params/',
            data: {
                'pro_ins_id': data.id,
            },
            success: function (data) {
                var cv_info = data.data;

                /**
                 * Commavult
                 */
                var cv_params = cv_info.cv_params,
                    agent_type = cv_info.agent_type,
                    is_commvault = cv_info.is_commvault;
                if (is_commvault) {
                    $('#qd_pri_id').val(cv_params.pri_id);
                    $('#qd_pri').val(cv_params.pri_name);
                    $('#qd_std').val(cv_params.std_id);

                    $('#qd_commvault_div').show();
                } else {
                    $('#qd_commvault_div').hide();
                }
                displayQDAgentParams(cv_params, agent_type, is_commvault);
            }
        });
    });
}

function initClient() {
    $('#cv_id').val('0');

    $("#host_ip").val("");
    $("#host_name").val("");
    $("#os").val("");
    $("#username").val("");
    $("#password").val("");
    $("#remark").val("");
    $('#param_se').empty();
    /**
     * Commvault配置、自主恢复字段初始化，参数初始化
     */
    $('#cvclient_type').val('');
    $('#cvclient_utils_manage').val('');
    $('#cvclient_source').val('');
    $('#cvclient_agentType').val('');
    $('#cvclient_instance').val('');
    $('#cvclient_destination').val('');

    $('#cv_orcl').hide();
    $('#cv_filesystem').hide();
    $('#cv_mssql').hide();

    $('#cv_r_orcl').hide();
    $('#cv_r_mssql').hide();
    $('#cv_r_filesystem').hide();

    $('#cv_r_sourceClient').val('');
    $('#cv_r_destClient').val('');

    // ORACLE
    $('#cvclient_copy_priority').val(1);  // 默认主拷贝
    $('#cvclient_db_open').val(1);  // 默认开启数据库
    $('#cvclient_log_restore').val(1);  // 默认回滚日志
    $('#cvclient_data_path').val('');

    $('#cv_r_copy_priority').val(1);
    $('#cv_r_db_open').val(1);
    $('#cv_r_log_restore').val(1);
    $('#cv_r_data_path').val('');

    // FILE SYSTEM
    $('input[name="cv_overwrite"]:first').prop("checked", true);  // 默认有介质较新改写
    $('input[name="cv_path"]:first').prop("checked", true);  // 默认恢复到相同路径
    $('#cv_mypath').val('');
    $('#cv_fs_se_1').empty();

    $('input[name="cv_r_overwrite"]:first').prop("checked", true);
    $('input[name="cv_r_path"]:first').prop("checked", true);
    $('#cv_r_mypath').val('');
    $('#cv_r_fs_se_1').empty();

    // MSSQL
    $('#cv_isoverwrite').prop("checked", true);  // 默认无条件改写
    $('#cv_r_isoverwrite').prop("checked", true);

    /**
     * 节点/客户端DIV区分展示
     */
    $("#client").show();
    $("#node").hide();
    $("#node_save").hide();
    $("#client_save").show();

    /**
     * 初始化备份历史、恢复历史、流程实例
     */
    $('#cv_backup_his').dataTable().fnClearTable();
    $('#cv_restore_his').dataTable().fnClearTable();
    $('#pro_config').dataTable().fnClearTable();
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
            } else {
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
                    "contextmenu": $('#is_superuser').val() == "True" ? {
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
                                        $("#tabcheck1").click();
                                        /**
                                         * 基础信息字段初始化
                                         */
                                        $("#title").text("新建")
                                        $("#pname").val(obj.data["name"])
                                        $("#id").val("0");
                                        $("#pid").val(obj.id);
                                        $("#my_type").val("CLIENT");
                                        initClient();
                                        getProcessInstancedata('', empty = true);
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
                    } : {
                        "items": {
                            "create": null,
                            "rename": null,
                            "remove": null,
                            "ccp": null,
                        }
                    },
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
                        initClient();  // 初始化各个tab的信息
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
                                            $("#cv_del").show();
                                            $("#cv_id").val(data.cvinfo.id);
                                            $("#cvclient_type").val(data.cvinfo.type);
                                            if ($("#cvclient_type").val() == "2") {
                                                $("#sourcediv").hide();
                                            } else {
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
                                            } else {
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
                                                    getFileTree($('#cv_id').val());
                                                    if ($('#cvclient_type').val() == 2) { // 目标端
                                                        $('#cv_select_file').hide();
                                                    } else {
                                                        $('#cv_select_file').show();
                                                    }
                                                }
                                            } catch (e) {
                                            }

                                            // SQL Server
                                            var mssqlOverWrite = data.cvinfo.mssqlOverWrite;
                                            if (mssqlOverWrite == "False") {
                                                $('#cv_isoverwrite').prop("checked", false);
                                            } else {
                                                $('#cv_isoverwrite').prop("checked", true);
                                            }

                                            get_cv_detail();

                                            // 应用类型 -> 参数展示
                                            displayAgentParams(data.cvinfo.agentType);

                                            /**
                                             * 默认时间
                                             */
                                            $('#cv_r_datetimepicker').val("");
                                            $("input[name='optionsRadios'][value='1']").prop("checked", true);
                                            $("input[name='optionsRadios'][value='2']").prop("checked", false);
                                        } else {
                                            $("#cv_del").hide();
                                        }
                                    } else {
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
                            $("#client").show();
                            $("#node").hide();

                            /**
                             * 流程实例
                             */
                            getProcessInstancedata(data.node.id);
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
    var table = $('#cv_backup_his').DataTable();
    table.ajax.url("../client_cv_get_backup_his?id=" + $('#cv_id').val()
    ).load();
    // // 目标客户端
    // var dest_client = $('#cvclient_destination').val();
    // if (dest_client == "self") {
    //     dest_client = $('#cv_id').val();
    // }
    // 主机ID
    var table1 = $('#cv_restore_his').DataTable();
    table1.ajax.url("../client_cv_get_restore_his?host_id=" + $('#id').val()).load();

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
    } catch (e) {
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
    } catch (e) {
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
                var client = {"clientid": utildata[i].instance_list[j].clientid, "clientname": utildata[i].instance_list[j].clientname};
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

function getFileTree(cv_id) {
    var setting = {
        async: {
            enable: true,
            url: '../get_file_tree/',
            autoParam: ["id"],
            otherParam: {"cv_id": cv_id},
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

    $.fn.zTree.init($("#cv_fs_tree"), setting);
}

function getJHFileTree(cv_id) {
    var setting = {
        async: {
            enable: true,
            url: '../get_file_tree/',
            autoParam: ["id"],
            otherParam: {"cv_id": cv_id},
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

    $.fn.zTree.init($("#jh_cv_fs_tree"), setting);
}

function displayJHAgentParams(cv_params, agent_type) {
    /**
     * 应用参数
     */
    var recovery_time = cv_params.recovery_time;

    if (recovery_time) {
        $("input[name='jh_optionsRadios'][value='2']").prop("checked", true);
        $('#jh_recovery_time').val(recovery_time);
    } else {
        $("input[name='jh_optionsRadios'][value='1']").prop("checked", true);
        $('#jh_recovery_time').val("");
    }
    $('#jh_agent_type').val(agent_type);

    if (agent_type.indexOf("Oracle") != -1) {
        $('#jh_cv_copy_priority').val(cv_params.copy_priority);
        $('#jh_cv_db_open').val(cv_params.db_open);
        $('#jh_cv_log_restore').val(cv_params.log_restore);
        $('#jh_cv_data_path').val(cv_params.data_path);

        $('#jh_cv_orcl').show();
        $('#jh_cv_mssql').hide();
        $('#jh_cv_filesystem').hide();
        $('#jh_cv_select_file').hide();
    } else if (agent_type.indexOf("File System") != -1) {
        var overWrite = cv_params.overWrite,
            destPath = cv_params.destPath,
            sourcePaths = cv_params.sourcePaths;
        if (overWrite == "True") {
            $('input[name="jh_cv_overwrite"]:last').prop("checked", true);
        } else {
            $('input[name="jh_cv_overwrite"]:first').prop("checked", true);
        }

        if (destPath == "same") {
            $('input[name="jh_cv_path"]:first').prop("checked", true);
        } else {
            $('input[name="jh_cv_path"]:last').prop("checked", true);
            $('#jh_cv_mypath').val(destPath);
        }

        $('#jh_cv_fs_se_1').empty();
        for (var i = 0; i < sourcePaths.length; i++) {
            $('#jh_cv_fs_se_1').append("<option value='" + sourcePaths[i] + "'>" + sourcePaths[i] + "</option>");
        }
        // 加载tree
        try {
            if (agent_type.indexOf("File System") != -1) {
                getJHFileTree($('#jh_pri_id').val());
                if ($('#jh_cvclient_type').val() == 2) { // 目标端
                    $('#jh_cv_select_file').hide();
                } else {
                    $('#jh_cv_select_file').show();
                }
            }
        } catch (e) {
        }

        $('#jh_cv_orcl').hide();
        $('#jh_cv_mssql').hide();
        $('#jh_cv_filesystem').show();
        $('#jh_cv_select_file').show();
    } else if (agent_type.indexOf("SQL Server") != -1) {
        var mssqlOverWrite = cv_params.mssqlOverWrite;
        if (mssqlOverWrite == "False") {
            $('#jh_cv_isoverwrite').prop("checked", false);
        } else {
            $('#jh_cv_isoverwrite').prop("checked", true);
        }

        $('#jh_cv_orcl').hide();
        $('#jh_cv_mssql').show();
        $('#jh_cv_filesystem').hide();
        $('#jh_cv_select_file').hide();
    } else {
        $('#jh_cv_orcl').hide();
        $('#jh_cv_mssql').hide();
        $('#jh_cv_filesystem').hide();
        $('#jh_cv_select_file').hide();
    }
}

function displayQDAgentParams(cv_params, agent_type) {
    /**
     * 应用参数
     */
    var recovery_time = cv_params.recovery_time;

    if (recovery_time) {
        $("input[name='qd_optionsRadios'][value='2']").prop("checked", true);
        $('#qd_recovery_time').val(recovery_time);
    } else {
        $("input[name='qd_optionsRadios'][value='1']").prop("checked", true);
        $('#qd_recovery_time').val("");
    }
    $('#qd_agent_type').val(agent_type);

    if (agent_type.indexOf("Oracle") != -1) {
        $('#qd_cv_copy_priority').val(cv_params.copy_priority);
        $('#qd_cv_db_open').val(cv_params.db_open);
        $('#qd_cv_log_restore').val(cv_params.log_restore);
        $('#qd_cv_data_path').val(cv_params.data_path);

        $('#qd_cv_orcl').show();
        $('#qd_cv_mssql').hide();
        $('#qd_cv_filesystem').hide();
        $('#qd_cv_select_file').hide();
    } else if (agent_type.indexOf("File System") != -1) {
        var overWrite = cv_params.overWrite,
            destPath = cv_params.destPath,
            sourcePaths = cv_params.sourcePaths;
        if (overWrite == "True") {
            $('input[name="qd_cv_overwrite"]:last').prop("checked", true);
        } else {
            $('input[name="qd_cv_overwrite"]:first').prop("checked", true);
        }

        if (destPath == "same") {
            $('input[name="qd_cv_path"]:first').prop("checked", true);
        } else {
            $('input[name="qd_cv_path"]:last').prop("checked", true);
            $('#qd_cv_mypath').val(destPath);
        }

        $('#qd_cv_fs_se_1').empty();
        for (var i = 0; i < sourcePaths.length; i++) {
            $('#qd_cv_fs_se_1').append("<option value='" + sourcePaths[i] + "'>" + sourcePaths[i] + "</option>");
        }
        // 加载tree
        try {
            if (agent_type.indexOf("File System") != -1) {
                getQDFileTree($('#qd_pri_id').val());
                if ($('#qd_cvclient_type').val() == 2) { // 目标端
                    $('#qd_cv_select_file').hide();
                } else {
                    $('#qd_cv_select_file').show();
                }
            }
        } catch (e) {
        }

        $('#qd_cv_orcl').hide();
        $('#qd_cv_mssql').hide();
        $('#qd_cv_filesystem').show();
        $('#qd_cv_select_file').show();
    } else if (agent_type.indexOf("SQL Server") != -1) {
        var mssqlOverWrite = cv_params.mssqlOverWrite;
        if (mssqlOverWrite == "False") {
            $('#qd_cv_isoverwrite').prop("checked", false);
        } else {
            $('#qd_cv_isoverwrite').prop("checked", true);
        }

        $('#qd_cv_orcl').hide();
        $('#qd_cv_mssql').show();
        $('#qd_cv_filesystem').hide();
        $('#qd_cv_select_file').hide();
    } else {
        $('#qd_cv_orcl').hide();
        $('#qd_cv_mssql').hide();
        $('#qd_cv_filesystem').hide();
        $('#qd_cv_select_file').hide();
    }
}

function getQDFileTree(cv_id) {
    var setting = {
        async: {
            enable: true,
            url: '../get_file_tree/',
            autoParam: ["id"],
            otherParam: {"cv_id": cv_id},
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

    $.fn.zTree.init($("#qd_cv_fs_tree"), setting);
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
    $("#static").modal({backdrop: "static"});
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
    $("#static").modal({backdrop: "static"});
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
                            "data": {"remark": $("#node_remark").val(), "name": $("#node_name").val(), "pname": $("#pname").val()},
                            "icon": false,
                        }, "last", false, false);
                        $("#id").val(data.nodeid)
                        $('#tree_client').jstree('deselect_all')
                        $('#tree_client').jstree('select_node', $("#id").val(), true)
                    } else {
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
                            "data": {"remark": $("#node_remark").val(), "name": $("#node_name").val(), "pname": $("#pname").val()},
                            "icon": false,
                        }, "last", false, false);
                        $("#id").val(data.nodeid)
                        $('#tree_client').jstree('deselect_all')
                        $('#tree_client').jstree('select_node', $("#id").val(), true)
                        $('#tabcheck2').removeAttr("style", "color: #cbd5dd");
                        $("#tabcheck2").parent().removeAttr("style", "pointer-events:none;");
                    } else {
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
        // 应用类型 -> 参数展示
        displayAgentParams(cv_agent);
    });
    $("#cvclient_type").change(function () {
        if ($("#cvclient_type").val() == "2") {
            $("#sourcediv").hide();
        } else {
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
                        var curnode = $('#tree_client').jstree('get_node', $("#id").val());
                        var newtext = "<img src = '/static/pages/images/cv.png' height='24px'> " + curnode.text
                        $('#tree_client').jstree('set_text', $("#id").val(), newtext);
                    }
                    if ($("#cvclient_type").val() == "2" || $("#cvclient_type").val() == "3") {
                        var destinationdata = JSON.parse($("#cvclient_u_destination").val());
                        for (var i = 0; i < destinationdata.length; i++) {
                            if (destinationdata[i].utilid == $("#cvclient_utils_manage").val()) {
                                var cur_destination = {"name": $("#cvclient_source").find("option:selected").text(), "id": data.cv_id}
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
                            getFileTree($('#cv_id').val());
                            if ($('#cvclient_type').val() == 2) { // 目标端
                                $('#cv_select_file').hide();
                            } else {
                                $('#cv_select_file').show();
                            }
                        }
                    } catch (e) {
                    }
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
        $('#tabcheck4').click();
        var table = $('#cv_backup_his').DataTable();
        var data = table.row($(this).parents('tr')).data();
        var pre_last_time = "";
        try {
            pre_last_time = table.row($(this).parents('tr').next()).data().LastTime;
        } catch (e) {
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
            {"data": "jobid"},
            {"data": "jobType"},
            {"data": "starttime"},
            {"data": "endtime"},
            {"data": "jobstatus"}
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
        if (!$('#cv_r_sourceClient').val()) {
            alert('源客户端为空，请务必先保存Commvault配置。')
        } else {
            if ($('#cv_r_destClient').val() == "") {
                alert("请选择目标客户端。");
            } else {
                if ($("input[name='optionsRadios']:checked").val() == "2" && $('#cv_r_datetimepicker').val() == "")
                    alert("请输入时间。");
                else {
                    if (confirm('是否确定启动自主恢复？')) {
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
        }
    });

    /**
     * 自主恢复
     *      应用对应的参数显示DIV
     */
    $('#navtabs a').on("click", function () {
        var a_id = $(this).prop('id');
        if (a_id == 'tabcheck4') {
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
    });
    $('#jh_cv_selectpath').click(function () {
        $('#jh_cv_fs_se_1').empty();
        var cv_fs_tree = $.fn.zTree.getZTreeObj("jh_cv_fs_tree");
        var nodes = cv_fs_tree.getCheckedNodes(true);
        for (var k = 0, length = nodes.length; k < length; k++) {
            var halfCheck = nodes[k].getCheckStatus();
            if (!halfCheck.half) {
                $("#jh_cv_fs_se_1").append("<option value='" + nodes[k].id + "'>" + nodes[k].id + "</option>");
            }
        }
        if (nodes.length == 0)
            $("#jh_cv_fs_se_1").append("<option value=''></option>");
    });

    /**
     * 选择预案切换
     */
    $('#pros').change(function () {
        try {
            var pro_list = JSON.parse($('#pro_list').val()),
                pro_id = $(this).val();
            $('#associated_host_div').empty();
            $('#host_param_div').empty();

            // 关联主机
            for (var i = 0; i < pro_list.length; i++) {
                if (pro_id == pro_list[i]["process_id"]) {
                    // 预案类型
                    $('#pro_type').val(pro_list[i]['p_type']);

                    // 关联主机
                    var hosts = pro_list[i]["hosts"];
                    for (var j = 0; j < hosts.length; j++) {
                        $('#associated_host_div').append(
                            '<div class="form-group">' +
                            '<label class="col-md-2 control-label">关联主机' + (j + 1) + '</label>\n' +
                            '<div class="col-md-4">\n' +
                            '    <input type="text" id="associated_host_id_' + (j + 1) + '" name="associated_host_id_' + (j + 1) + '" value="' + hosts[j]['hosts_id'] + '" hidden>\n' +
                            '    <input type="text" id="associated_host_' + (j + 1) + '" name="associated_host_' + (j + 1) + '" class="form-control" value="' + hosts[j]['hosts_name'] + '" readonly>\n' +
                            '    <div class="form-control-focus"></div>\n' +
                            '</div>\n' +
                            '<div class="col-md-2 control-label" style="text-align: center; color: #00B83F">\n' +
                            '    <span><i class="fa fa-link fa-lg"></i></span>\n' +
                            '</div>\n' +
                            '<div class="col-md-4">\n' +
                            '    <select name="hosts_manage_' + (j + 1) + '" id="hosts_manage_' + (j + 1) + '" class="form-control">\n' +
                            '    </select>\n' +
                            '    <div class="form-control-focus"></div>\n' +
                            '</div>' +
                            '</div>'
                        );
                    }

                    // HostsManage
                    var hosts_num = hosts.length,
                        hosts_manage_list = $('#hosts_manage_list').val();
                    try {
                        hosts_manage_list = JSON.parse(hosts_manage_list);
                    } catch (e) {
                        hosts_manage_list = [];
                    }
                    for (var L = 0; L < hosts_num; L++) {
                        for (var M = 0; M < hosts_manage_list.length; M++) {
                            $('#hosts_manage_' + (L + 1)).append('<option value="' + hosts_manage_list[M]['id'] + '">' + hosts_manage_list[M]['host_name'] + '</option>');
                        }

                        // 主机参数默认空栏，待选择主机后填充
                        $('#host_param_div').append('<div class="mt-element-ribbon bg-grey-steel" h_id="" style="margin:0">\n' +
                            '    <div class="ribbon ribbon-border-hor ribbon-clip ribbon-color-primary">\n' +
                            '        <div class="ribbon-sub ribbon-clip"></div>\n' +
                            '        待选择\n' +
                            '    </div>\n' +
                            '    <div class="ribbon-content" id="host_param_ribbon_' + (L + 1) + '">\n' +
                            '    </div>\n' +
                            '</div>');
                    }


                    // 流程参数
                    var process_param_list = pro_list[i]['process_param_list'];
                    if (process_param_list.length > 0) {
                        $('#process_div').show();
                    } else {
                        $('#process_div').hide();
                    }

                    $('#pro_param_ribbon').empty();
                    var pro_param_html = '';
                    for (var k = 0; k < process_param_list.length; k++) {
                        var params = process_param_list[k];
                        var pre_group_div = '',
                            aft_group_div = '';
                        if (k % 2 == 0) {  // 奇数(i+1)
                            pre_group_div = '<div class="form-group">\n';
                        } else {
                            aft_group_div = '</div>';
                        }
                        if (k == process_param_list.length - 1) {
                            aft_group_div = '</div>';
                        }
                        pro_param_html += pre_group_div +
                            '    <label class="col-md-2 control-label" style="padding-left: 0;">' + params.param_name + '</label>\n' +
                            '    <div class="col-md-4">\n' +
                            '        <input id="' + params.variable_name + '" type="text" name="' + params.variable_name + '" class="form-control"\n' +
                            '               value="' + params.param_value + '"\n' +
                            '               >\n' +
                            '        <div class="form-control-focus"></div>\n' +
                            '    </div>\n' +
                            aft_group_div;
                    }
                    $('#pro_param_ribbon').append(pro_param_html);
                    // 流程名称
                    $('#process_param_div .ribbon').text(pro_list[i]['process_name']);
                    break;
                }
            }

            /**
             * 选择关联主机
             */
            // $('select[id^="hosts_manage_"]').val("");
            selectAssociatedHost();

            $('select[id^="hosts_manage_"]').val($('#id').val()).trigger('change').prop('disabled', true);

        } catch (e) {
        }
    });


    /**
     * 流程配置保存(实例化)
     * @param pros_id: 预案ID
     * @param associated_hosts: 主机对应关系
     [{
                'host_id': '',
                'host_uuid': '',
                'host_given_name': '',
                'host_name': ''
            },{
                'host_id': '',
                'host_uuid': '',
                'host_given_name': '',
                'host_name': ''
            }]
     * @param config: 流程参数/主机参数
     {
                "PROCESS": [{
                    'params': [{  // 参数集
                        'param_name': '',
                        'variable_name': '',
                        'param_value': '',
                    }]
                }],
                "HOSTS": [{
                    'host_id': '',
                    'host_uuid': '',
                    'host_given_name': '',
                    'host_name': '',
                    'params': [{  // 参数集
                        'param_name': '',
                        'variable_name': '',
                        'param_value': '',
                    }]
                }]
            }
     */
    $('#pro_save').click(function () {
        var pros_id = $('#pros').val(),
            associated_hosts = [];
        $('#associated_host_div').children().each(function (index, el) {
            var associated_host_id = $(el).find('input:first').val(),
                associated_host_name = $(el).find('input:last').val(),
                hosts_manage_id = $(el).find('select[id^="hosts_manage_"]').val(),
                hosts_manage_name = $(el).find('select[id^="hosts_manage_"] option:selected').text();
            associated_hosts.push({
                'host_id': hosts_manage_id,
                'host_uuid': associated_host_id,
                'host_given_name': associated_host_name,
                'host_name': hosts_manage_name,
            })
        });

        var process_params = [];
        $('#process_param_div').find('input').each(function (index, el) {
            var p_variable_name = $(el).prop('id');
            p_param_value = $(el).val();
            p_param_name = $(el).parent().prev().text();
            process_params.push({
                'param_name': p_param_name,
                'variable_name': p_variable_name,
                'param_value': p_param_value,
            })
        });
        var HOSTS = [];
        $('#host_param_div').children().each(function (index, el) {
            var h_params = [],
                h_id = $(el).prop('h_id');
            $(el).find('input').each(function (index, el) {
                var h_variable_name = $(el).prop('id');
                h_param_value = $(el).val();
                h_param_name = $(el).parent().prev().text();
                h_params.push({
                    'param_name': h_param_name,
                    'variable_name': h_variable_name,
                    'param_value': h_param_value,
                })
            });
            var h_config = {}
            // 从associated_hosts匹配出主机对应关系
            for (var i = 0; i < associated_hosts.length; i++) {
                if (h_id == associated_hosts[i]['host_id']) {
                    h_config = associated_hosts[i];
                    break;
                }
            }
            h_config['params'] = h_params
            HOSTS.push(h_config);
        })

        var config = {
            'PROCESS': [{
                'params': process_params,
            }],
            'HOSTS': HOSTS
        }
        try {
            config = JSON.stringify(config);
        } catch (e) {
            config = '{}'
        }
        var table = $('#pro_config').DataTable();
        $.ajax({
            type: 'POST',
            dataType: 'JSON',
            url: '../pro_save/',
            data: {
                'p_id': $('#p_id').val(),  // 实例ID
                'pros_id': pros_id,
                'pro_ins': $('#pro_ins').val(),
                'config': config,
            },
            success: function (data) {
                var status = data.status,
                    info = data.info,
                    data = data.data;
                if (status == 1) {
                    $('#p_id').val(data);
                    $('#static07').modal('hide');
                    table.ajax.reload();
                }
                alert(info);
            }
        });
    });

    /**
     * 新增流程实例
     */
    $('#pro_new').click(function () {
        $('#pro_schedule').hide();

        var host_id = $('#id').val();

        $('#pros').val('');
        $('#p_id').val('0');
        $('#pro_ins').val('');
        /**
         * 初始化
         */
        $('#pro_param_ribbon').empty();
        $('#process_div').hide();
        $('#host_param_div').empty();
        // $('#host_div').hide();
        $('#associated_host_div').empty();
    });

    /**
     * 流程计划
     */
    $("#sche_new").click(function () {
        $("#process_schedule_id").val("0");
        $("#process").val("");
        $("#process_schedule_name").val("");
        $("#per_time").val("00:00").timepicker("setTime", "00:00");
        $("#per_week").val("").trigger("change");
        $("#per_month").val("").trigger("change");
        $("#process_schedule_remark").val("");
        $("#schedule_type").val("");
        $('#Commvault_div').hide();
        $('#jh_cv_select_file').hide();

        /**
         * Commavult
         */
        try {
            var cv_info = JSON.parse($('#cv_info').val());
            var cv_params = cv_info.cv_params,
                agent_type = cv_info.agent_type,
                is_commvault = cv_info.is_commvault;
            if (is_commvault) {
                $('#jh_pri_id').val(cv_params.pri_id);
                $('#jh_pri').val(cv_params.pri_name);
                $('#jh_std').val(cv_params.std_id);

                $('#jh_std').val(cv_params.std_id);

                $('#Commvault_div').show();
            } else {
                $('#Commvault_div').hide();
            }
            displayJHAgentParams(cv_params, agent_type);
        } catch (e) {
            console.log(e)
        }
    });

    // time-picker
    $("#per_time").timepicker({
        showMeridian: false,
        minuteStep: 5,
    }).on('show.timepicker', function () {
        $('#static').removeAttr('tabindex');
    }).on('hide.timepicker', function () {
        $('#static').attr('tabindex', -1);
    });


    $("#schedule_type").change(function () {
        var schedule_type = $(this).val();
        if (schedule_type == 1) {
            $("#per_week_div").hide();
            $("#per_month_div").hide();
        }
        if (schedule_type == 2) {
            $("#per_week").val(1);
            $("#per_week_div").show();
            $("#per_month_div").hide();
        }
        if (schedule_type == 3) {
            $("#per_month").val(1);
            $("#per_week_div").hide();
            $("#per_month_div").show();
        }
    });

    // 主动流程文件系统
    $('#qd_cv_selectpath').click(function () {
        $('#qd_cv_fs_se_1').empty();
        var cv_fs_tree = $.fn.zTree.getZTreeObj("qd_cv_fs_tree");
        var nodes = cv_fs_tree.getCheckedNodes(true);
        for (var k = 0, length = nodes.length; k < length; k++) {
            var halfCheck = nodes[k].getCheckStatus();
            if (!halfCheck.half) {
                $("#qd_cv_fs_se_1").append("<option value='" + nodes[k].id + "'>" + nodes[k].id + "</option>");
            }
        }
        if (nodes.length == 0)
            $("#qd_cv_fs_se_1").append("<option value=''></option>");
    });

    $("#qd_cv_recovery_time_redio_group").click(function () {
        if ($("input[name='qd_optionsRadios']:checked").val() == 2) {
            $("#static09").modal({backdrop: "static"});
            var pri = $("#qd_pri_id").val();
            var datatable = $("#backup_point").dataTable();
            datatable.fnClearTable(); //清空数据
            datatable.fnDestroy();
            $('#backup_point').dataTable({
                "bAutoWidth": true,
                "bProcessing": true,
                "bSort": false,
                "ajax": "../../client_cv_get_backup_his?id=" + pri,
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
            $('#backup_point tbody').on('click', 'button#select', function () {
                var table = $('#backup_point').DataTable();
                var data = table.row($(this).parents('tr')).data();
                $("#qd_recovery_time").val(data.LastTime);
                $("input[name='qd_optionsRadios'][value='1']").prop("checked", false);
                $("input[name='qd_optionsRadios'][value='2']").prop("checked", true);
                $("#browseJobId").val(data.jobId);

                $("#static09").modal("hide");

            });
        } else {
            $("#qd_recovery_time").val("");
        }
    });


    $('#jh_cv_selectpath').click(function () {
        $('#jh_cv_fs_se_1').empty();
        var cv_fs_tree = $.fn.zTree.getZTreeObj("jh_cv_fs_tree");
        var nodes = cv_fs_tree.getCheckedNodes(true);
        for (var k = 0, length = nodes.length; k < length; k++) {
            var halfCheck = nodes[k].getCheckStatus();
            if (!halfCheck.half) {
                $("#jh_cv_fs_se_1").append("<option value='" + nodes[k].id + "'>" + nodes[k].id + "</option>");
            }
        }
        if (nodes.length == 0)
            $("#jh_cv_fs_se_1").append("<option value=''></option>");
    });

    $("#jh_cv_recovery_time_redio_group").click(function () {
        if ($("input[name='jh_optionsRadios']:checked").val() == 2) {
            $("#static09").modal({backdrop: "static"});
            var pri = $("#jh_pri_id").val();
            var datatable = $("#backup_point").dataTable();
            datatable.fnClearTable(); //清空数据
            datatable.fnDestroy();
            $('#backup_point').dataTable({
                "bAutoWidth": true,
                "bProcessing": true,
                "bSort": false,
                "ajax": "../../client_cv_get_backup_his?id=" + pri,
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
            $('#backup_point tbody').on('click', 'button#select', function () {
                var table = $('#backup_point').DataTable();
                var data = table.row($(this).parents('tr')).data();
                $("#jh_recovery_time").val(data.LastTime);
                $("input[name='jh_optionsRadios'][value='1']").prop("checked", false);
                $("input[name='jh_optionsRadios'][value='2']").prop("checked", true);
                $("#jh_browse_job_id").val(data.jobId);

                $("#static09").modal("hide");

            });
        } else {
            $("#jh_recovery_time").val("");
        }
    });

    $('#sche_save').click(function () {
        var table = $('#process_schedule_dt').DataTable();
        // File System
        var iscover = $("input[name='jh_cv_overwrite']:checked").val();
        var mypath = "same"
        if ($("input[name='jh_cv_path']:checked").val() == "2") {
            mypath = $('#jh_cv_mypath').val()
        }
        var selectedfile = "";
        $("#jh_cv_fs_se_1 option").each(function () {
            var txt = $(this).val();
            selectedfile = selectedfile + txt + "*!-!*"
        });
        // SQL Server
        var mssql_iscover = "FALSE"
        if ($('#jh_cv_isoverwrite').is(':checked')) {
            mssql_iscover = "TRUE"
        }
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../process_schedule_save/",
            data: {
                process_schedule_name: $("#process_schedule_name").val(),
                process_schedule_id: $("#process_schedule_id").val(),
                pro_ins_id: $("#p_id").val(),
                schedule_type: $("#schedule_type").val(),
                per_time: $("#per_time").val(),
                per_week: $("#per_week").val(),
                per_month: $("#per_month").val(),
                process_schedule_remark: $("#process_schedule_remark").val(),

                /**
                 * Commvault参数
                 */
                agent_type: $("#jh_agent_type").val(),

                pri: $("#jh_pri_id").val(),
                pri_name: $("#jh_pri").val(),
                std: $("#jh_std").val(),
                recovery_time: $("#jh_recovery_time").val(),
                browseJobId: $("#jh_browse_job_id").val(),

                data_path: $("#jh_cv_data_path").val(),
                copy_priority: $("#jh_cv_copy_priority").val(),
                db_open: $("#jh_cv_db_open").val(),
                log_restore: $("#jh_cv_log_restore").val(),

                // SQL Server
                mssql_iscover: mssql_iscover,

                // File System
                iscover: iscover,
                mypath: mypath,
                selectedfile: selectedfile,
            },
            success: function (data) {
                if (data.ret == 1) {
                    $('#static08').modal('hide');
                    table.ajax.reload();
                    $('#pro_schedule').show();
                }
                alert(data.info);
            },
            error: function (e) {
                alert("页面出现错误，请于管理员联系。");
            }
        });
    });

    function loadScheData() {
        if ($.fn.DataTable.isDataTable('#process_schedule_dt')) {
            $('#process_schedule_dt').dataTable().fnDestroy();
        }
        $('#process_schedule_dt').dataTable({
            "destory": true,
            "bAutoWidth": true,
            "bSort": false,
            "bProcessing": true,
            "ajax": "../process_schedule_data/?pro_ins_id=" + $('#p_id').val(),
            "columns": [
                {"data": "process_schedule_id"},
                {"data": "process_schedule_name"},
                {"data": "schedule_type_display"},
                {"data": null},
                {"data": "remark"},
                {"data": null},
                {"data": null}
            ],
            "columnDefs": [{
                "data": null,
                "targets": -4,
                "render": function (data, type, full) {
                    /*
                        日：
                            00:00
                        周：
                            00:00 周六
                        月：
                            00:00 第2天(月)
                     */
                    var time = full.hours + ":" + full.minutes;
                    var week_map = {1: "周一", 2: "周二", 3: "周三", 4: "周四", 5: "周五", 6: "周六", 7: "周日"};
                    var per_week = week_map[full.per_week];
                    var per_month = full.per_month;

                    if (full.schedule_type == 2) {
                        time += " " + per_week;
                    }
                    if (full.schedule_type == 3) {
                        time += " 第" + per_month + "天(月)";
                    }
                    return "<td>" + time + "</td>"
                },
            }, {
                "data": null,
                "targets": -2,
                "render": function (data, type, full) {
                    // 定时任务状态
                    var status = "";
                    if (full.status == false) {
                        status = "关闭"
                    }
                    if (full.status == true) {
                        status = "开启"
                    }
                    return "<td>" + status + "</td>";
                },
            }, {
                "targets": -1,
                "data": null,
                "width": "100px",
                "render": function (data, type, full) {
                    var statusButton = "";
                    if (full.status == true) {
                        statusButton = "<button title='关闭'  id='reload' class='btn btn-xs btn-danger' type='button'><i class='fa fa-power-off'></i></button>";
                    } else {
                        statusButton = "<button title='启动'  id='reload' class='btn btn-xs btn-primary' type='button'><i class='fa fa-power-off'></i></button>";
                    }
                    return statusButton + "<button  id='edit' title='编辑' data-toggle='modal'  data-target='#static08'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button><button title='删除'  id='delrow' class='btn btn-xs btn-primary' type='button'><i class='fa fa-trash-o'></i></button>";
                },
            }],
            "oLanguage": {
                "sLengthMenu": "每页显示 _MENU_ 条记录",
                "sZeroRecords": "抱歉， 没有找到",
                "sInfo": "从 _START_ 到 _END_ /共 _TOTAL_ 条数据",
                "sInfoEmpty": "没有数据",
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

    }

    $('#process_schedule_dt tbody').on('click', 'button#reload', function () {
        $('#Commvault_div').hide();
        var table = $('#process_schedule_dt').DataTable();
        var data = table.row($(this).parents('tr')).data();
        var confirmInfo = "";
        var status = 0;

        if (data.status == true) {
            confirmInfo = "确定要关闭该流程计划？";
            status = 0;
        } else {
            confirmInfo = "确定要启动该流程计划？";
            status = 1;
        }

        if (confirm(confirmInfo)) {
            $.ajax({
                type: "POST",
                url: "../change_periodictask/",
                data: {
                    process_schedule_id: data.process_schedule_id,
                    process_periodictask_status: status
                },
                success: function (data) {
                    if (data.ret == 1) {
                        table.ajax.reload();
                    }
                    alert(data.info);
                },
                error: function (e) {
                    alert("定时任务状态修改失败，请于管理员联系。");
                }
            });
        }
    });
    $('#process_schedule_dt tbody').on('click', 'button#delrow', function () {
        if (confirm("确定要删除该条数据？")) {
            var table = $('#process_schedule_dt').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $.ajax({
                type: "POST",
                url: "../process_schedule_del/",
                data: {
                    process_schedule_id: data.process_schedule_id,
                },
                success: function (data) {
                    if (data.ret == 1) {
                        table.ajax.reload();
                    }
                    alert(data.info);
                },
                error: function (e) {
                    alert("删除失败，请于管理员联系。");
                }
            });

        }
    });
    $('#process_schedule_dt tbody').on('click', 'button#edit', function () {
        var table = $('#process_schedule_dt').DataTable();
        var data = table.row($(this).parents('tr')).data();

        $("#process_schedule_id").val(data.process_schedule_id);
        $("#process").val(data.process_id);
        $("#process_schedule_name").val(data.process_schedule_name);
        $("#schedule_type").val(data.schedule_type);

        if (data.schedule_type == 1) {
            $("#per_week_div").hide();
            $("#per_month_div").hide();
        }
        if (data.schedule_type == 2) {
            $("#per_week").val(1);
            $("#per_week_div").show();
            $("#per_month_div").hide();
        }
        if (data.schedule_type == 3) {
            $("#per_month").val(1);
            $("#per_week_div").hide();
            $("#per_month_div").show();
        }


        var per_time = data.hours + ":" + data.minutes;
        $("#per_time").val(per_time).timepicker("setTime", per_time);
        $("#per_week").val(data.per_week != "*" ? data.per_week : "").trigger("change");
        $("#per_month").val(data.per_month != "*" ? data.per_month : "").trigger("change");
        $("#process_schedule_remark").val(data.remark);

        /**
         * Commavult
         */
        try {
            var cv_params = data.cv_params,
                agent_type = data.agent_type,
                p_type = data.p_type;
            if (p_type == "Commvault") {
                $('#jh_pri_id').val(cv_params.pri_id);
                $('#jh_pri').val(cv_params.pri_name);
                $('#jh_std').val(cv_params.std_id);

                $('#jh_std').val(cv_params.std_id);

                $('#Commvault_div').show();
            } else {
                $('#Commvault_div').hide();
            }
            displayJHAgentParams(cv_params, agent_type);

            // 恢复时间

        } catch (e) {
            console.log(e)
        }
    });

    $('#static07').on('shown.bs.modal', function () {
        loadScheData();
    });

});
/**
 * 启动自主恢复流程
 */
$("#confirm").click(function () {
    if ($("#confirmtext").val() != "确认启动流程") {
        alert("请在文本框内输入\"确认启动流程\"");
    } else {
        var pro_ins_id = $("#pro_ins_id").val();
        // File System
        var iscover = $("input[name='qd_cv_isoverwrite']:checked").val();
        var mypath = "same"
        if ($("input[name='qd_cv_path']:checked").val() == "2") {
            mypath = $('#qd_cv_mypath').val()
        }
        var selectedfile = ""
        $("#qd_cv_fs_se_1 option").each(function () {
            var txt = $(this).val();
            selectedfile = selectedfile + txt + "*!-!*"
        });
        // SQL Server
        var mssql_iscover = "FALSE"
        if ($('#qd_cv_isoverwrite').is(':checked')) {
            mssql_iscover = "TRUE"
        }
        // 非邀请流程启动
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../falconstorrun/",
            data: {
                pro_ins_id: pro_ins_id,
                run_person: $("#run_person").val(),
                run_time: $("#run_time").val(),
                run_reason: $("#run_reason").val(),

                pri: $("#qd_pri_id").val(),
                std: $("#qd_std").val(),
                agent_type: $("#qd_agent_type").val(),
                recovery_time: $("#qd_recovery_time").val(),
                browseJobId: $("#browseJobId").val(),

                data_path: $("#qd_data_path").val(),
                copy_priority: $("#qd_copy_priority").val(),
                db_open: $("#qd_db_open").val(),
                log_restore: $("#qd_log_restore").val(),

                // SQL Server
                mssql_iscover: mssql_iscover,

                // File System
                iscover: iscover,
                mypath: mypath,
                selectedfile: selectedfile,
            },
            success: function (data) {
                if (data["res"] == "新增成功。") {
                    window.location.href = data["data"];
                } else
                    alert(data["res"]);
            },
            error: function (e) {
                alert("流程启动失败，请于管理员联系。");
            }
        });
    }
});

$('#static10').on("show.bs.modal", function () {
    $('#confirmtext').val("");
    $('#run_reason').val("");
});

