$(document).ready(function() {
    $('#hosts_dt').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../hosts_manage_data/",
        "columns": [
            { "data": "host_id" },
            { "data": "host_ip" },
            { "data": "os" },
            { "data": "type" },
            { "data": "username" },
            { "data": "password" },
            { "data": null }
        ],

        "columnDefs": [{
            "targets": -2,
            "visible": false,
        }, {
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
    $('#hosts_dt tbody').on('click', 'button#delrow', function() {
        if (confirm("确定要删除该条数据？")) {
            var table = $('#hosts_dt').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $.ajax({
                type: "POST",
                url: "../hosts_manage_del/",
                data: {
                    host_id: data.host_id,
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
    $('#hosts_dt tbody').on('click', 'button#edit', function() {
        var table = $('#hosts_dt').DataTable();
        var data = table.row($(this).parents('tr')).data();

        $("#host_id").val(data.host_id);
        $("#host_ip").val(data.host_ip);
        $("#os").val(data.os);
        $("#type").val(data.type);
        $("#username").val(data.username);
        $("#password").val(data.password);
    });

    $("#new").click(function() {
        $("#host_id").val("0");
        $("#host_ip").val("");
        $("#os").val("");
        $("#type").val("");
        $("#username").val("");
        $("#password").val("");
    });

    $('#save').click(function() {
        var table = $('#hosts_dt').DataTable();

        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../host_save/",
            data: {
                host_id: $("#host_id").val(),
                host_ip: $("#host_ip").val(),
                os: $("#os").val(),
                type: $("#type").val(),
                username: $("#username").val(),
                password: $("#password").val(),
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
    })

    $('#error').click(function() {
        $(this).hide()
    })
});