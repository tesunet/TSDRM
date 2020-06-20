$(document).ready(function () {
    $('#origin_dt').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../origin_data/",
        "columns": [
            {"data": "id"},
            {"data": "client_id"},
            {"data": "client_name"},
            {"data": "agent"},
            {"data": "instance"},
            {"data": "os"},
            {"data": "target_client_name"},
            {"data": "utils_name"},
            {"data": null}
        ],

        "columnDefs": [{
            "targets": -1,
            "data": null,
            "width": "100px",
            "defaultContent": "<button  id='edit' title='编辑' data-toggle='modal'  data-target='#static'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button><button title='删除'  id='delrow' class='btn btn-xs btn-primary' type='button'><i class='fa fa-trash-o'></i></button>"
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

        }
    });
    // 行按钮
    $('#origin_dt tbody').on('click', 'button#delrow', function () {
        if (confirm("确定要删除该条数据？")) {
            var table = $('#origin_dt').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $.ajax({
                type: "POST",
                url: "../origin_del/",
                data: {
                    origin_id: data.id,
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
    $('#origin_dt tbody').on('click', 'button#edit', function () {
        // 重载客户端列表
        get_client_list();

        var table = $('#origin_dt').DataTable();
        var data = table.row($(this).parents('tr')).data();

        $("#origin_id").val(data.id);
        $("#origin").val(data.client_id);
        $("#agent").val(data.agent);
        $("#instance").val(data.instance);
        $("#target").val(data.target_client);
        $("#os").val(data.os);

        $("#copy_priority").val(data.copy_priority);
        $("#db_open").val(data.db_open);
        $("#data_path").val(data.data_path);
        $("#log_restore").val(data.log_restore);

        $("#utils_manage").val(data.utils_id);
    });

    function get_client_list() {
        $("#origin").empty();
        // 加载源客户端，如果有则选中第一个直接加载应用、实例、平台
        var utils_manage_data = eval($('#utils_manage_info').val());
        // 加载oracle_client
        var utils_manage_id = $('#utils_manage').val()

        for (var i = 0; i < utils_manage_data.length; i++) {
            if (utils_manage_data[i].utils_manage == utils_manage_id) {
                for (var j = 0; j < utils_manage_data[i].oracle_client.length; j++) {
                    var clientInfo = JSON.stringify(utils_manage_data[i].oracle_client[j]);
                    $("#origin").append('<option value="' + utils_manage_data[i].oracle_client[j].clientid
                        + '" clientInfo="' + clientInfo + '">' + utils_manage_data[i].oracle_client[j].clientname + '</option>');
                }
                $('#selected_client_info').val(JSON.stringify(utils_manage_data[i].oracle_client))
                break;
            }
        }
        // 加载目标客户端
        $('#target').empty();
        var u_targets = eval($('#u_targets').val());
        for (var i = 0; i < u_targets.length; i++) {
            if (u_targets[i].utils_manage == utils_manage_id) {
                for (var j = 0; j < u_targets[i].target_list.length; j++) {
                    $("#target").append('<option value="' + u_targets[i].target_list[j].target_id
                        + '">' + u_targets[i].target_list[j].target_name + '</option>');
                }
                break;
            }
        }
    }


    $('#utils_manage').change(function () {
        get_client_list();
        // 选中第一个
        var firstNode = $("#origin").find('option:eq(0)').val()
        fullfilled(firstNode);
    })

    // 选中填充信息
    function fullfilled(clientid) {
        var selected_client_info = eval($('#selected_client_info').val());
        for (var i = 0; i < selected_client_info.length; i++) {
            if (clientid == selected_client_info[i].clientid) {
                $("#agent").val(selected_client_info[i].agent);
                $("#instance").val(selected_client_info[i].instance);
                $("#os").val(selected_client_info[i].os);
                break
            }
        }
    }

    // 切换
    $("#origin").change(function () {
        var clientid = $(this).val();
        fullfilled(clientid);
    });

    $("#new").click(function () {
        $("#origin_id").val("0");
        $("#origin").val("");
        $("#agent").val("");
        $("#instance").val("");

        $("#target").val("");
        $("#os").val("");

        $("#copy_priority").val(1);
        $("#db_open").val(1);
        $("#data_path").val("");

        $('#log_restore').val(1);

        $('#utils_manage').val("");
    });

    $('#save').click(function () {
        var table = $('#origin_dt').DataTable();
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../origin_save/",
            data: {
                origin_id: $("#origin_id").val(),
                client_id: $("#origin").val(),
                client_name: $("#origin").find("option:selected").text(),
                agent: $("#agent").val(),
                instance: $("#instance").val(),

                target_client: $("#target").val(),
                os: $("#os").val(),

                // 拷贝优先级/数据重定向路径
                copy_priority: $("#copy_priority").val(),
                db_open: $("#db_open").val(),
                data_path: $("#data_path").val(),

                log_restore: $("#log_restore").val(),

                utils_manage: $('#utils_manage').val()
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

    $('#error').click(function () {
        $(this).hide()
    })
});