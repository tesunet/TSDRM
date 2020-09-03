$("ul#locate").on("click", " li", function () {
    var job_id = $(this).attr("id");
    $("input#clientname").val($("#a".replace("a", job_id)).find("input#clientname_tag").val());
    $("input#idataagent").val($("#a".replace("a", job_id)).find("input#idataagent_tag").val());
    $("input#enddate").val($("#a".replace("a", job_id)).find("input#enddate_tag").val());
    $("textarea#jobfailedreason").text($("#a".replace("a", job_id)).find("input#jobfailedreason_tag").val());
    $("input#jobid").val(job_id);
});


function getframeworkstate() {
    $("#url_util").click(function () {
        window.open("/framework?util=" + $("#util").val());
    });
    $.ajax({
        type: 'POST',
        dataType: 'json',
        url: '../get_frameworkstate/',
        data: {
            "util": $('#util').val(),
        },
        success: function (data) {
            if (data.data == 0) {
                $('#frameworkstate').text("正常")
                $("#frameworkstate").css("color", "white");
            } else if (data.data == 1) {
                $('#frameworkstate').text("警告")
                $("#frameworkstate").css("color", "yellow");

            } else if (data.data == 2) {
                $('#frameworkstate').text("错误")
                $("#frameworkstate").css("color", "red");
            }
        }
    });
}

function getclientnum() {
    $("#url_allclient").click(function () {
        window.open("/client_list?util=" + $("#util").val());
    });
    $("#url_wnclient").click(function () {
        window.open("/client_list?util=" + $("#util").val());
    });
    $.ajax({
        type: 'POST',
        dataType: 'json',
        url: '../get_backup_status/',
        data: {

            'utils_manage_id': $("#util").val(),
        },
        success: function (data) {
            if (data.ret == 0) {
                alert(data.data)
            } else {
                // 报警客户端
                var all_client_num = 0;
                var warning_client_num = 0;
                var allclientlist = []
                var warningclientlist = []
                var whole_list = data.data;

                // 加载数据
                var content_el = ''
                for (var i = 0; i < whole_list.length; i++) {
                    if (allclientlist.indexOf(whole_list[i]["clientname"]) == -1) {
                        allclientlist.push(whole_list[i]["clientname"]);
                    }
                    if (whole_list[i]["bk_status"].indexOf("失败") != -1 && warningclientlist.indexOf(whole_list[i]["clientname"]) == -1) {
                        warningclientlist.push(whole_list[i]["clientname"]);
                    }
                }
                var all_client_num = allclientlist.length;
                var warning_client_num = warningclientlist.length;

                $("#all_client_num").text(all_client_num)
                $("#warning_client_num").text(warning_client_num)
                if (warning_client_num > 0) {
                    $("#warning_client_num").css("color", "red");
                }

            }
        }
    });
}

