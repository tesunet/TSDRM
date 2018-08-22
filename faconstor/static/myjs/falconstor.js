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
                    $('#form_wizard_1').find('.progress-bar').css({
                        width: $percent + '%'
                    });
                }
            });


        }

    };

}();

if (App.isAngularJsApp() === false) {
    jQuery(document).ready(function () {
        var t1 = window.setTimeout(getstep, 1000);
        var t2 = window.setInterval(timefun, 1000);
        var num = 0;
        var isinit = true;
        $(document).on('click', function () {
            num = 0;
        });

        function timefun() {
            var strUrl = window.location.href;
            if (strUrl.indexOf("falconstor") > -1) {
                num++;
                if (num >= 15) {
                    $('#form_wizard_1').removeData('bootstrapWizard');
                    getstep();
                    num = 0;
                }
            }
            else {
                window.clearInterval(t2);
            }
        }

        function getstep() {
            $.ajax({
                type: "POST",
                url: "../../getrunsetps/",
                data:
                    {
                        process: $("#process").val()
                    },
                dataType: "json",
                success: function (data) {
                    $("#continue").hide();
                    $("ul.steps").empty();
                    $("div.tab-content").empty();
                    for (var i = 0; i < data.length; i++) {
                        var first = ""
                        var last = ""
                        if (i == 0)
                            first = "first"
                        if (i == data.length - 1)
                            last = "last"
                        if (data[i]["state"] == "ERROR")
                            $("#continue").show();
                        var tabdone = ""
                        if (data[i]["state"] == "DONE")
                            tabdone = "done"
                        var tabrun = ""
                        if (data[i]["state"] == "RUN" || data[i]["state"] == "ERROR" || ((i == data.length - 1) && data[i]["state"] == "DONE"))
                            tabrun = "active"
                        if (data[i]["state"] == "ERROR" || ((i == data.length - 1) && data[i]["state"] == "DONE"))
                            window.clearInterval(t2);
                        $("ul.steps").append("<li id='li_" + (i + 1).toString() + "' class='" + tabdone + " " + tabrun + "'><a href='#tab" + (i + 1).toString() + "' data-toggle='tab' class='step' aria-expanded='true'><span class='number'> " + (i + 1).toString() + " </span><span class='desc'><i hidden class='fa fa-check'></i> " + data[i]["name"] + " </span></a></li>")
                        $("div.tab-content").append("<div class='tab-pane " + tabrun + "' id='tab" + (i + 1).toString() + "'></div>")
                        if (data[i]["children"].length > 0) {
                            $("#tab" + (i + 1).toString()).append("<div id='tabdiv" + (i + 1).toString() + "' class='mt-element-step'><div id='tabsteps" + (i + 1).toString() + "' class='row  step-background-thin'></div><br><br></div>")
                            for (var j = 0; j < data[i]["children"].length; j++) {
                                var stepdone = ""
                                if (data[i]["children"][j]["state"] == "DONE")
                                    stepdone = "done"
                                var steprun = ""
                                var hidediv = "hidden"
                                var style = "display:none;"
                                if (data[i]["children"][j]["state"] == "RUN" || data[i]["children"][j]["state"] == "ERROR" || ((j == data[i]["children"].length - 1) && data[i]["children"][j]["state"] == "DONE")) {
                                    hidediv = ""
                                    steprun = "active"
                                    style = ""
                                }
                                $("#tabsteps" + (i + 1).toString()).append("<div id='step" + (i + 1).toString() + "_" + (j + 1).toString() + "' class='col-md-4 bg-grey-steel mt-step-col " + stepdone + " " + steprun + "'><div class='mt-step-number'>" + (j + 1).toString() + "</div><div class='mt-step-title uppercase font-grey-cascade'><i class='fa fa-hand-o-right' style='" + style + "'></i>     " + data[i]["children"][j]["name"] + "</div><div class='mt-step-content font-grey-cascade'>开始时间:" + data[i]["children"][j]["starttime"] + "</div><div class='mt-step-content font-grey-cascade'>结束时间:" + data[i]["children"][j]["endtime"] + "</div></div>")

                                $("#tabdiv" + (i + 1).toString()).append("<div " + hidediv + " class='form-group tabdiv' id='div" + (i + 1).toString() + "_" + (j + 1).toString() + "'><div class='col-md-12'><select id='se" + (i + 1).toString() + "_" + (j + 1).toString() + "' size='7' class='form-control' style='overflow-y:auto;'></select></div></div>")
                                for (var k = 0; k < data[i]["children"][j]["scripts"].length; k++) {
                                    var color = ""
                                    if (data[i]["children"][j]["scripts"][k]["scriptstate"] == "DONE")
                                        color = "#26C281"
                                    if (data[i]["children"][j]["scripts"][k]["scriptstate"] == "RUN")
                                        color = "#32c5d2"
                                    if (data[i]["children"][j]["scripts"][k]["scriptstate"] == "IGNORE")
                                        color = "#ffd966"
                                    if (data[i]["children"][j]["scripts"][k]["scriptstate"] == "ERROR")
                                        color = "#ff0000"
                                    $("#se" + (i + 1).toString() + "_" + (j + 1).toString()).append("<option style='color:" + color + "' value='" + data[i]["children"][j]["scripts"][k]["runscriptid"] + "'>" + data[i]["children"][j]["scripts"][k]["name"] + "</option>")
                                }
                            }
                        }
                        else {
                            $("#tab" + (i + 1).toString()).append("<div class='col-md-12'><select id='se" + (i + 1).toString() + "' size='7' class='form-control' style='overflow-y:auto;'></select><br><br></div>")
                            for (var j = 0; j < data[i]["scripts"].length; j++) {
                                var color = ""
                                if (data[i]["scripts"][j]["scriptstate"] == "DONE")
                                    color = "#26C281"
                                if (data[i]["scripts"][j]["scriptstate"] == "RUN")
                                    color = "#32c5d2"
                                if (data[i]["scripts"][j]["scriptstate"] == "IGNORE")
                                    color = "#ffd966"
                                if (data[i]["scripts"][j]["scriptstate"] == "ERROR")
                                    color = "#ff0000"
                                $("#se" + (i + 1).toString()).append("<option style='color:" + color + "' value='" + data[i]["scripts"][j]["runscriptid"] + "'>" + data[i]["scripts"][j]["name"] + "</option>")
                            }
                        }
                    }
                    FormWizard.init();

                    $(".mt-step-col").click(function () {
                        $(".tabdiv").hide()
                        $("#" + this.id.replace('step', 'div')).show()
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
                                $("#b1").hide();
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
                                        if (data.data["state"] == "执行中" || data.data["state"] == "执行失败") {
                                            $("#b1").show();
                                        } else {
                                            $("#b1").hide();
                                        }
                                    }
                                });
                            }
                        }

                    });

                    // 继续
                    $('#exec').click(function () {
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
                                    $('#continue').hide()
                                }
                                else
                                    alert(data["res"]);
                            },
                            error: function (e) {
                                alert("执行失败，请于管理员联系。");
                            }
                        });
                    })

                    // 跳过脚本
                    $("#ignore").click(function () {
                        var scriptid = $("#script_button").val();
                        $.ajax({
                            url: "/ignore_current_script/",
                            type: "post",
                            data: {"scriptid": scriptid},
                            success: function (data) {
                                alert(data.data);
                                $('#static').modal('hide');
                            }
                        });
                    });
                }
            });
        }
    });
}