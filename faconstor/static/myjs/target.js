$(document).ready(function () {
    $('#target_dt').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../target_data/",
        "columns": [
            {"data": "id"},
            {"data": "client_id"},
            {"data": "client_name"},
            {"data": "agent"},
            {"data": "instance"},
            {"data": "os"},
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

        },
    });
    // 行按钮
    $('#target_dt tbody').on('click', 'button#delrow', function () {
        if (confirm("确定要删除该条数据？")) {
            var table = $('#target_dt').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $.ajax({
                type: "POST",
                url: "../target_del/",
                data: {
                    target_id: data.id,
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
    $('#target_dt tbody').on('click', 'button#edit', function () {
        var table = $('#target_dt').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $("#target_id").val(data.id);
        $("#target").val(data.client_id);
        $("#agent").val(data.agent);
        $("#instance").val(data.instance);
        $("#os").val(data.os);
        $("#utils_manage").val(data.utils_id);

        // 重载客户端列表
        get_client_list()
    });

    /*
        加载oracle_data
        [{utils_manage: 1,
        oracle_client:
            [{"clientname": "myrac1", "instance": "oracle_1", "agent": "Oracle Database", "clientid": 33},
            {"clientname": "myrac2", "instance": "oracle_2", "agent": "Oracle Database", "clientid": 34},
            {"clientname": "win-2qls3b7jx3v.hzx", "instance": "ORCL", "agent": "Oracle Database", "clientid": 3}]
         },]
     */
    $.ajax({
        type: "POST",
        dataType: 'json',
        url: "../get_orcl_client_from_utils/",
        data: {},
        success: function (data) {
            if (data.status == 1) {
                $('#utils_manage').data('utils_manage_data', data.data);
            } else {
                alert(data.info);
            }
        },
        error: function (e) {
            alert("页面出现错误，请于管理员联系。");
        }
    });

    function get_client_list(){
        $("#target").empty();
        // 加载目标客户端，如果有则选中第一个直接加载应用、实例、平台
        var utils_manage_data = $('#utils_manage').data().utils_manage_data;
        // 加载oracle_client
        var utils_manage_id = $('#utils_manage').val()

        for (var i = 0; i < utils_manage_data.length; i++) {
            if (utils_manage_data[i].utils_manage == utils_manage_id) {
                for (var j = 0; j < utils_manage_data[i].oracle_client.length; j++) {
                    var clientInfo = JSON.stringify(utils_manage_data[i].oracle_client[j]);
                    $("#target").append('<option value="' + utils_manage_data[i].oracle_client[j].clientid
                        + '" clientInfo="' + clientInfo + '">' + utils_manage_data[i].oracle_client[j].clientname + '</option>');
                }
                $('#selected_client_info').val(JSON.stringify(utils_manage_data[i].oracle_client))
                break;
            }
        }
    }


    $('#utils_manage').change(function () {
        get_client_list();
        // 选中第一个
        var firstNode = $("#target").find('option:eq(0)').val()
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
    $("#target").change(function () {
        var clientid = $(this).val();
        fullfilled(clientid);
    });


    $("#new").click(function () {
        $("#target_id").val("0");
        $("#target").val("");
        $("#agent").val("");
        $("#instance").val("");
        $("#os").val("");
        $('#utils_manage').val("");
    });

    $('#save').click(function () {
        var table = $('#target_dt').DataTable();
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../target_save/",
            data: {
                target_id: $("#target_id").val(),
                client_id: $("#target").val(),
                client_name: $("#target").find("option:selected").text(),
                agent: $("#agent").val(),
                instance: $("#instance").val(),
                os: $("#os").val(),

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
    })

    $('#error').click(function () {
        $(this).hide()
    })
});