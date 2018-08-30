$(document).ready(function () {
    $('#sample_1').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../falconstorswitchdata/",
        "columns": [
            {"data": "processrun_id"},
            {"data": "process_name"},
            {"data": "createuser"},
            {"data": "state"},
            {"data": "run_reason"},
            {"data": "starttime"},
            {"data": "endtime"},
            {"data": "process_id"},
            {"data": "process_url"},
            {"data": null},
        ],
        "columnDefs": [{
            "targets": 1,
            "render": function (data, type, full) {
                return "<td><a href='process_url'>data</a></td>".replace("data", full.process_name).replace("process_url", full.process_url + "/" + full.processrun_id)
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
                return "<td><a href='/custom_pdf_report/?processrunid&processid'></td><i class='fa fa-arrow-down'></i></a>".replace("processrunid", "processrunid=" + full.processrun_id).replace("processid", "processid=" + full.process_id)
            }
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

    $("#confirm").click(function () {
        var processid = $("#processid").val();
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

    $("#run").click(function () {
        var process_id = $("#process_id").val();
        $("#processid").val(process_id);
        $("#static").modal({backdrop: "static"});
        // 写入当前时间
        var myDate = new Date();
        $("#run_time").val(myDate.toLocaleString());
    })
    $("#invite").click(function () {
        $("#person_invited").empty();
        $("#invite_reason").val("");
        var process_id = $("#process_id").val();
        $("#processid").val(process_id);
        $("#static01").modal({backdrop: "static"});
        // 写入当前时间
        var myDate = new Date();
        $("#invite_time").val(myDate.toLocaleString());

        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../get_all_users/",
            data: {},
            success: function (data) {
                var userList = data.data.split("&");
                for (var i = 0; i < userList.length - 1; i++) {
                    var user = userList[i];
                    $("#person_invited").append('<option value="' + user + '">' + user + '</option>')
                }
            },
            error: function (e) {
                alert("流程启动失败，请于管理员联系。");
            }
        });

    })
});