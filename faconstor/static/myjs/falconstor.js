var FormWizard = function () {


    return {
        //main function to initiate the module
        init: function () {
            if (!jQuery().bootstrapWizard) {
                return;
            }
            var handleTitle = function (index, state) {
                var total = $("ul.steps").find('li').length;
                var current = index + 1;
                $('#li' + current.toString() + ' a').tab("show")
                App.scrollTo($('.page-title'));
            }


            // default form wizard
            $('#form_wizard_1').bootstrapWizard({
                'nextSelector': '.button-next',
                'previousSelector': '.button-previous',
                onTabClick: function (tab, navigation, index, clickedIndex) {
                    handleTitle(clickedIndex, "EDIT");

                },
                onNext: function (tab, navigation, index) {

                },
                onPrevious: function (tab, navigation, index) {

                },
                onTabShow: function (tab, navigation, index) {
                    var total = navigation.find('li').length;
                    var current = index + 1;
                    var $percent = (current / total) * 100;
                    // $('#form_wizard_1').find('.progress-bar').css({
                    //     width: $percent + '%'
                    // });
                }
            });


        }

    };

}();

if (App.isAngularJsApp() === false) {
    jQuery(document).ready(function () {
        var global_end = false;
        var curHref = window.href;
        function customOurInterval(argument) {
            setTimeout(function () {
                if (!global_end) {
                    // 处理时对end标志进行修改，end=True表示停止（取消定时器）。
                    if (curHref.indexOf("falconstor") != -1) {
                        getstep();
                    };

                    // 循环(arguments.callee获取当前执行函数的引用)
                    setTimeout(arguments.callee, 3000);
                } else {
                    global_end = false;
                }
            }, 3000);
        }

        // 点击页面后1分钟刷新页面
        $(document).on('click', function () {
            global_end = true;
            console.log("点击页面，不动")
            setTimeout(function () {
                global_end = false; 
                customOurInterval();
            }, 60000);
        });

        customOurInterval();

        function showResult() {
            var process_run_id = $("#process_run_id").val();
            $.ajax({
                url: "../../show_result/",
                type: "post",
                data: {
                    "process_run_id": process_run_id,
                },
                success: function (data) {
                    $("table#process_data tbody").empty();
                    $("table#group_data tbody").empty();

                    $("#current_process").text(data.process_name);
                    $("#summary").text("为了提高防范灾难风险的能力，保证业务连续性要求，在公司总经理室高度重视下，太平资产成立灾备演练项目组，于time进行核心系统灾备演练，并取得圆满成功。演练具体情况报告如下。".replace("time", data.processrun_time));

                    var elements = "";
                    for (var i = 0; i < data.step_info_list.length; i++) {
                        // wrapper_step
                        var stepWrapper = data.step_info_list[i];
                        var innerStep = stepWrapper.inner_step_list;
                        if (innerStep != "" && innerStep != null) {
                            var innerStepLength = innerStep.length;
                            var rowSpanString = ' rowspan="' + innerStepLength + '"';
                        } else {
                            rowSpanString = "";
                        }

                        if (stepWrapper.operator) {
                            var stepWrapperOperator = stepWrapper.operator
                        } else {
                            var stepWrapperOperator = ""
                        }
                        elements += '<tr><td' + rowSpanString + '><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">*' + stepWrapper.step_name + '</font></font></td>';
                        // inner_step
                        if (innerStep != "" && innerStep != null) {
                            for (var j = 0; j < innerStep.length; j++) {
                                if (innerStep[j].operator) {
                                    var stepInnerOperator = innerStep[j].operator
                                } else {
                                    var stepInnerOperator = ""
                                }

                                elements += '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">**' + innerStep[j].step_name + '</font></font></td>' +
                                    '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + stepInnerOperator + '</font></font></td>' +
                                    '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + innerStep[j].start_time + '</font></font></td>' +
                                    '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + innerStep[j].end_time + '</font></font></td>' +
                                    '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + innerStep[j].rto + '</font></font></td></tr>'
                            }
                        } else {
                            elements += '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;"></font></font></td>' +
                                '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + stepWrapperOperator + '</font></font></td>' +
                                '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + stepWrapper.start_time + '</font></font></td>' +
                                '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + stepWrapper.end_time + '</font></font></td>' +
                                '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + stepWrapper.rto + '</font></font></td></tr>'
                        }
                    }
                    // 添加流程总RTO
                    elements += '<tr><td' + rowSpanString + '><font style="vertical-align: inherit;"><font style="vertical-align: inherit;"><font color="#ff0000">*</font>总环节</font></font></td>';
                    elements += '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;"></font></font></td>' +
                        '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;"></font></font></td>' +
                        '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + data.start_time + '</font></font></td>' +
                        '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + data.end_time + '</font></font></td>' +
                        '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + data.rto + '</font></font></td></tr>';

                    $("table#process_data tbody").append(elements);

                    var groupElements = "";
                    for (var i = 0; i < data.total_list.length; i++) {
                        var currentGroup = data.total_list[i];
                        var userList = currentGroup.current_users_and_departments;
                        if (userList != "" && userList != null) {
                            var userListLength = userList.length;
                            var rowSpanString01 = ' rowspan="' + userListLength + '"';
                        } else {
                            rowSpanString01 = "";
                        }
                        groupElements += '<tr><td' + rowSpanString01 + '><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + currentGroup.group + '</font></font></td>';
                        if (userList != "" && userList != null) {
                            for (var j = 0; j < userList.length; j++) {
                                groupElements += '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + userList[j].fullname + '</font></font></td>' +
                                    '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + userList[j].depart_name + '</font></font></td></tr>'
                            }
                        } else {
                            groupElements += '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;"></font></font></td>' +
                                '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;"></font></font></td></tr>'
                        }
                    }
                    $("table#group_data tbody").append(groupElements);
                }
            });
        }


        // 构造异步任务表
        function customTasksTable() {
            $("#task_info").dataTable().fnDestroy();
            $("#task_info").dataTable({
                "searching": false,
                "paging": false,
                "ordering": false,
                "info": false,
                "bAutoWidth": true,
                "bSort": false,
                "bProcessing": true,
                "ajax": "../../get_celery_tasks_info/",
                "columns": [
                    {"data": "uuid"},
                    {"data": "state"},
                    {"data": "args"},
                    {"data": "received"},
                ],
                "columnDefs": [{
                    targets: 0,
                    width: "340px",
                },],
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
            })
        }


        // 获取异步任务状态
        function getTaskStatus(process_run_id, abnormal) {
            // 判断获取异步任务状态,"1"表示自主关闭，"0"表示异常关闭
            $.ajax({
                url: "../../revoke_current_task/",
                type: "post",
                data: {
                    "process_run_id": process_run_id,
                    "abnormal": abnormal,
                },
                success: function (data) {
                    if (abnormal == "1") {
                        alert(data.data);
                        customTasksTable();
                    } else if (data.data != "异步任务未出现异常") {
                        alert(data.data);
                    }
                }
            });
        }

        var getStepTimes = 0;
        function getstep() {
            console.log('loading...');
            $.ajax({
                type: "POST",
                url: "../../getrunsetps/",
                data:
                    {
                        process: $("#process").val()
                    },
                dataType: "json",
                success: function (data) {
                    $("#show_force_script").hide();

                    $("ul.steps").empty();
                    $("div#tab-content").empty();
                    $("#current_process_task_info").empty();
                    $("#stopbtn").show();
                    $("#show_result").hide();
                    $("#process_run_id").val($("#process").val());
                    $("#process_name").html(data["process_name"] + "&nbsp&nbsp <button id='show_tasks' type='button' style='background-color: #1d89cf'><i class='fa fa-cogs'></i></button>");
                    $("#process_starttime").val(data["process_starttime"]);
                    $("#process_endtime").val(data["process_endtime"]);
                    $("#process_note").val(data["process_note"]);
                    $("#process_rto").val(data["process_rto"]);

                    var totalTaskLi = ''
                    // 右侧当前任务
                    for (var i = 0; i < data["current_process_task_info"].length; i++) {
                        var currentTaskLi = '<li class="col-md-12"><div class="col1"><div class="cont"><div class="cont-col1"><div class="label label-sm ' +
                            data["current_process_task_info"][i].task_color + '"><i class="' + data["current_process_task_info"][i].task_icon +
                            '"></i></div></div><div class="cont-col2"><div class="desc"> ' + data["current_process_task_info"][i].content +
                            '</div></div></div></div><div class="col2"><div class="date"> ' + data["current_process_task_info"][i].time + '</div></div></li>'
                        totalTaskLi += currentTaskLi
                    }
                    $("#current_process_task_info").append(totalTaskLi);

                    if (data["process_state"] == "DONE") {
                        // 隐藏查看异步任务的按钮
                        $("#process_name").html(data["process_name"]);

                        $("#process_state").val("完成");
                        $("#stopbtn").hide();

                        // 完成的状态下关闭定时器
                        global_end = true;
                        // window.clearInterval(t2);

                        $("#show_result").show();

                        if (getStepTimes < 1) {
                            if (confirm("是否查看流程报告？")) {
                                // 自动触发模态框
                                $("#process_result").modal({ backdrop: "static" });

                                showResult();
                            }
                            getStepTimes += 1
                        }
                        // if (confirm("是否查看流程报告？")) {
                        //     // 自动触发模态框
                        //     $("#process_result").modal({backdrop: "static"});

                        //     showResult();
                        // }
                    }

                    if (data["process_state"] == "RUN"){
                        // 异常异步任务处理
                        var process_run_id = $("#process_run_id").val();
                        var abnormal = "0";
                        getTaskStatus(process_run_id, abnormal);
                        $("#process_state").val("运行");
                    }
                    if (data["process_state"] == "PLAN"){
                        $("#process_state").val("计划");
                    }
                    if (data["process_state"] == "ERROR") {
                        $("#process_state").val("错误");
                        // 错误的状态下，关闭定时器
                        global_end = true;
                        // window.clearInterval(t2);
                    }
                    if (data["process_state"] == "STOP") {
                        $("#process_state").val("停止");
                        // 隐藏查看异步任务的按钮
                        $("#process_name").html(data["process_name"]);

                        $("#stopbtn").hide();

                        // 错误的状态下，关闭定时器
                        global_end = true;
                        // window.clearInterval(t2);

                        $("#show_result").show();

                        // 显示强制执行脚本modal触发按钮
                        $("#show_force_script").show();
                    }
                    var processallsteps = 0;
                    var processdonesteps = 0;
                    var showButtonId = "";

                    var innerUl = "";
                    for (var i = 0; i < data["step"].length; i++) {

                        var first = "";
                        var last = "";
                        if (i == 0)
                            first = "first";
                        if (i == data["step"].length - 1)
                            last = "last";
                        var tabdone = "";
                        if (data["step"][i]["state"] == "DONE")
                            tabdone = "done";
                        var tabrun = "";
                        if (data["step"][i]["state"] == "RUN" || data["step"][i]["state"] == "CONFIRM" || data["step"][i]["state"] == "CONTINUE" || data["step"][i]["state"] == "ERROR" || ((i == data["step"].length - 1) && data["step"][i]["state"] == "DONE"))
                            tabrun = "active";
                        /*
                        innerUl += "<li style='text-align:center;' id='li_" + (i + 1).toString() + "' class='" + tabdone + " " + tabrun + "'><i style='display: none;' class='fa fa-check'></i>" + data["step"][i]["name"] + " </span></a></li>";
                        var arrowStr = "<i class='fa fa-angle-right fa-3x'></i>";
                        $("ul.steps").append("<li id='li_" + (i + 1).toString() + "' class='" + tabdone + " " + tabrun + "'><a href='#tab" + (i + 1).toString() + "' data-toggle='tab' class='step' aria-expanded='true'><span class='number' style='line-height: 100px;font-size: 40px;'> " + (i + 1).toString() + " </span></a></li>");


                        var arrowStr = "<i style='text-align: center' class='fa fa-angle-right fa-3x'></i><i style='text-align: center' class='fa fa-angle-right fa-3x'></i>";
                        if (i==0){
                            arrowStr = ""
                        }
                        */
                        $("ul.steps").append("<li id='li_" + (i + 1).toString() + "' class='" + tabdone + " " + tabrun + "'><a href='#tab" + (i + 1).toString() + "' data-toggle='tab' class='step' aria-expanded='true'><span class='number'> " + (i + 1).toString() + " </span><span class='desc'><i hidden class='fa fa-check'></i> " + data["step"][i]["name"] + " </span></a></li>");
                        $("div#tab-content").append("<div class='tab-pane " + tabrun + "' id='tab" + (i + 1).toString() + "'></div>");

                        $("#tab" + (i + 1).toString()).append("<div id='tabdiv" + (i + 1).toString() + "' class='mt-element-step'></div>");
                        var step1_id = data["step"][i]["id"];
                        var step1_run_id = data["step"][i]["runid"];
                        var step1_name = data["step"][i]["name"];
                        var step1_state = data["step"][i]["state"];
                        var step1_starttime = data["step"][i]["starttime"];
                        var step1_endtime = data["step"][i]["endtime"];
                        var step1_rto = data["step"][i]["rto"];
                        var step1_group = data["step"][i]["group"] != null ? data["step"][i]["group"] : "";
                        var step1_operator = data["step"][i]["operator"];
                        var step1_note = data["step"][i]["note"];
                        var step1_verify = data["step"][i]["verify"];
                        processallsteps = processallsteps + 1;
                        var expand = "collapse";
                        var bar = "";
                        var style = "";
                        var stepbtn = "";
                        if (data["step"][i]["children"].length > 0) {
                            expand = "expand";
                            bar = "<div id=\"step_bar\"" + (i + 1).toString() + " class=\"progress progress-striped\"\n" +
                                "                                                             role=\"progressbar\">\n" +
                                "                                                            <div id=\"step_bar_\"" + (i + 1).toString() + " class=\"progress-bar progress-bar-success\"\n" +
                                "                                                                 style=\"width: 0%;\"></div>\n" +
                                "                                                        </div>";
                            style = "style=\"display: none;\""
                        }
                        if (step1_state == "DONE") {
                            step1_state = "完成";
                            processdonesteps = processdonesteps + 1
                        }

                        if (step1_state == "CONFIRM") {
                            global_end = true;

                            step1_state = "待确认";
                            expand = "collapse";
                            style = "";
                            stepbtn = "<div class=\"form-actions noborder\" style=\"text-align:center\" hidden>\n" + "<input name='step_id' id='step_id' value='" + step1_run_id + "' hidden>" +
                                "                                                <button id=\"confirmbtn\" type=\"button\" class=\"btn green\"> 确认 </button>\n" +
                                "                                            </div>"
                        }
                        if (step1_state == "CONTINUE") {
                            global_end = true;

                            step1_state = "待继续";
                            expand = "collapse";
                            style = "";
                            stepbtn = "<div class=\"form-actions noborder\" style=\"text-align:center\" hidden>\n" + "<input name='step_id' id='step_id' value='" + step1_run_id + "' hidden>" +
                                "                                                <button id=\"continuebtn\" type=\"button\" class=\"btn green\"> 继续 </button>\n" +
                                "                                            </div>"
                        }

                        if (step1_state == "RUN")
                            step1_state = "运行";
                        if (step1_state == "ERROR")
                            step1_state = "错误";
                        if (step1_state == "EDIT")
                            step1_state = "未开始";
                        $("#tabdiv" + (i + 1).toString()).append("<div class=\"portlet box blue\"><div class=\"portlet-title\"><div class=\"caption\">" + step1_name + "</div><div class=\"tools\"><a href=\"javascript:;\"class=\"" + expand + "\"> </a>\n" +
                            "</div></div><div class=\"portlet-body\" " + style + "><div class=\"row\"><div ><div class=\"panel-body\"><div class=\"form-body\"><div class=\"row\"><div class=\"col-md-6\">\n" +
                            "<div class=\"form-group \"><label class=\"col-md-2 control-label\">状态</label><div class=\"col-md-10\"><input  type=\"text\" value='" + step1_state + "'\n" +
                            "class=\"form-control \" placeholder=\"\" readonly=\"\"> <div class=\"form-control-focus\"></div> </div> </div> <div class=\"form-group \"> <label class=\"col-md-2 control-label\">\n" +
                            "开始时间</label> <div class=\"col-md-10\"> <input  type=\"text\" value=\"" + step1_starttime + "\" class=\"form-control \" placeholder=\"\" readonly=\"\"> <div class=\"form-control-focus\"></div>\n" +
                            "</div> </div> <div class=\"form-group \"> <label class=\"col-md-2 control-label\">结束时间</label> <div class=\"col-md-10\"> <input  type=\"text\" value=\"" + step1_endtime + "\" class=\"form-control \" placeholder=\"\"\n" +
                            "readonly=\"\"> <div class=\"form-control-focus\"></div> </div> </div> <div class=\"form-group \"> <label class=\"col-md-2 control-label\">步骤耗时</label> <div class=\"col-md-10\">\n" +
                            "<input  type=\"text\" value=\"" + step1_rto + "\" class=\"form-control \" placeholder=\"\" readonly=\"\"> <div class=\"form-control-focus\"></div> </div> </div> <div class=\"form-group \">\n" +
                            "<label class=\"col-md-2 control-label\">负责角色</label> <div class=\"col-md-10\"> <input type=\"text\" value=\"" + step1_group + "\" class=\"form-control \"\n" +
                            "placeholder=\"\" readonly=\"\"> <div class=\"form-control-focus\"></div> </div> </div> <div class=\"form-group \"> <label class=\"col-md-2 control-label\">确认人</label>\n" +
                            "<div class=\"col-md-10\"> <input  type=\"text\" value=\"" + step1_operator + "\" class=\"form-control \" placeholder=\"\" readonly=\"\"> <div class=\"form-control-focus\"></div> </div> </div> <div class=\"form-group\">\n" +
                            "<label class=\"col-md-2 control-label\">说明</label> <div class=\"col-md-10\"> <textarea style=\"height: 100px\" value=\"" + step1_note + "\" style=\"resize:none;\" autocomplete=\"off\" class=\"form-control\" readonly=\"\"></textarea> <div class=\"form-control-focus\"></div> </div> </div></div><div id='scriptdiv_" + (i + 1).toString() + "' class=\"col-md-6\"> </div> </div>" + bar + stepbtn + " </div> </div> </div> </div> </div></div>")
                        if (data["step"][i]["scripts"].length > 0) {

                            $("#scriptdiv_" + (i + 1).toString()).append("<div class=\"form-group\"><label class=\"col-md-2 control-label\"></span>脚本</label><div class=\"col-md-10\"><select id='se" + (i + 1).toString() + "' size='9' class='form-control' style='overflow-y:auto;'></select><div class=\"form-control-focus\"></div></div></div>")
                            for (var j = 0; j < data["step"][i]["scripts"].length; j++) {
                                var color = ""
                                if (data["step"][i]["scripts"][j]["scriptstate"] == "DONE")
                                    color = "#26C281"
                                if (data["step"][i]["scripts"][j]["scriptstate"] == "RUN") {
                                    color = "#32c5d2"
                                    // // 异常异步任务处理
                                    // var process_run_id = $("#process_run_id").val();
                                    // var abnormal = "0";
                                    // getTaskStatus(process_run_id, abnormal);
                                }

                                if (data["step"][i]["scripts"][j]["scriptstate"] == "IGNORE")
                                    color = "#ffd966"
                                if (data["step"][i]["scripts"][j]["scriptstate"] == "ERROR")
                                    color = "#ff0000"
                                $("#se" + (i + 1).toString()).append("<option style='color:" + color + "' value='" + data["step"][i]["scripts"][j]["runscriptid"] + "'>" + data["step"][i]["scripts"][j]["name"] + "</option>")
                            }


                        }
                        if (data["step"][i]["verifyitems"].length > 0) {
                            $("#scriptdiv_" + (i + 1).toString()).append("<div class=\"form-group\"><label class=\"col-md-2 control-label\"></span>事项</label><div class=\"col-md-10\"><div class=\"md-checkbox-inline\" id='verifyitems_" + (i + 1).toString() + "'></div></div></div><div class=\"form-group\"><div  style='padding-top: 5px'  class=\"checkbox-list\">")
                            for (var j = 0; j < data["step"][i]["verifyitems"].length; j++) {
                                var checked = "";
                                if (data["step"][i]["verifyitems"][j]["has_verified"] == "1")
                                    checked = "checked";
                                $("#verifyitems_" + (i + 1).toString()).append("<div class=\"md-checkbox\"><input class=\"md-check\" id=\"" + data["step"][i]["verifyitems"][j]["runverifyitemid"] + "\" type=\"checkbox\" " + checked + "  /><label for=\"" + data["step"][i]["verifyitems"][j]["runverifyitemid"] + "\"><span class=\"inc\"></span><span class=\"check\"></span><span class=\"box\"></span><font style=\"vertical-align: inherit;\"><font style=\"vertical-align: inherit;\">\n" +
                                    data["step"][i]["verifyitems"][j]["name"] + "</font></font></label></div>")
                            }
                        }
                        $("#tabdiv" + (i + 1).toString()).append("<div id='tabsteps" + (i + 1).toString() + "' class='row  step-background-thin'></div><br><br>");
                        var stepallsteps = 0;
                        var stepdonesteps = 0;
                        var buttonShowId = "";
                        for (var j = 0; j < data["step"][i]["children"].length; j++) {
                            var stepdone = "";
                            if (data["step"][i]["children"][j]["state"] == "DONE")
                                stepdone = "done";
                            var steprun = "";
                            var hidediv = "hidden";
                            var style = "display:none;";
                            if (data["step"][i]["children"][j]["state"] == "RUN" || data["step"][i]["children"][j]["state"] == "CONFIRM" || data["step"][i]["children"][j]["state"] == "CONTINUE" || data["step"][i]["children"][j]["state"] == "ERROR" || ((j == data["step"][i]["children"].length - 1) && data["step"][i]["children"][j]["state"] == "DONE")) {
                                hidediv = "";
                                steprun = "active";
                                style = ""
                            }
                            $("#tabsteps" + (i + 1).toString()).append("<div id='step" + (i + 1).toString() + "_" + (j + 1).toString() + "' class='col-md-4 bg-grey-steel mt-step-col " + stepdone + " " + steprun + "' ><div class='mt-step-number'>" + (j + 1).toString() + "</div><div class='mt-step-title uppercase font-grey-cascade' style='font-size: 25px;'><i class='fa fa-hand-o-right' style='" + style + "'></i>     " + data["step"][i]["children"][j]["name"] + "</div><div class='mt-step-content font-grey-cascade'>开始时间:" + data["step"][i]["children"][j]["starttime"] + "</div><div class='mt-step-content font-grey-cascade'>结束时间:" + data["step"][i]["children"][j]["endtime"] + "</div></div>")
                            $("#tabdiv" + (i + 1).toString()).append("<div " + hidediv + " class='form-group tabdiv' id='div" + (i + 1).toString() + "_" + (j + 1).toString() + "'></div>");

                            var step2_name = data["step"][i]["children"][j]["name"];
                            var step2_run_id = data["step"][i]["children"][j]["runid"];
                            var step2_state = data["step"][i]["children"][j]["state"];
                            var step2_starttime = data["step"][i]["children"][j]["starttime"];
                            var step2_endtime = data["step"][i]["children"][j]["endtime"];
                            var step2_rto = data["step"][i]["children"][j]["rto"];
                            var step2_group = data["step"][i]["children"][j]["group"] != null ? data["step"][i]["children"][j]["group"] : "";
                            var step2_operator = data["step"][i]["children"][j]["operator"];
                            var step2_note = data["step"][i]["children"][j]["note"];
                            var step2_verify = data["step"][i]["children"][j]["verify"];
                            processallsteps = processallsteps + 1;
                            stepallsteps = stepallsteps + 1;

                            var step2btn = "";

                            if (step2_state == "DONE") {
                                step2_state = "完成";
                                processdonesteps = processdonesteps + 1;
                                stepdonesteps = stepdonesteps + 1;
                            }
                            if (step2_state == "CONFIRM") {
                                global_end = true;

                                step2_state = "待确认";
                                step2btn = "<div class=\"form-actions noborder\" style=\"text-align:center\" hidden>\n" + "<input name='step_id' id='step_id' value='" + step2_run_id + "' hidden>" +
                                    "                                                <button id=\"confirmbtn\" type=\"button\" class=\"btn green\"> 确认 </button>\n" +
                                    "                                            </div>"
                            }
                            if (step2_state == "CONTINUE") {
                                step2_state = "待继续";
                                step2btn = "<div class=\"form-actions noborder\" style=\"text-align:center\" hidden>\n" + "<input name='step_id' id='step_id' value='" + step2_run_id + "' hidden>" +
                                    "                                                <button hidden id=\"continuebtn\" type=\"button\" class=\"btn green\"> 继续 </button>\n" +
                                    "                                            </div>"
                            }

                            if (step2_state == "RUN")
                                step2_state = "运行";
                            if (step2_state == "ERROR")
                                step2_state = "错误";
                            if (step2_state == "EDIT")
                                step2_state = "未开始";
                            var stepbtn = "";
                            $("#div" + (i + 1).toString() + "_" + (j + 1).toString()).append("<div class=\"portlet box green\"><div class=\"portlet-title\"><div class=\"caption\">" + step2_name + "</div><div class=\"tools\"><a href=\"javascript:;\"class=\"collapse\"> </a>\n" +
                                "</div></div><div class=\"portlet-body\"><div class=\"row\"><div ><div class=\"panel-body\"><div class=\"form-body\"><div class=\"row\"><div class=\"col-md-6\">\n" +
                                "<div class=\"form-group \"><label class=\"col-md-2 control-label\">状态</label><div class=\"col-md-10\"><input  type=\"text\" value='" + step2_state + "'\n" +
                                "class=\"form-control \" placeholder=\"\" readonly=\"\"> <div class=\"form-control-focus\"></div> </div> </div> <div class=\"form-group \"> <label class=\"col-md-2 control-label\">\n" +
                                "开始时间</label> <div class=\"col-md-10\"> <input  type=\"text\" value=\"" + step2_starttime + "\" class=\"form-control \" placeholder=\"\" readonly=\"\"> <div class=\"form-control-focus\"></div>\n" +
                                "</div> </div> <div class=\"form-group \"> <label class=\"col-md-2 control-label\">结束时间</label> <div class=\"col-md-10\"> <input  type=\"text\" value=\"" + step2_endtime + "\" class=\"form-control \" placeholder=\"\"\n" +
                                "readonly=\"\"> <div class=\"form-control-focus\"></div> </div> </div> <div class=\"form-group \"> <label class=\"col-md-2 control-label\">步骤耗时</label> <div class=\"col-md-10\">\n" +
                                "<input  type=\"text\" value=\"" + step2_rto + "\" class=\"form-control \" placeholder=\"\" readonly=\"\"> <div class=\"form-control-focus\"></div> </div> </div> <div class=\"form-group \">\n" +
                                "<label class=\"col-md-2 control-label\">负责角色</label> <div class=\"col-md-10\"> <input type=\"text\" value=\"" + step2_group + "\" class=\"form-control \"\n" +
                                "placeholder=\"\" readonly=\"\"> <div class=\"form-control-focus\"></div> </div> </div> <div class=\"form-group \"> <label class=\"col-md-2 control-label\">确认人</label>\n" +
                                "<div class=\"col-md-10\"> <input  type=\"text\" value=\"" + step2_operator + "\" class=\"form-control \" placeholder=\"\" readonly=\"\"> <div class=\"form-control-focus\"></div> </div> </div> <div class=\"form-group\">\n" +
                                "<label class=\"col-md-2 control-label\">说明</label> <div class=\"col-md-10\"> <textarea style=\"height: 100px\" value=\"" + step2_note + "\" style=\"resize:none;\" autocomplete=\"off\" class=\"form-control\" readonly=\"\"></textarea> <div class=\"form-control-focus\"></div> </div> </div></div><div id='scriptdiv_" + (i + 1).toString() + "_" + (j + 1).toString() + "' class=\"col-md-6\"> </div> </div>" + step2btn + " </div> </div> </div> </div> </div></div>")

                            if (data["step"][i]["children"][j]["scripts"].length > 0) {
                                $("#scriptdiv_" + (i + 1).toString() + "_" + (j + 1).toString()).append("<div class=\"form-group\"><label class=\"col-md-2 control-label\"></span>脚本</label><div class=\"col-md-10\"><select id='se" + (i + 1).toString() + "_" + (j + 1).toString() + "' size='9' class='form-control' style='overflow-y:auto;'></select><div class=\"form-control-focus\"></div></div></div>")
                                for (var k = 0; k < data["step"][i]["children"][j]["scripts"].length; k++) {
                                    var color = "";
                                    if (data["step"][i]["children"][j]["scripts"][k]["scriptstate"] == "DONE")
                                        color = "#26C281";
                                    if (data["step"][i]["children"][j]["scripts"][k]["scriptstate"] == "RUN") {
                                        color = "#32c5d2";
                                        // // 异常异步任务处理
                                        // var process_run_id = $("#process_run_id").val();
                                        // var abnormal = "0";
                                        // getTaskStatus(process_run_id, abnormal);
                                    }
                                    if (data["step"][i]["children"][j]["scripts"][k]["scriptstate"] == "IGNORE")
                                        color = "#ffd966";
                                    if (data["step"][i]["children"][j]["scripts"][k]["scriptstate"] == "ERROR")
                                        color = "#ff0000";
                                    $("#se" + (i + 1).toString() + "_" + (j + 1).toString()).append("<option style='color:" + color + "' value='" + data["step"][i]["children"][j]["scripts"][k]["runscriptid"] + "'>" + data["step"][i]["children"][j]["scripts"][k]["name"] + "</option>")
                                }


                            }
                            if (data["step"][i]["children"][j]["verifyitems"].length > 0) {
                                $("#scriptdiv_" + (i + 1).toString() + "_" + (j + 1).toString()).append("<div class=\"form-group\"><label class=\"col-md-2 control-label\"></span>事项</label><div class=\"col-md-10\"><div class=\"md-checkbox-inline\" id='verifyitems_" + (i + 1).toString() + "_" + (j + 1).toString() + "'></div></div></div><div class=\"form-group\"><div  style='padding-top: 5px'  class=\"checkbox-list\">")
                                for (var k = 0; k < data["step"][i]["children"][j]["verifyitems"].length; k++) {
                                    var checked = "";
                                    if (data["step"][i]["children"][j]["verifyitems"][k]["has_verified"] == "1")
                                        checked = "checked";
                                    $("#verifyitems_" + (i + 1).toString() + "_" + (j + 1).toString()).append("<div class=\"md-checkbox\"><input class=\"md-check\" id=\"" + data["step"][i]["children"][j]["verifyitems"][k]["runverifyitemid"] + "\" type=\"checkbox\" " + checked + "  /><label for=\"" + data["step"][i]["children"][j]["verifyitems"][k]["runverifyitemid"] + "\"><span class=\"inc\"></span><span class=\"check\"></span><span class=\"box\"></span><font style=\"vertical-align: inherit;\"><font style=\"vertical-align: inherit;\">\n" +
                                        data["step"][i]["children"][j]["verifyitems"][k]["name"] + "</font></font></label></div>")
                                }
                            }
                        }

                        try {
                            var stepbar = "0";
                            stepbar = Math.round(stepdonesteps / stepallsteps * 100).toString();
                            $("#step_bar_" + (i + 1).toString()).width(stepbar + "%");
                        } catch (err) {

                        }


                    }

                    // $("ul.steps").append("<ul class='nav nav-pills nav-justified steps'>" + innerUl + "</ul>");

                    // 展示确认按钮
                    $("#confirmbtn").parent().show();
                    // 展示继续按钮
                    $("#continuebtn").parent().show();

                    try {
                        var processbar = "0";
                        processbar = Math.round(processdonesteps / processallsteps * 100).toString();
                        $("#process_bar").width(processbar + "%");
                    } catch (err) {

                    }
                    FormWizard.init();

                    $(".mt-step-col").click(function () {
                        $(".tabdiv").hide();
                        $("#" + this.id.replace('step', 'div')).show();
                        $(".mt-step-col").removeClass("active");
                        $("#" + this.id).addClass("active");
                        $(".mt-step-col" + " i").hide();
                        $("#" + this.id + " i").show();
                    });
                    $('select').dblclick(function () {

                        if ($(this).find('option:selected').length == 0) {
                            alert("请至少选中一个脚本。")

                        } else {
                            if ($(this).find('option:selected').length > 1) {
                                alert("请不要选择多条记录。");
                            } else {
                                $("#exec").hide();
                                $("#ignore").hide();

                                $("#static").modal({backdrop: "static"});
                                $("#script_button").val($(this).find('option:selected').val());
                                // 获取当前步骤脚本信息
                                var steprunid = "0";
                                var scriptid = $(this).find('option:selected').val();
                                $.ajax({
                                    url: "/get_current_scriptinfo/",
                                    type: "post",
                                    data: {"steprunid": steprunid, "scriptid": scriptid},
                                    success: function (data) {
                                        $("#steprunid").val(scriptid);
                                        $("#code").val(data.data["code"]);
                                        $("#script_ip").val(data.data["ip"]);
                                        $("#script_port").val(data.data["port"]);
                                        $("#filename").val(data.data["filename"]);
                                        $("#scriptpath").val(data.data["scriptpath"]);
                                        $("#scriptstate").val(data.data["state"]);
                                        $("#ontime").val(data.data["starttime"]);
                                        $("#offtime").val(data.data["endtime"]);
                                        $("#errorinfo").val(data.data["explain"]);
                                        if (data.data["state"] == "执行失败" && data.data["processrunstate"] == "ERROR") {
                                            $("#exec").show();
                                            $("#ignore").show();
                                        } else {
                                            $("#exec").hide();
                                            $("#ignore").hide();
                                        }
                                        if (data.data["show_log_btn"] == "1") {
                                            $("#show_log").show();
                                        } else {
                                            $("#show_log").hide();
                                        }
                                    }
                                });
                            }
                        }

                    });


                    // 确认
                    $("#confirmbtn").click(function () {
                        /*
                            多个确认项处理：
                                verify_run_id

                         */
                        var verify_array = [];
                        var verify_els = $("#confirmbtn").parent().prev().find('div[id^="verifyitems_"]').find('input');
                        verify_els.each(function (index, element) {
                            if (element.checked == true) {
                                verify_array.push(element.id);
                            }
                        });

                        var step_id = $(this).prev().val();
                        var notChecked = "";
                        $(this).parent().siblings().find("input[type='checkbox']:not(:checked)").each(function (index, element) {
                            notChecked += $(this).parent().text() + ",";
                        });
                        if (notChecked) {
                            if (confirm("data未勾选，是否继续？".replace("data", notChecked.slice(0, notChecked.length - 1)))) {
                                $.ajax({
                                    url: "/verify_items/",
                                    type: "post",
                                    data: {
                                        "verify_array": JSON.stringify(verify_array),
                                        "step_id": step_id,
                                    },
                                    success: function (data) {
                                        if (data.data == "0") {
                                            alert("该步骤已确认，请继续流程！");
                                            getstep();
                                            global_end = false;
                                            customOurInterval();
                                            getTaskInfo();
                                        } else {
                                            alert("步骤确认异常，请联系客服！")
                                        }
                                    }
                                });
                            }
                        } else {
                            $.ajax({
                                url: "/verify_items/",
                                type: "post",
                                data: {
                                    "verify_array": JSON.stringify(verify_array),
                                    "step_id": step_id,
                                },
                                success: function (data) {
                                    if (data.data == "0") {
                                        alert("该步骤已确认，请继续流程！");
                                        getstep();
                                        // 确认流程之后再次开启定时器
                                        global_end = false;
                                        customOurInterval();
                                        getTaskInfo();
                                    } else {
                                        alert("步骤确认异常，请联系客服！")
                                    }
                                }
                            });
                        }

                    });

                    // 继续
                    $("#continuebtn").click(function () {
                        var step_id = $(this).prev().val();
                        $.ajax({
                            url: "/processcontinue/",
                            type: "post",
                            data: {
                                "step_id": step_id,
                            },
                            success: function (data) {
                                if (data.data == "0") {
                                    alert("流程已继续运行！");
                                    getstep();
                                    global_end = false;
                                    customOurInterval();
                                    getTaskInfo();
                                } else {
                                    alert("步骤确认异常，请联系客服！")
                                }
                            }
                        });
                    });

                    // 展示结果
                    $("#show_result").click(function () {
                        $("#process_result").modal({backdrop: "static"});

                        showResult();
                    });
                    // 展示任务信息
                    $("#show_tasks").click(function () {
                        $("#static_tasks").modal({backdrop: "static"});
                        customTasksTable();
                    });
                }
            });
        }

        // 重试
        $('#exec').click(function () {
            $("#confirmbtn").parent().empty();
            $("#continuebtn").parent().empty()
            $.ajax({
                type: "POST",
                dataType: 'json',
                url: "../../falconstorcontinue/",
                data:
                    {
                        process: $('#process').val(),
                    },
                success: function (data) {
                    if (data["res"] == "执行成功。") {
                        $("#exec").hide();
                        $("#ignore").hide();
                        $('#static').modal('hide');
                        // 重启定时器
                        global_end = false;
                        customOurInterval();
                    } else
                        alert(data["res"]);
                },
                error: function (e) {
                    alert("执行失败，请于管理员联系。");
                }
            });
        });

        // 跳过脚本
        $("#ignore").click(function () {
            $("#confirmbtn").parent().empty();
            $("#continuebtn").parent().empty();
            var scriptid = $("#script_button").val();
            $.ajax({
                url: "../../ignore_current_script/",
                type: "post",
                data: {"scriptid": scriptid},
                success: function (data) {
                    alert(data.data);
                    $('#static').modal('hide');
                    // 重启定时器
                    global_end = false;
                    customOurInterval();
                }
            });
        });


        // 展示错误日志
        $("#show_log").click(function () {
            $("#static_log").modal({backdrop: "static"});
            $("#log_info").val("");
            var scriptRunId = $("#script_button").val();
            $.ajax({
                url: "../../get_script_log/",
                type: "post",
                data: {
                    "scriptRunId": scriptRunId
                },
                success: function (data) {
                    if (data["res"] == "1") {
                        $("#log_info").val(data["log_info"])
                    } else {
                        alert(data["log_info"])
                    }
                }
            });
        });

        // 终止定时器的判断
        var end = false;

        function get_force_script_info() {
            // [script_name], [script_status]
            // 脚本全部执行完毕之后，刷新步骤
            $.ajax({
                url: "../../get_force_script_info/",
                type: "post",
                data: {
                    "process": $("#process").val()
                },
                success: function (data) {
                    if (data.ret == 1) {
                        $("#script_name_div").empty();
                        $("#script_status_div").empty();

                        for (var i = 0; i < data.data.script_name_list.length; i++) {
                            $("#script_name_div").append('<label class="control-label col-md-12" style="text-align: left;">' + data.data.script_name_list[i] + '</label>')
                        }
                        for (var i = 0; i < data.data.script_status_list.length; i++) {
                            var script_icon = "",
                                script_color = "";
                            if (data.data.script_status_list[i] == "DONE") {
                                script_icon = "fa fa-check";
                                script_color = "color:#26C281;"
                            } else if (data.data.script_status_list[i] == "ERROR") {
                                script_icon = "fa fa-times";
                                script_color = "color:#c51b26;"
                            } else {
                                script_icon = "fa fa-circle-o";
                                script_color = ""
                            }
                            $("#script_status_div").append('<div class="control-label col-md-12"><i class="' + script_icon + '" style="' + script_color + '"></i></div>')
                        }
                        if (data.data.finish == 1) {
                            // 强制执行脚本完成,关闭定时器
                            $('#static_force_script').modal("hide");
                            alert("强制执行脚本完成。");
                            end = true;
                            // 跳转启动页面
                            // window.location.href = data.data.switch_url;
                        }
                    } else {
                        // 不作为
                        console.log(data.data);
                    }
                }
            });
        }

        /*
            刷新页面，如何弹出模态框？
            这时定时器还未启动
            给已终止的流程提供展示模态框的按钮:显示强制执行脚本
         */
        $("#show_force_script").click(function () {
            $('#static_force_script').modal("show");
        });

        // 启动模态框时先查询状态，再开启定时器
        $('#static_force_script').on('show.bs.modal', function () {
            // 有脚本分组：修改状态
            // 无脚本分组：构建分组，添加状态
            get_force_script_info();

            // 3.定时任务
            setTimeout(function () {
                if (!end) {
                    // do something 定时任务
                    // 处理时对end标志进行修改，end=True表示停止（取消定时器）。
                    get_force_script_info();

                    // 循环(arguments.callee获取当前执行函数的引用)
                    setTimeout(arguments.callee, 4000);
                } else {
                    end = false;
                }
            }, 4000);
        });

        // 关闭模态框时reload
        $('#static_force_script').on('hide.bs.modal', function () {
            getstep();
        });

        // 终止流程
        $("#stopbtn").click(function () {
            $("#confirmbtn").parent().empty();
            $("#continuebtn").parent().empty();

            if ($("#process_note").val() == "")
                alert("请在说明项目输入停止原因！");
            else {
                if (confirm("即将终止本次演练，注意，此操作不可逆！是否继续？")) {
                    var process_run_id = $("#process_run_id").val();

                    /*
                        弹出模态框：
                            弹出所有包含强制执行的步骤下的脚本，script_run_id，script_run_name~~ 仅在弹出模态框时展示.
                        开启定时任务：
                            执行完成--弹出提示框
                            未完成  --修改脚本执行状态 √/×
                        窗口关闭后，再次开启：
                            根据是否有该异步任务存在，存在则弹出模态框
                        终止当前流程的异步任务
                     */
                    // 2.终止任务，开启新的强制任务
                    $.ajax({
                        url: "../../stop_current_process/",
                        type: "post",
                        data: {
                            "process_run_id": process_run_id,
                            "process_note": $("#process_note").val(),
                        },
                        success: function (data) {
                            // 停止定时器
                            global_end = true;

                            alert(data.data);
                            // 1.模态框
                            $("#static_force_script").modal("show");
                            // 3.终止当前流程的异步任务
                            var process_run_id = $("#process_run_id").val();
                            var abnormal = "2";
                            $.ajax({
                                url: "../../revoke_current_task/",
                                type: "post",
                                data: {
                                    "process_run_id": process_run_id,
                                    "abnormal": abnormal,
                                },
                                success: function (data) {
                                    // 不做处理
                                    console.log("终止当前流程异步任务。")
                                }
                            });
                        }
                    });
                }
            }
        });

        // 撤销当前任务
        $("#revoke_current_task").click(function () {
            if (confirm("即将撤销当前任务，注意，此操作不可逆！是否继续？")) {
                var process_run_id = $("#process_run_id").val();
                var abnormal = "1";
                getTaskStatus(process_run_id, abnormal);
            }
        });

        // 刷新异步任务
        $("#tasks_fresh").click(function () {
            customTasksTable();
        });

        // 说明字段的聚焦于取消聚焦
        $("#process_note").focus(function () {
            global_end = true;
        });

        $("#process_note").blur(function () {
            global_end = false;
            customOurInterval();
        });

    });
}