function getsla() {
    $("#url_sla").click(function () {
        window.open("/sla?util=" + $("#util").val());
    });
    $.ajax({
        type: 'POST',
        dataType: 'json',
        url: '../get_cv_sla/',
        data: {

            'utils_manage_id': $("#util").val(),
        },
        success: function (data) {
            if (data.ret == 0) {
                alert(data.data)
            } else {
                var backup_sla = data.data;

                var policynum = 0;
                var statenum = 0;
                var rponum = 0;
                var percentnum = 0;
                var healthnum = 0;
                var curclientname = "";
                var curclientsla = "";
                for (var i = 0; i < backup_sla.length; i++) {
                    var cur_policy = false
                    var cur_state = false
                    var cur_rpo = false
                    var cur_percent = false


                    if (backup_sla[i]["policy"] == "未配置") {
                        cur_policy = true
                    }
                    if (["运行", "正常", "等待", "QueuedCompleted", "Queued", "成功", "部分完成", "PartialSuccess", "阻塞", "已完成，但有一个或多个错误", "已完成，但有一个或多个警告"].indexOf(backup_sla[i]["bk_status"]) == -1) {
                        cur_state = true
                    }
                    if (backup_sla[i]["rposec"] == 0 || 604800 && backup_sla[i]["rposec"] > 2592000) {
                        cur_rpo = true
                    }
                    if (backup_sla[i]["percent"] < 50) {
                        cur_percent = true
                    }


                    if (curclientname != backup_sla[i]["clientname"]) {
                        if (curclientname != "") {
                            if (curclientsla == "policy") {
                                policynum++;
                            } else if (curclientsla == "state") {
                                statenum++;
                            } else if (curclientsla == "rpo") {
                                rponum++;
                            } else if (curclientsla == "percent") {
                                percentnum++;
                            } else {
                                healthnum++;
                            }
                        }
                        curclientsla = ""
                        curclientname = backup_sla[i]["clientname"]
                        if (cur_policy) {
                            curclientsla = "policy"
                        } else if (cur_state) {
                            curclientsla = "state"
                        } else if (cur_rpo) {
                            curclientsla = "rpo"
                        } else if (cur_percent) {
                            curclientsla = "percent"
                        } else {
                            curclientsla = "health"
                        }
                    } else {
                        if (cur_policy) {
                            curclientsla = "policy"
                        } else if (cur_state) {
                            if (curclientsla != "policy") {
                                curclientsla = "state"
                            }
                        } else if (cur_rpo) {
                            if (curclientsla != "policy" && curclientsla != "state") {
                                curclientsla = "rpo"
                            }
                        } else if (cur_percent) {
                            if (curclientsla != "policy" && curclientsla != "state" && curclientsla != "rpo") {
                                curclientsla = "percent"
                            }
                        }
                    }
                }
                if (curclientname != "") {
                    if (curclientsla == "policy") {
                        policynum++;
                    } else if (curclientsla == "state") {
                        statenum++;
                    } else if (curclientsla == "rpo") {
                        rponum++;
                    } else if (curclientsla == "percent") {
                        percentnum++;
                    } else {
                        healthnum++;
                    }
                }
                var score = 0;
                try {
                    score = healthnum / (policynum + statenum + rponum + percentnum + healthnum) * 100
                    score = score.toFixed(0)
                } catch (e) {

                }
                $("#sla_score").text(score)
                if (score < 60) {
                    $("#sla_score").css("color", "red");
                } else if (score < 80) {
                    $("#sla_score").css("color", "sandybrown");
                }
            }
        }
    });
}

function getdashboard() {
    $("#url_cv_joblist").click(function () {
        window.open("/cv_joblist?util=" + $("#util").val());
    });
    $("#url_display_error_job").click(function () {
        window.open("/display_error_job?util=" + $("#util").val());
    });
    $('#loading1').show();
    $('#loading2').show();
    $('#backup_info').hide();
    $('#show_jobstatus_num').hide();
    $.ajax({
        type: 'POST',
        dataType: 'json',
        url: '../get_dashboard/',
        data: {
            "util": $('#util').val(),
        },
        success: function (data) {
            $('#loading1').hide();
            $('#loading2').hide();
            $('#backup_info').show();
            $('#show_jobstatus_num').show();
            if (data.ret == 0) {
                alert(data.data)
            } else {
                $("#job_run_num").append('<span class="widget-thumb-subtitle">运行中</span>\n' +
                    '<span  class="widget-thumb-body-stat" data-counter="counterup" data-value="7,644">' + data.show_job_status_num['job_run_num'] + '</span>')
                $("#job_success_num").append('<span class="widget-thumb-subtitle">成功</span>\n' +
                    '<span  class="widget-thumb-body-stat" data-counter="counterup" data-value="7,644">' + data.show_job_status_num['job_success_num'] + '</span>')
                $("#job_warn_num").append('<span class="widget-thumb-subtitle">警告</span>\n' +
                    '<span  class="widget-thumb-body-stat" data-counter="counterup" data-value="7,644">' + data.show_job_status_num['job_warn_num'] + '</span>')
                $("#job_failed_num").append('<span class="widget-thumb-subtitle">失败</span>\n' +
                    '<span  class="widget-thumb-body-stat" data-counter="counterup" data-value="7,644">' + data.show_job_status_num['job_failed_num'] + '</span>')

                for (i = 0; i < data.error_job_list.length; i++) {
                    $("#locate").append('<li id="' + data.error_job_list[i].jobid + '">\n' +
                        '    <div class="col1">\n' +
                        '        <div class="cont">\n' +
                        '            <div class="cont-col1">\n' +
                        '                <div class="label label-sm label-info">\n' +
                        '                    <i class="fa fa-bullhorn"></i>\n' +
                        '                </div>\n' +
                        '            </div>\n' +
                        '            <div class="cont-col2">\n' +
                        '                <div class="desc">\n' +
                        '                    <a href="#" data-toggle="modal" data-target="#static">\n' +
                        '                        <span class="label label-sm label-success">' +  data.error_job_list[i].enddate  + '</span> \n' +
                        '                        <span>' +
                        '                            <font style="vertical-align: inherit;">\n' +
                        '                                <font style="vertical-align: inherit;">' + data.error_job_list[i].jobfailedreason + '</font>\n' +
                        '                            </font>\n' +
                        '                        </span>\n' +
                        '                    </a>\n' +
                        '                    <input hidden id="clientname_tag" type="text" value="' + data.error_job_list[i].clientname + '">\n' +
                        '                    <input hidden id="idataagent_tag" type="text" value="' + data.error_job_list[i].idataagent + '">\n' +
                        '                    <input hidden id="enddate_tag" type="text" value="' + data.error_job_list[i].enddate + '">\n' +
                        '                    <input hidden id="jobfailedreason_tag" type="text" value="' + data.error_job_list[i].jobfailedreason + '">\n' +
                        '                </div>\n' +
                        '            </div>\n' +
                        '        </div>\n' +
                        '    </div>\n' +
                        '</li>')
                }
            }

        }
    });
}




