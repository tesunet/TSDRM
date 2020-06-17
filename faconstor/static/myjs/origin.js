$(document).ready(function() {
    $('#origin_dt').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../origin_data/",
        "columns": [
            { "data": "id" },
            { "data": "client_id" },
            { "data": "client_name" },
            { "data": "agent" },
            { "data": "instance" },
            { "data": "os" },
            { "data": "target_client_name" },
            { "data": null }
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

        }
    });
    // 行按钮
    $('#origin_dt tbody').on('click', 'button#delrow', function() {
        if (confirm("确定要删除该条数据？")) {
            var table = $('#origin_dt').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $.ajax({
                type: "POST",
                url: "../origin_del/",
                data: {
                    origin_id: data.id,
                },
                success: function(data) {
                    if (data.ret == 1) {
                        table.ajax.reload();
                    }
                    alert(data.info);
                },
                error: function(e) {
                    alert("删除失败，请于管理员联系。");
                }
            });

        }
    });
    $('#origin_dt tbody').on('click', 'button#edit', function() {
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
        console.log(data.log_restore)
        $("#log_restore").val(data.log_restore);
    });

    var oracle_data = JSON.parse($("#oracle_data").val());
    for (var i = 0; i < oracle_data.length; i++) {
        $("#origin").append('<option value="' + oracle_data[i].clientid + '">' + oracle_data[i].clientname + '</option>');
    }

    // 切换
    $("#origin").change(function() {
        //..
        var clientid = $(this).val();

        for (var i = 0; i < oracle_data.length; i++) {
            if (clientid == oracle_data[i].clientid) {
                $("#agent").val(oracle_data[i].agent);
                $("#instance").val(oracle_data[i].instance);
                $("#os").val(oracle_data[i].os);
                break
            }
        }
    });


    $("#new").click(function() {
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
    });

    $('#save').click(function() {
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
            },
            success: function(data) {
                if (data.ret == 1) {
                    $('#static').modal('hide');
                    table.ajax.reload();
                }
                alert(data.info);
            },
            error: function(e) {
                alert("页面出现错误，请于管理员联系。");
            }
        });
    });

    $('#error').click(function() {
        $(this).hide()
    })
});