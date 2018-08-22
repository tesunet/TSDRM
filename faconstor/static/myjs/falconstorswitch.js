$(document).ready(function () {
    $('#sample_1').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../falconstorswitchdata/",
        "columns": [
            {"data": "name"},
            {"data": "rto"},
            {"data": "rpo"},
            {"data": "remark"},
            {"data": null},

        ],

        "columnDefs": [{
            "targets": -1,
            "data": null,
            "defaultContent": "<button title='启动'  id='runrow' class='btn btn-xs btn-primary' type='button'><i class='fa fa-play'></i></button>"
        }],
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


    $('#sample_1 tbody').on('click', 'button#runrow', function () {
        var table = $('#sample_1').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $("#process_id").val(data.id);
        $("#static").modal({backdrop: "static"});
        // 写入当前时间
        var myDate = new Date();
        $("#run_time").val(myDate.toLocaleString());
    });

    $("#confirm").click(function () {
        var processid = $("#process_id").val();
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../falconstorrun/",
            data:
                {
                    processid: processid,
                    run_person: $("#run_person").val(),
                    run_time: $("#run_time").val(),
                    run_reason: $("#run_reason").val(),
                },
            success: function (data) {
                if (data["res"] == "新增成功。") {
                    window.location.href = data["data"];
                }
                else
                    alert(data["res"]);
            },
            error: function (e) {
                alert("流程启动失败，请于管理员联系。");
            }
        });
    });
});