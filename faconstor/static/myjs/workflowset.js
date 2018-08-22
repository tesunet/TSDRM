$(document).ready(function () {
    $("#stepdiv").empty();
    $.ajax({
        type: "POST",
        url: "../getsetps/",
        data:
            {
                process: $("#process").val()
            },
        dataType: "json",
        success: function (data) {
            var divtxt = ""
            for (var i = 0; i < data.length; i++) {
                var first = ""
                var last = ""
                if (i == 0)
                    first = "first"
                if (i == data.length - 1)
                    last = "last"
                divtxt += "<div onclick=\"myFunction(this)\" id='div_" + data[i]["id"] + "' class='col-md-2 mt-step-col " + first + " " + last + "  active' data-toggle='modal'  data-target='#static'><div class='mt-step-number bg-white'>" + (i + 1).toString() + "</div><div class='mt-step-title uppercase font-grey-cascade'><span id='name_" + data[i]["id"] + "'>" + data[i]["name"] + "</span><input hidden id='approval_" + data[i]["id"] + "' type='text' name='approval_" + data[i]["id"] + "' value='" + data[i]["approval"] + "'><input hidden id='skip_" + data[i]["id"] + "' type='text' name='skip_" + data[i]["id"] + "' value='" + data[i]["skip"] + "'><input hidden id='group_" + data[i]["id"] + "' type='text' name='group_" + data[i]["id"] + "' value='" + data[i]["group"] + "'><input hidden id='time_" + data[i]["id"] + "' type='text' name='time_" + data[i]["id"] + "' value='" + data[i]["time"] + "'></div><div class=\"mt-step-content font-grey-cascade\"><span id='curstring_" + data[i]["id"] + "'>" + data[i]["curstring"] + "</div></div>"
            }
            $("#stepdiv").append(divtxt)
        },
        error: function (e) {
            alert("流程读取失败，请于客服联系。");
        }
    });

    $("#process").change(function () {
        $("#stepdiv").empty();
        $.ajax({
            type: "POST",
            url: "../getsetps/",
            data:
                {
                    process: $("#process").val()
                },
            dataType: "json",
            success: function (data) {
                var divtxt = ""
                for (var i = 0; i < data.length; i++) {
                    var first = ""
                    var last = ""
                    if (i == 0)
                        first = "first"
                    if (i == data.length - 1)
                        last = "last"
                    divtxt += "<div onclick=\"myFunction(this)\" id='div_" + data[i]["id"] + "' class='col-md-2 mt-step-col " + first + " " + last + "  active' data-toggle='modal'  data-target='#static'><div class='mt-step-number bg-white'>" + (i + 1).toString() + "</div><div class='mt-step-title uppercase font-grey-cascade'><span id='name_" + data[i]["id"] + "'>" + data[i]["name"] + "</span><input hidden id='approval_" + data[i]["id"] + "' type='text' name='approval_" + data[i]["id"] + "' value='" + data[i]["approval"] + "'><input hidden id='skip_" + data[i]["id"] + "' type='text' name='skip_" + data[i]["id"] + "' value='" + data[i]["skip"] + "'><input hidden id='group_" + data[i]["id"] + "' type='text' name='group_" + data[i]["id"] + "' value='" + data[i]["group"] + "'><input hidden id='time_" + data[i]["id"] + "' type='text' name='time_" + data[i]["id"] + "' value='" + data[i]["time"] + "'></div><div class=\"mt-step-content font-grey-cascade\"><span id='curstring_" + data[i]["id"] + "'>" + data[i]["curstring"] + "</div></div>"

                }
                $("#stepdiv").append(divtxt)
            },
            error: function (e) {
                alert("流程读取失败，请于客服联系。");
            }
        });
    });
    $("#approval").change(function () {
        if ($("#approval").val() != "1") {
            $("#group").prop("disabled", true)
            $("#group").val("")
        }
        else
            $("#group").removeProp("disabled");

    });
    $('#save').click(function () {
        $.ajax({
            type: "POST",
            url: "../setpsave/",
            data: {
                id: $("#id").val(),
                name: $("#name").val(),
                time: $("#time").val(),
                skip: $("#skip").val(),
                approval: $("#approval").val(),
                group: $("#group").val(),
            },
            success: function (data) {
                alert(data);
                $("#name_" + $("#id").val()).text($("#name").val());
                $("#time_" + $("#id").val()).val($("#time").val());
                $("#approval_" + $("#id").val()).val($("#approval").val());
                $("#skip_" + $("#id").val()).val($("#skip").val());
                $("#group_" + $("#id").val()).val($("#group").val());
                var approvaltext = ""
                if ($("#approval").val() == "1")
                    approvaltext = "需审批"
                var skiptext = ""
                if ($("#skip").val() == "1")
                    skiptext = "可跳过"
                $("#curstring_" + $("#id").val()).text(approvaltext + skiptext);
                $('#static').modal('hide');
            },
            error: function (e) {
                alert("保存失败，请于客服联系。");
            }
        });
    })
});


