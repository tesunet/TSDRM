$(document).ready(function() {
    $('#target_dt').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../target_data/",
        "columns": [
            { "data": "id" },
            { "data": "client_id" },
            { "data": "client_name" },
            { "data": "agent" },
            { "data": "instance" },
            { "data": "os" },
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
    $('#target_dt tbody').on('click', 'button#delrow', function() {
        if (confirm("确定要删除该条数据？")) {
            var table = $('#target_dt').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $.ajax({
                type: "POST",
                url: "../target_del/",
                data: {
                    target_id: data.id,
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
    $('#target_dt tbody').on('click', 'button#edit', function() {
        var table = $('#target_dt').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $("#target_id").val(data.id);
        $("#target").val(data.client_id);
        // $("#client_id").val(data.client_id);
        $("#agent").val(data.agent);
        $("#instance").val(data.instance);
        $("#os").val(data.os);
    });

    // 加载oracle_data
    // [{"clientname": "myrac1", "instance": "oracle_1", "agent": "Oracle Database", "clientid": 33},
    // {"clientname": "myrac2", "instance": "oracle_2", "agent": "Oracle Database", "clientid": 34},
    // {"clientname": "win-2qls3b7jx3v.hzx", "instance": "ORCL", "agent": "Oracle Database", "clientid": 3}]
    var oracle_data = JSON.parse($("#oracle_data").val());
    for (var i = 0; i < oracle_data.length; i++) {
        $("#target").append('<option value="' + oracle_data[i].clientid + '">' + oracle_data[i].clientname + '</option>');
    }

    // 切换
    $("#target").change(function() {
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
        $("#target_id").val("0");
        $("#target").val("");
        $("#agent").val("");
        $("#instance").val("");
        $("#os").val("");
    });

    $('#save').click(function() {
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