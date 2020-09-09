$('#process_schedule_dt').dataTable({
    "destory": true,
    "bAutoWidth": true,
    "bSort": false,
    "bProcessing": true,
    "ajax": "../process_schedule_data/",
    "columns": [
        {"data": "process_schedule_id"},
        {"data": "process_schedule_name"},
        {"data": "process_name"},
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
            return statusButton + "<button  id='edit' title='编辑' data-toggle='modal'  data-target='#static'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button><button title='删除'  id='delrow' class='btn btn-xs btn-primary' type='button'><i class='fa fa-trash-o'></i></button>";
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
// 行按钮
$('#process_schedule_dt tbody').on('click', 'button#reload', function () {
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
            $('#pri_id').val(cv_params.pri_id);
            $('#pri').val(cv_params.pri_name);
            $('#std').val(cv_params.std_id);
            var recovery_time = cv_params.recovery_time;

            if (recovery_time){
                $("input[name='optionsRadios'][value='2']").prop("checked", true);
                $('#recovery_time').val(recovery_time);
            } else {
                $("input[name='optionsRadios'][value='1']").prop("checked", true);
                $('#recovery_time').val("");
            }

            $('#std').val(cv_params.std_id);

            $('#Commvault_div').show();
        } else {
            $('#Commvault_div').hide();
        }
        displayAgentParams(cv_params, agent_type);

        // 恢复时间

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

$("#new").click(function () {
    $("#process_schedule_id").val("0");
    $("#process").val("");
    $("#process_schedule_name").val("");
    $("#per_time").val("00:00").timepicker("setTime", "00:00");
    $("#per_week").val("").trigger("change");
    $("#per_month").val("").trigger("change");
    $("#process_schedule_remark").val("");
    $("#schedule_type").val("");
    $('#Commvault_div').hide();
    $('#cv_select_file').hide();
});

$('#save').click(function () {
    var table = $('#process_schedule_dt').DataTable();
    // File System
    var iscover = $("input[name='cv_overwrite']:checked").val();
    var mypath = "same"
    if ($("input[name='cv_path']:checked").val() == "2") {
        mypath = $('#cv_mypath').val()
    }
    var selectedfile = "";
    $("#cv_fs_se_1 option").each(function () {
        var txt = $(this).val();
        selectedfile = selectedfile + txt + "*!-!*"
    });
    // SQL Server
    var mssql_iscover = "FALSE"
    if ($('#cv_isoverwrite').is(':checked')) {
        mssql_iscover = "TRUE"
    }
    $.ajax({
        type: "POST",
        dataType: 'json',
        url: "../process_schedule_save/",
        data: {
            process_schedule_name: $("#process_schedule_name").val(),
            process_schedule_id: $("#process_schedule_id").val(),
            process: $("#process").val(),
            schedule_type: $("#schedule_type").val(),
            per_time: $("#per_time").val(),
            per_week: $("#per_week").val(),
            per_month: $("#per_month").val(),
            process_schedule_remark: $("#process_schedule_remark").val(),

            /**
             * Commvault参数
             */
            agent_type: $("#agent_type").val(),

            pri: $("#pri_id").val(),
            pri_name: $("#pri").val(),
            std: $("#std").val(),
            recovery_time: $("#recovery_time").val(),
            browseJobId: $("#browse_job_id").val(),

            data_path: $("#cv_data_path").val(),
            copy_priority: $("#cv_copy_priority").val(),
            db_open: $("#cv_db_open").val(),
            log_restore: $("#cv_log_restore").val(),

            // SQL Server
            mssql_iscover: mssql_iscover,

            // File System
            iscover: iscover,
            mypath: mypath,
            selectedfile: selectedfile,
        },
        success: function (data) {
            if (data.ret == 1) {
                $('#static').modal('hide');
                table.ajax.reload();
            }
            alert(data.info);
        },
        error: function (e) {
            alert("页面出现错误，请于管理员联系。");
        }
    });
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

function getFileTree() {
    var setting = {
        async: {
            enable: true,
            url: '../get_file_tree/',
            autoParam: ["id"],
            otherParam: {"cv_id": $('#pri_id').val()},
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

function displayProcessParams(p_id) {
    /**
     * Commvault流程下应用参数
     */
    for (var i = 0; i < p_params.length; i++) {
        var p_param = p_params[i],
            p_type = p_params[i].p_type,
            cv_params = p_params[i].cv_params;

        /*
         * 对应流程参数
         */
        if (p_type == "Commvault") {
            $('#pri_id').val(cv_params.pri_id);
            $('#pri').val(cv_params.pri_name);
            $('#std').val(cv_params.std_id);

            $('#Commvault_div').show();
        } else {
            $('#Commvault_div').hide();
        }

        if (p_id == p_param.p_id) {
            displayAgentParams(cv_params, p_param.agent_type)
            break;
        }
    }
}

function displayAgentParams(cv_params, agent_type) {
    /**
     * 应用参数
     */
    $('#agent_type').val(agent_type);
    if (agent_type.indexOf("Oracle") != -1) {
        $('#cv_copy_priority').val(cv_params.copy_priority);
        $('#cv_db_open').val(cv_params.db_open);
        $('#cv_log_restore').val(cv_params.log_restore);
        $('#cv_data_path').val(cv_params.data_path);

        $('#cv_orcl').show();
        $('#cv_mssql').hide();
        $('#cv_filesystem').hide();
        $('#cv_select_file').hide();
    } else if (agent_type.indexOf("File System") != -1) {
        var overWrite = cv_params.overWrite,
            destPath = cv_params.destPath,
            sourcePaths = cv_params.sourcePaths;
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
            if (agent_type.indexOf("File System") != -1) {
                getFileTree();
                if ($('#cvclient_type').val() == 2) { // 目标端
                    $('#cv_select_file').hide();
                } else {
                    $('#cv_select_file').show();
                }
            }
        } catch (e) {
        }

        $('#cv_orcl').hide();
        $('#cv_mssql').hide();
        $('#cv_filesystem').show();
        $('#cv_select_file').show();
    } else if (agent_type.indexOf("SQL Server") != -1) {
        var mssqlOverWrite = cv_params.mssqlOverWrite;
        if (mssqlOverWrite == "False") {
            $('#cv_isoverwrite').prop("checked", false);
        } else {
            $('#cv_isoverwrite').prop("checked", true);
        }

        $('#cv_orcl').hide();
        $('#cv_mssql').show();
        $('#cv_filesystem').hide();
        $('#cv_select_file').hide();
    } else {
        $('#cv_orcl').hide();
        $('#cv_mssql').hide();
        $('#cv_filesystem').hide();
        $('#cv_select_file').hide();
    }
}

$('#process').change(function () {
    var p_id = $(this).val();
    displayProcessParams(p_id);
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

$("#cv_recovery_time_redio_group").click(function () {
    if ($("input[name='optionsRadios']:checked").val() == 2) {
        $("#static02").modal({backdrop: "static"});
        var pri = $("#pri_id").val();
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
            $("#recovery_time").val(data.LastTime);
            $("input[name='optionsRadios'][value='1']").prop("checked", false);
            $("input[name='optionsRadios'][value='2']").prop("checked", true);
            $("#browse_job_id").val(data.jobId);

            $("#static02").modal("hide");

        });
    } else {
        $("#recovery_time").val("");
    }
});