$('#se_1').contextmenu({
    target: '#context-menu2',
    onItem: function (context, e) {
        if ($(e.target).text() == "新增") {
            $("#scriptid").val("0");
            $("#scriptcode").val("");
            $("#script_name").val("");
            $("#scriptip").val("");
            $("#scriptport").val("");
            $("#scriptusername").val("");
            $("#scriptpassword").val("");
            $("#scriptfilename").val("");
            $("#scriptparamtype").val("无");
            $("#scriptparam").val("");
            $("#scriptscriptpath").val("");
            $("#scriptrunpath").val("");
            $("#scriptcommand").val("");
            $("#scriptmaxtime").val("");
            $("#scripttime").val("");
            document.getElementById("edit").click();
        }
        if ($(e.target).text() == "修改") {
            if ($("#se_1").find('option:selected').length == 0)
                alert("请选择要修改的脚本。");
            else {
                if ($("#se_1").find('option:selected').length > 1)
                    alert("修改时请不要选择多条记录。");
                else {
                    $.ajax({
                        type: "POST",
                        url: "../get_script_data/",
                        data:
                            {
                                id: $("#id").val(),
                                script_id: $("#se_1").find('option:selected').val()
                            },
                        dataType: "json",
                        success: function (data) {
                            $("#scriptid").val(data["id"]);
                            $("#scriptcode").val(data["code"]);
                            $("#script_name").val(data["name"]);
                            $("#scriptip").val(data["ip"]);
                            // $("#scriptport").val(data["port"]);
                            $("#scripttype").val(data.type);
                            // $("#scriptruntype").val(data.runtype);
                            $("#scriptusername").val(data.username);
                            $("#scriptpassword").val(data.password);
                            $("#scriptfilename").val(data.filename);
                            // $("#scriptparamtype").val(data.paramtype);
                            // $("#scriptparam").val(data.param);
                            $("#scriptscriptpath").val(data.scriptpath);
                        //     $("#scriptrunpath").val(data.runpath);
                        //     $("#scriptcommand").val("cd " + $("#scriptscriptpath").val() + ";" + $("#scriptrunpath").val() + "/" + $("#scriptfilename").val() + " " + $("#scriptparam").val());
                        //     $("#scriptmaxtime").val(data.maxtime);
                        //     $("#scripttime").val(data.time);
                        },
                        error: function (e) {
                            alert("数据读取失败，请于客服联系。");
                        }
                    });


                    document.getElementById("edit").click();
                }
            }

        }

        if ($(e.target).text() == "删除") {
            if ($("#se_1").find('option:selected').length == 0)
                alert("请选择要删除的脚本。");
            else {
                if (confirm("确定要删除该脚本吗？")) {
                    $.ajax({
                        type: "POST",
                        url: "../../remove_script/",
                        data:
                            {
                                script_id: $("#se_1").find('option:selected').val(),
                            },
                        success: function (data) {
                            if (data["status"] == 1) {
                                $("#se_1").find('option:selected').remove();
                                alert("删除成功！");
                            }
                            else
                                alert("删除失败，请于管理员联系。");
                        },
                        error: function (e) {
                            alert("删除失败，请于管理员联系。");
                        }
                    });
                }
            }
        }

    }
});

$('#scriptsave').click(function () {
    $.ajax({
        type: "POST",
        dataType: 'json',
        url: "../../processscriptsave/",
        data:
            {
                processid: $("#process option:selected").val(),
                pid: $("#id").val().replace("demo_node_", ""),
                id: $("#scriptid").val().replace("script_", ""),
                code: $("#scriptcode").val(),
                name: $("#script_name").val(),
                ip: $("#scriptip").val(),
                // port: $("#scriptport").val(),
                type: $("#scripttype").val(),
                // runtype: $("#scriptruntype").val(),
                username: $("#scriptusername").val(),
                password: $("#scriptpassword").val(),
                filename: $("#scriptfilename").val(),
                // paramtype: $("#scriptparamtype").val(),
                // param: $("#scriptparam").val(),
                scriptpath: $("#scriptscriptpath").val(),
                // runpath: $("#scriptrunpath").val(),
                // maxtime: $("#scriptmaxtime").val(),
                // time: $("#scripttime").val(),
            },
        success: function (data) {
            var myres = data["res"];
            var mydata = data["data"];
            if (myres == "新增成功。") {
                $("#scriptid").val(data["data"]);
                $("#se_1").append("<option id='" + "script_" + mydata + "'>" + $("#scriptcode").val() + "</option>");
                $('#static01').modal('hide');
            }
            if (myres == "修改成功。") {
                $('#static01').modal('hide');
            }
            alert(myres);
        },
        error: function (e) {
            alert("页面出现错误，请于管理员联系。");
        }
    });
})