$(document).ready(function () {
    getframeworkstate();
    getclientnum();
    getsla();
    getdashboard();
    $("#util").change(function () {
        getframeworkstate();
        getclientnum();
        getsla();
        getdashboard();
        getAgentSpace($(this).val());
        getBackupSpace($(this).val());
    });


    var Dashboard = function () {

        return {
            componentsKnobDials: function () {
                //knob does not support ie8 so skip it
                if (!jQuery().knob || App.isIE8()) {
                    return;
                }

                // general knob
                $(".knob").knob({
                    'dynamicDraw': true,
                    'thickness': 0.2,
                    'tickColorizeValues': true,
                    'skin': 'tron'
                });
            },

            init: function () {
                this.componentsKnobDials();
            }
        };

    }();

    if (App.isAngularJsApp() === false) {
        jQuery(document).ready(function () {
            Dashboard.init(); // init metronic core componets
        });
    }


    /*
    TOP 5 客户端应用程序大小
     */
    function getAgentSpace(util){
        $('#loading4').show();
        $('#app_space_div').hide();
        $.ajax({
            type: "POST",
            dataType: "JSON",
            url: "../get_top5_app_capacity/",
            data: {
                "util": util,
            },
            success: function (data) {
                $('#loading4').hide();
                $('#app_space_div').show();
                var top5_data = eval(data.data)
                $('#tb_top5').empty();
                for (var i = 0; i < top5_data.length; i++) {
                    if (i > 5) {
                        break;
                    }
                    $('#tb_top5').append('<tr>\n' +
                        '    <td> ' + top5_data[i].client_name + '</td>\n' +
                        '    <td> ' + top5_data[i].app_capacity + ' TB </td>\n' +
                        '</tr>')
                }
            }
        });
    }
    getAgentSpace($("#util").val());
    /*
    备份空间使用情况
     */
    function getBackupSpace(util){
        $('#loading3').show();
        $('#disk_space_div').hide();
        $.ajax({
            type: "POST",
            dataType: "JSON",
            url: "../get_ma_disk_space/",
            data: {
                "util": util
            },
            success: function (data) {
                $('#loading3').hide();
                $('#disk_space_div').show();
                var disk_space = data.data;
                $('#ma_disk_space input').eq(0).val(disk_space["used_space_percent"].toFixed(0)).trigger('change');
                $('#ma_disk_space h4').eq(1).text(disk_space["used_space"] + " TB/" + disk_space["total_space"] + " TB")
    
                // href
                $("#a_bk_space").attr("href", data.data["bk_space_href"]);
                $("#a_top5").attr("href", data.data["client_list_href"]);
            }
        });
    }
    getBackupSpace($("#util").val());
});








