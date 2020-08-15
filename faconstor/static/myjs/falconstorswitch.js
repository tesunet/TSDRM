$(document).ready(function () {
    $("#std").val("");
    var copy_priority_hidden = $("#copy_priority_hidden").val();
    $("#copy_priority").val(copy_priority_hidden);

    var db_open_hidden = $("#db_open_hidden").val();
    $("#db_open").val(db_open_hidden);

    var log_restore_hidden = $("#log_restore_hidden").val();
    $("#log_restore").val(log_restore_hidden);

    function customProcessDataTable() {
        $('#sample_1').dataTable({
            "bAutoWidth": true,
            "bSort": false,
            "bProcessing": true,
            "ajax": "../falconstorswitchdata/",
            "fnServerParams": function (aoData) {
                aoData.push({
                    name: "process_id",
                    value: $("#process_id").val()
                })
            },
            "columns": [
                { "data": "processrun_id" },
                { "data": "process_name" },
                { "data": "process_type" },
                { "data": "createuser" },
                { "data": "state" },
                { "data": "run_reason" },
                { "data": "starttime" },
                { "data": "endtime" },
                { "data": "process_id" },
                { "data": "process_url" },
                { "data": null },
            ],
            "columnDefs": [{
                "targets": 1,
                "render": function (data, type, full) {
                    return "<td><a href='process_url' target='_blank'>data</a></td>".replace("data", full.process_name).replace("process_url", "/processindex/" + full.processrun_id + "?s=true")
                }
            }, {
                "visible": false,
                "targets": -2  // 倒数第一列
            }, {
                "visible": false,
                "targets": -3  // 倒数第一列
            }, {
                "targets": -1,  // 指定最后一列添加按钮；
                "data": null,
                "width": "60px",  // 指定列宽；
                "render": function (data, type, full) {
                    return "<td><button class='btn btn-xs btn-primary' type='button'><a href='/custom_pdf_report/?processrunid&processid'><i class='fa fa-arrow-circle-down' style='color: white'></i></a></button><button title='删除'  id='delrow' class='btn btn-xs btn-primary' type='button'><i class='fa fa-trash-o'></i></button></td>".replace("processrunid", "processrunid=" + full.processrun_id).replace("processid", "processid=" + full.process_id)
                }
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

        $('#sample_1 tbody').on('click', 'button#delrow', function () {
            if (confirm("确定要删除该条数据？")) {
                var table = $('#sample_1').DataTable();
                var data = table.row($(this).parents('tr')).data();
                $.ajax({
                    type: "POST",
                    url: "../../delete_current_process_run/",
                    data:
                    {
                        processrun_id: data.processrun_id
                    },
                    success: function (data) {
                        if (data == 1) {
                            table.ajax.reload();
                            alert("删除成功！");
                        } else
                            alert("删除失败，请于管理员联系。");
                    },
                    error: function (e) {
                        alert("删除失败，请于管理员联系。");
                    }
                });

            }
        });
    }

    customProcessDataTable();

    $("#confirm").click(function () {
        var process_id = $("#process_id").val();
        // File System
        var iscover = $("input[name='overwrite']:checked").val();
        var mypath = "same"
        if ($("input[name='path']:checked").val() == "2") {
            mypath = $('#mypath').val()
        }
        var selectedfile = ""
        $("#fs_se_1 option").each(function () {
            var txt = $(this).val();
            selectedfile = selectedfile + txt + "*!-!*"
        });
        // SQL Server
        var mssql_iscover = "FALSE"
        if ($('#isoverwrite').is(':checked')) {
            mssql_iscover = "TRUE"
        }
        console.log($('#pri').val())
        // 非邀请流程启动
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../falconstorrun/",
            data: {
                processid: process_id,
                run_person: $("#run_person").val(),
                run_time: $("#run_time").val(),
                run_reason: $("#run_reason").val(),

                pri: $("#pri").val(),
                std: $("#std").val(),
                agent_type: $("#agent_type").val(),
                recovery_time: $("#recovery_time").val(),
                browseJobId: $("#browseJobId").val(),

                data_path: $("#data_path").val(),
                copy_priority: $("#copy_priority").val(),
                db_open: $("#db_open").val(),
                log_restore: $("#log_restore").val(),

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
    });


    $("#run").click(function () {
        $("#static").modal({ backdrop: "static" });
        $('#recovery_time').datetimepicker({
            format: 'yyyy-mm-dd hh:ii:ss',
            pickerPosition: 'top-right'
        });
        // 写入当前时间
        var myDate = new Date();
        $("#run_time").val(myDate.toLocaleString());
        $("#std").val("");
    });

    $("#recovery_time_redio_group").click(function () {
        if ($("input[name='recovery_time_redio']:checked").val() == 2) {
            $("#static04").modal({ backdrop: "static" });
            var pri_name = $("#pri_name").val();
            var datatable = $("#backup_point").dataTable();
            datatable.fnClearTable(); //清空数据
            datatable.fnDestroy();
            $('#backup_point').dataTable({
                "bAutoWidth": true,
                "bProcessing": true,
                "bSort": false,
                "ajax": "../../oraclerecoverydata?origin_id=" + origin_id,
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
            $('#backup_point tbody').on('click', 'button#select', function () {
                var table = $('#backup_point').DataTable();
                var data = table.row($(this).parents('tr')).data();
                $("#recovery_time").val(data.LastTime);
                $("input[name='recovery_time_redio'][value='1']").prop("checked", false);
                $("input[name='recovery_time_redio'][value='2']").prop("checked", true);
                $("#browseJobId").val(data.jobId);

                $("#static04").modal("hide");

            });
        } else {
            $("#recovery_time").val("");
        }
    });

    // modal.show事件
    $("#static").on("shown.bs.modal", function (event) {
        $("#std").val($("#std_selected").val());
        $("#run_reason").val("");
        $("#recovery_time").val("");

        // 写入当前时间
        var myDate = new Date();
        $("#run_time").val(myDate.toLocaleString());
        $("input[name='recovery_time_redio'][value='1']").prop("checked", true);
        $("input[name='recovery_time_redio'][value='2']").prop("checked", false);
    });

    // File System加载目录树
    // params: client_id agent_type
    var agent_type = $('#agent_type').val(),
        cv_id = $('#cv_id').val();
    if (agent_type.indexOf("File System") != -1) {
        var setting = {
            async: {
                enable: true,
                url: '../get_file_tree/',
                autoParam: ["id"],
                otherParam: { "cv_id": cv_id },
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
        $.fn.zTree.init($("#fs_tree"), setting);
    }
    // 选中文件
    $('#selectpath').click(function () {
        $('#fs_se_1').empty();
        var fs_tree = $.fn.zTree.getZTreeObj("fs_tree");
        var nodes = fs_tree.getCheckedNodes(true);
        for (var k = 0, length = nodes.length; k < length; k++) {
            var halfCheck = nodes[k].getCheckStatus();
            if (!halfCheck.half) {
                $("#fs_se_1").append("<option value='\\" + nodes[k].id + "\\'>\\" + nodes[k].id + "\\</option>");
            }
        }
        if (nodes.length == 0)
            $("#fs_se_1").append("<option value='\\'>\\</option>");
    })
});
