function selectAssociatedHost() {
    /**
     * 注册选中事件
     */
    $('select[id^="hosts_manage_"]').change(function () {
        $('#host_div').show();
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
                    "<button title='启动'  id='setup' class='btn btn-xs btn-primary' type='button' disabled><i class='fa fa-power-off'></i></button>";
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
        var table = $('#pro_config').DataTable();
        var data = table.row($(this).parents('tr')).data();
        console.log(data.process_id)
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
        if (HOST.length > 0) {
            $('#host_div').show();
        } else {
            $('#host_div').hide();
        }
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
    });
}

getProcessInstancedata('');

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
        $('select[id^="hosts_manage_"]').val("");
        selectAssociatedHost();
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
    $('#host_div').hide();
    $('#associated_host_div').empty();
});