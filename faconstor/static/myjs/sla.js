$(document).ready(function () {
    $("#loading").show();


    function getSla(utils_manage_id) {
        $.ajax({
            type: 'POST',
            dataType: 'json',
            url: '../get_cv_sla/',
            data: {
                'utils_manage_id': utils_manage_id
            },
            success: function (data) {
                if (data.ret == 0) {
                    alert(data.data)
                } else {
                    var backup_sla = data.data;

                    var pre_clientname = "";
                    var pre_idataagent = "";
                    var pre_type = "";
                    var sort = 0;
                    var policynum = 0;
                    var statenum = 0;
                    var rponum = 0;
                    var percentnum = 0;
                    var healthnum = 0;
                    var curclientname="";
                    var curclientsla="";
                    for (var i = 0; i < backup_sla.length; i++) {
                        var cur_policy = false
                        var cur_state = false
                        var cur_rpo = false
                        var cur_percent = false


                        var clientname_hidden = "";
                        var idataagent_hidden = "";
                        var type_hidden = "";

                        if (pre_clientname == backup_sla[i]["clientname"]) {
                            // 非首个客户端
                            clientname_hidden = "display:none";
                        } else {
                            sort += 1;
                        }
                        if (pre_clientname == backup_sla[i]["clientname"] && pre_idataagent == backup_sla[i]["idataagent"]) {
                            idataagent_hidden = "display:none";
                        }
                        if (pre_clientname == backup_sla[i]["clientname"] && pre_idataagent == backup_sla[i]["idataagent"] && pre_type == backup_sla[i]["type"]) {
                            type_hidden = "display:none";
                        }

                        var result = "";
                        result += '<tr>' +
                            '<td rowspan="' + backup_sla[i].clientname_rowspan + '" style="vertical-align:middle; ' + clientname_hidden + '">' + sort + '</td>' +
                            '<td rowspan="' + backup_sla[i].clientname_rowspan + '" style="vertical-align:middle; ' + clientname_hidden + '">' + backup_sla[i]["clientname"] + '</td>' +
                            '<td rowspan="' + backup_sla[i].idataagent_rowspan + '" style="vertical-align:middle; ' + idataagent_hidden + '">' + backup_sla[i]["idataagent"] + '</td>' +
                            '<td rowspan="' + backup_sla[i].type_rowspan + '" style="vertical-align:middle; ' + type_hidden + '">' + backup_sla[i]["type"] + '</td>' +
                            '<td style="vertical-align:middle">' + backup_sla[i]["subclient"] + '</td>'
                        if (backup_sla[i]["policy"] == "未配置") {
                            result += "<td style='vertical-align:middle;color: red'>" + backup_sla[i]["policy"] + "</td>";
                            cur_policy = true
                        } else
                            result += "<td style='vertical-align:middle;color: green'>" + backup_sla[i]["policy"] + "</td>";

                        if (["运行", "正常", "等待", "QueuedCompleted", "Queued", "成功"].indexOf(backup_sla[i]["bk_status"]) != -1) {
                            result += "<td style='vertical-align:middle;color: green'>" + backup_sla[i]["bk_status"] + "</td>";
                        } else if (["部分完成", "PartialSuccess", "阻塞", "已完成，但有一个或多个错误", "已完成，但有一个或多个警告"].indexOf(backup_sla[i]["bk_status"]) != -1) {
                            result += "<td style='vertical-align:middle;color:sandybrown'>" + backup_sla[i]["bk_status"] + "</td>";
                        } else {
                            result += "<td style='vertical-align:middle;;color:red'>" + backup_sla[i]["bk_status"] + "</td>";
                            cur_state = true
                        }


                        if (backup_sla[i]["rposec"] == 0 || 604800 && backup_sla[i]["rposec"] > 2592000) {
                            result += "<td style='vertical-align:middle;color: red'>" + backup_sla[i]["rpo"] + "</td>";
                            cur_rpo = true
                        } else if (backup_sla[i]["rposec"] > 604800 && backup_sla[i]["rposec"] <= 2592000)
                            result += "<td style='vertical-align:middle;color: sandybrown'>" + backup_sla[i]["rpo"] + "</td>";
                        else
                            result += "<td style='vertical-align:middle;color:green'>" + backup_sla[i]["rpo"] + "</td>";

                        if (backup_sla[i]["percent"] < 50) {
                            result += "<td style='vertical-align:middle;color: red'>" + backup_sla[i]["percent"] + "%</td>";
                            cur_percent = true
                        } else if (backup_sla[i]["percent"] >= 50 && backup_sla[i]["rposec"] < 100)
                            result += "<td style='vertical-align:middle;color: sandybrown'>" + backup_sla[i]["percent"] + "%</td>";
                        else
                            result += "<td style='vertical-align:middle;color:green'>" + backup_sla[i]["percent"] + "%</td>";

                        result += "</tr>";
                        $("tbody").append(result);

                        pre_clientname = backup_sla[i]["clientname"]
                        pre_idataagent = backup_sla[i]["idataagent"]
                        pre_type = backup_sla[i]["type"]

                        if(curclientname!=backup_sla[i]["clientname"]) {
                            if(curclientname!="") {
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
                                curclientsla="policy"
                            }
                            else if (cur_state){
                                curclientsla="state"
                            }
                            else if (cur_rpo) {
                                curclientsla="rpo"
                            }
                            else if (cur_percent) {
                                curclientsla="percent"
                            }
                            else {
                                curclientsla="health"
                            }
                        }else{
                            if (cur_policy) {
                                curclientsla="policy"
                            }
                            else if (cur_state){
                                if(curclientsla!="policy"){
                                    curclientsla = "state"
                                }
                            }
                            else if (cur_rpo) {
                                if(curclientsla!="policy"&&curclientsla!="state") {
                                    curclientsla = "rpo"
                                }
                            }
                            else if (cur_percent) {
                                if(curclientsla!="policy"&&curclientsla!="state"&&curclientsla!="rpo") {
                                    curclientsla = "percent"
                                }
                            }
                        }

                    }
                    if(curclientname!="") {
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
                    $("#loading").hide();

                    var chart = AmCharts.makeChart("chart_sla", {
                        "type": "pie",
                        "theme": "light",
                        "fontSize":15,
                        "fontFamily": 'Open Sans',

                        "color":    '#000',
                        "colors":["#228B22","#FF0F00", "#FF6600", "#FF9E01", "#FCD202", "#F8FF01", "#B0DE09"],

                        "dataProvider": [{
                            "name": "健康",
                            "value": healthnum
                        }, {
                            "name": "未设置计划",
                            "value": policynum
                        }, {
                            "name": "备份失败",
                            "value": statenum
                        }, {
                            "name": "RTO过长",
                            "value": rponum
                        }, {
                            "name": "备份成功率过低",
                            "value": percentnum
                        }],
                        "valueField": "value",
                        "titleField": "name",
                        "outlineAlpha": 0.4,
                        "depth3D": 15,
                        "balloonText": "[[title]]<br><span style='font-size:15px'><b>[[value]]</b> ([[percents]]%)</span>",
                        "angle": 30,
                    });
                }
            }
        });
    }

    getSla($('#utils_manage').val());

        // 点击事件

    $('#utils_manage').change(function () {
        $("tbody").empty();

        $("#loading").show();

        getSla($(this).val());
    });
});