$('#sample_1').dataTable({
    "bAutoWidth": true,
    "bSort": false,
    "bProcessing": true,
    "ajax": "../../scriptdata/",
    "columns": [
        {"data": "id"},
        {"data": "code"},
        {"data": "name"},
        {"data": "ip"},
        // {"data": "port"},
        {"data": "type"},
        // {"data": "runtype"},
        {"data": "filename"},
        // {"data": "time"},
        {"data": "username"},
        {"data": "password"},
        // {"data": "paramtype"},
        // {"data": "param"},
        {"data": "scriptpath"},
        // {"data": "runpath"},
        // {"data": "maxtime"},
        {"data": null}
    ],

    "columnDefs": [{
        "targets": -1,
        "data": null,
        "defaultContent": "<button  id='select' title='选择'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-check'></i></button>"
    },
        //     {
        //     "targets": [-2],
        //     "visible": false
        // }, {
        //     "targets": [-3],
        //     "visible": false
        // },
        {
            "targets": [-2],
            "visible": false
        },
        //     {
        //     "targets": [-5],
        //     "visible": false
        // }, {
        //     "targets": [-6],
        //     "visible": false
        // },
        {
            "targets": [-3],
            "visible": false
        }, {
            "targets": [-4],
            "visible": false
        },
        //     {
        //     "targets": [-9],
        //     "visible": false
        // },
        {
            "targets": [0],
            "visible": false
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
$('#sample_1 tbody').on('click', 'button#select', function () {
    var table = $('#sample_1').DataTable();
    var data = table.row($(this).parents('tr')).data();
    $("#scriptcode").val(data.code);
    $("#script_name").val(data.name);
    $("#scriptip").val(data.ip);
    // $("#scriptport").val(data.port);
    $("#scripttype").val(data.type);
    // $("#scriptruntype").val(data.runtype);
    $("#scriptusername").val(data.username);
    $("#scriptpassword").val(data.password);
    $("#scriptfilename").val(data.filename);
    // $("#scriptparamtype").val(data.paramtype);
    // $("#scriptparam").val(data.param);
    $("#scriptscriptpath").val(data.scriptpath);
    // $("#scriptrunpath").val(data.runpath);
    // $("#scriptcommand").val("cd " + $("#scriptscriptpath").val() + ";" + $("#scriptrunpath").val() + "/" + $("#scriptfilename").val() + " " + $("#scriptparam").val());
    // $("#scriptmaxtime").val(data.maxtime);
    // $("#scripttime").val(data.time);
    $('#static1').modal('hide');
});


function myFunction(ob) {
    $("#se_1").empty();
    var id = $(ob).attr("id");
    $("#id").val(id.replace("div_", ""));
    $("#name").val($("#" + id.replace("div", "name")).text());
    $("#time").val($("#" + id.replace("div", "time")).val());
    $("#skip").val($("#" + id.replace("div", "skip")).val());
    $("#approval").val($("#" + id.replace("div", "approval")).val());
    $("#group").val($("#" + id.replace("div", "group")).val());
    if ($("#approval").val() != "1") {
        $("#group").val("")
        $("#group").prop("disabled", true)
    }
    else
        $("#group").removeProp("disabled");
    if (ob.classList.contains("last") > 0)
        $("#scriptsdiv").hide();
    else {
        $("#scriptsdiv").show();
        $.ajax({
            type: "POST",
            url: "../get_scripts/",
            data:
                {
                    step_id: $("#id").val()
                },
            dataType: "json",
            success: function (data) {
                for (var i = 0; i < data.data.length; i++) {
                    $("#se_1").append('<option value="' + data.data[i]["script_id"] + '">' + data.data[i]["script_code"] + '</option>')
                }
            },
            error: function (e) {
                alert("数据读取失败，请于客服联系。");
            }
        });
    }


}