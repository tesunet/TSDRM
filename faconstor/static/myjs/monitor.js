$(document).ready(function () {
    /*
        初始化
     */
    var csrfToken = $("[name='csrfmiddlewaretoken']").val();

    // 最近七日演练
    var weekDrillChart = echarts.init(document.getElementById('arightboxbott'));
    var weekDrillOption = {
        color: ['#7de494', '#7fd7b1', '#5578cf', '#5ebbeb', '#d16ad8', '#f8e19a', '#00b7ee', '#81dabe', '#5fc5ce'],
        backgroundColor: 'rgba(1,202,217,.2)',

        grid: {
            left: '5%',
            right: '8%',
            bottom: '7%',
            top: '8%',
            containLabel: true
        },
        toolbox: {
            feature: {
                saveAsImage: {}
            }
        },
        xAxis: {
            type: 'category',
            boundaryGap: false,
            axisLine: {
                lineStyle: {
                    color: 'rgba(255,255,255,.2)'
                }
            },
            splitLine: {
                lineStyle: {
                    color: 'rgba(255,255,255,.1)'
                }
            },
            axisLabel: {
                color: "rgba(255,255,255,.7)"
            },
            data: []
        },
        yAxis: {
            type: 'value',
            axisLine: {
                lineStyle: {
                    color: 'rgba(255,255,255,.2)'
                }
            },
            splitLine: {
                lineStyle: {
                    color: 'rgba(255,255,255,.1)'
                }
            },
            axisLabel: {
                color: "rgba(255,255,255,.7)"
            },
        },
        series: [
            {
                name: '最近7日演练次数',
                type: 'line',
                stack: '次数',
                areaStyle: {normal: {}},
                data: [],
                label: {
                    normal: {
                        show: true,
                        position: 'top',
                        textStyle: {
                            color: 'white'
                        }
                    }
                },
            }
        ]
    };
    weekDrillChart.setOption(weekDrillOption);

    // 系统演练次数TOP5
    var drillTopTimeChart = echarts.init(document.getElementById('pleftbox2bott_cont'));
    var drillTopTimeOption = {
        color: ['#7ecef4'],
        backgroundColor: 'rgba(1,202,217,.2)',
        grid: {
            left: 40,
            right: 20,
            top: 30,
            bottom: 0,
            containLabel: true
        },

        xAxis: {
            type: 'value',
            axisLine: {
                lineStyle: {
                    color: 'rgba(255,255,255,0)'
                }
            },
            splitLine: {
                lineStyle: {
                    color: 'rgba(255,255,255,0)'
                }
            },
            axisLabel: {
                color: "rgba(255,255,255,0)"
            },
            boundaryGap: [0, 0.01]
        },
        yAxis: {
            type: 'category',
            axisLine: {
                lineStyle: {
                    color: 'rgba(255,255,255,.5)'
                }
            },
            splitLine: {
                lineStyle: {
                    color: 'rgba(255,255,255,.1)'
                }
            },
            axisLabel: {
                color: "rgba(255,255,255,.5)"
            },
            data: []
        },
        series: [
            {
                name: '系统演练次数TOP5',
                type: 'bar',
                barWidth: 20,
                itemStyle: {
                    normal: {
                        color: new echarts.graphic.LinearGradient(
                            1, 0, 0, 1,
                            [
                                {offset: 0, color: 'rgba(230,253,139,.7)'},
                                {offset: 1, color: 'rgba(41,220,205,.7)'}
                            ]
                        )
                    }
                },
                data: [],
                label: {
                    normal: {
                        show: true,
                        position: 'right',
                        textStyle: {
                            color: 'white'
                        }
                    }
                },
            }
        ]
    };
    drillTopTimeChart.setOption(drillTopTimeOption);

    // 演练成功率
    var drillRateChart = echarts.init(document.getElementById('lpeftbot'));
    var drillRateOption = {
        color: ['#00b7ee', '#d2d17c', '#5578cf', '#5ebbeb', '#d16ad8', '#f8e19a', '#00b7ee', '#81dabe', '#5fc5ce'],
        backgroundColor: 'rgba(1,202,217,.2)',
        grid: {
            left: 20,
            right: 20,
            top: 0,
            bottom: 20
        },
        legend: {
            top: 10,
            textStyle: {
                fontSize: 10,
                color: 'rgba(255,255,255,.7)'
            },
            data: ['成功', '失败']
        },
        series: [
            {
                name: '演练成功率',
                type: 'pie',
                radius: '55%',
                center: ['50%', '55%'],
                data: [
                    {value: 50, name: '成功'},
                    {value: 50, name: '失败'}

                ],
                itemStyle: {
                    emphasis: {
                        shadowBlur: 10,
                        shadowOffsetX: 0,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    },
                    normal: {
                        label: {
                            show: true,
                            formatter: '{b}:{d}%'
                        },
                        labelLine: {show: true}
                    }
                },
            }
        ]
    };
    drillRateChart.setOption(drillRateOption);

    /*
    大屏动态加载数据
        最近7日演练次数:
            weekDrillChart.setOption({
                xAxis: {
                    data: data.week_drill.drill_day
                },
                series: [{
                    data: data.week_drill.drill_times
                }]
            });
            weekDrillChart.setOption({
                xAxis: {
                    data: data.avgRTO.drill_day
                },
                series: [{
                    data: data.avgRTO.drill_rto
                }]
            });
            drillTopTimeChart.setOption({
                xAxis: {
                    data: data.drill_top_time.drill_name
                },
                series: [{
                    data: data.drill_top_time.drill_time
                }]
            });
     */
    $.ajax({
        type: "POST",
        url: "../get_monitor_data/",
        data: {
            "csrfmiddlewaretoken": csrfToken
        },
        success: function (data) {
            // 最近七日演练
            weekDrillChart.setOption({
                xAxis: {
                    data: data.week_drill.drill_day
                },
                series: [{
                    data: data.week_drill.drill_times
                }]
            });

            // 系统演练次数TOP5
            drillTopTimeChart.setOption({
                yAxis: {
                    data: data.drill_top_time.drill_name
                },
                series: [{
                    data: data.drill_top_time.drill_time
                }]
            });
            // 演练成功率
            drillRateChart.setOption({
                series: [{
                    data: [
                        {value: data.drill_rate[0], name: '成功'},
                        {value: data.drill_rate[1], name: '失败'}

                    ],
                }]
            });

            // 演练监控
            $("#drill_monitor").empty();
            for (var i = 0; i < data.drill_monitor.length; i++) {
                var status_label = "",
                    status_name = "";
                if (data.drill_monitor[i].state == "DONE") {
                    status_label = "label-success";
                    status_name = "成功";
                } else if (data.drill_monitor[i].state == "STOP") {
                    status_label = "label-warning";
                    status_name = "终止";
                } else if (data.drill_monitor[i].state == "ERROR") {
                    status_label = "label-danger";
                    status_name = "错误";
                } else if (data.drill_monitor[i].state == "RUN") {
                    status_label = "label-info";
                    status_name = "运行中";
                } else if (data.drill_monitor[i].state == "REJECT") {
                    status_label = "label-warning";
                    status_name = "已取消";
                } else {
                    status_label = "label-primary";
                    status_name = "未演练";
                }

                $("#drill_monitor").append('<tr>\n' +
                    '    <td> ' + data.drill_monitor[i].process_name + '</td>\n' +
                    '    <td><span class="label label-sm ' + status_label + '"> ' + status_name + ' </span></td>\n' +
                    '    <td> ' + data.drill_monitor[i].schedule_time + '</td>\n' +
                    '    <td> ' + data.drill_monitor[i].start_time + '</td>\n' +
                    '    <td> ' + data.drill_monitor[i].end_time + '</td>\n' +
                    '    <td> ' + data.drill_monitor[i].percent + '</td>\n' +
                    '</tr>');
            }

            // 演练日志
            $("#drill_log").empty();
            for (var i = 0; i < data.task_list.length; i++) {
                var drill_log_class = i % 2 ? ' class="bg"' : '';
                $("#drill_log").append('<li ' + drill_log_class + '>\n' +
                    '    <p class="fl"><b>' + data.task_list[i].process_name + '</b><br>\n' +
                    '        ' + data.task_list[i].content + '<br>\n' +
                    '    </p>\n' +
                    '    <p class="fr pt17">' + data.task_list[i].start_time + '</p>\n' +
                    '</li>');
            }

            // 错误流程
            // error_processrun
            $("#error_process").empty();
            console.log(data.error_processrun.length)
            if (data.error_processrun.length < 1) {
                $("#error_process").append('<li>\n' +
                    '    <p class="fl"><a style="text-decoration: none;"><b>无</b></a></p>\n' +
                    '    <p class="fr pt17"></p>\n' +
                    '</li>')
            } else {
                for (var i = 0; i < data.error_processrun.length; i++) {
                    var error_processrun_class = i % 2 ? ' class="bg"' : '';

                    $("#error_process").append('<li ' + error_processrun_class + '>\n' +
                        '    <p class="fl"><a style="text-decoration: none;" target="_blank" href="' + data.error_processrun[i].processrun_url + '"><b>' + data.error_processrun[i].process_name + '</b></a></p>\n' +
                        '    <p class="fr pt17">' + data.error_processrun[i].start_time + '</p>\n' +
                        '</li>');
                }
            }

            // 今日作业
            // var myDate = new Date();
            //
            // var year = myDate.getFullYear();        //获取当前年
            // var month = myDate.getMonth() + 1;   //获取当前月
            // var date = myDate.getDate();            //获取当前日
            // var curTime = year + "-" + month + "-" + date;
            var aSuccessHref = '/falconstorsearch?runstate=DONE';
            var aRunningHref = '/falconstorsearch?runstate=RUN';
            var aErrorHref = '/falconstorsearch?runstate=ERROR';
            var aEditHref = '/falconstorsearch?runstate=EDIT';

            if (data.today_job.running_job > 0) {
                $("#running_job").html('<a href="' + aRunningHref + '" target="_blank">' + data.today_job.running_job + '</a>');
                $("#running_job").find("a").css("color", "#44ee44");
            } else {
                $("#running_job").html(data.today_job.running_job);
            }
            console.log(data.today_job.success_job)
            if (data.today_job.success_job > 0) {
                $("#success_job").html('<a href="' + aSuccessHref + '" target="_blank">' + data.today_job.success_job + '</a>');
                $("#success_job").find("a").css("color", "#24c9ff");
            } else {
                $("#success_job").html(data.today_job.success_job);
            }
            if (data.today_job.error_job > 0) {
                $("#error_job").html('<a href="' + aErrorHref + '" target="_blank">' + data.today_job.error_job + '</a>');
                $("#error_job").find("a").css("color", "#e02222");

            } else {
                $("#error_job").html(data.today_job.error_job);
            }
            // if (data.today_job.not_running > 0) {
            //     $("#not_running").html('<a href="'+ aEditHref +'" target="_blank">' + data.today_job.not_running + '</a>');
            //     $("#not_running").find("a").css("color", "#ffff00");
            // } else {
            $("#not_running").html(data.today_job.not_running);
            // }
            // var table = $('#sample_1').DataTable();
            // table.ajax.url("../restore_search_data?runstate=" + $('#runstate').val() + "&startdate=" + $('#startdate').val() + "&enddate=" + $('#enddate').val() + "&processname=" + $('#processname').val() + "&runperson=" + $('#runperson').val()).load();
        },
    });

    function getClientsStatus() {
        $.ajax({
            type: "POST",
            url: "../get_clients_status/",
            data: {
                "csrfmiddlewaretoken": csrfToken,
                "utils_id": $("#utils").val()
            },
            success: function (data) {
                $("#service_status").text(data.clients_status.service_status);
                $("#net_status").text(data.clients_status.net_status);
                $("#all_clients").html('<a href="/backup_status/" target="_blank">' + data.clients_status.all_clients + '</a>');
                $("#all_clients").find("a").css("color", "#24c9ff");
                // 报警客户端
                var warning_client_num = 0;
                var whole_list = data.clients_status.whole_backup_list;

                // 客户端下有一个子客户端下备份报错记录 失败
                var pre_clientname = "";
                for (var i = 0; i < whole_list.length; i++) {
                    if (whole_list[i]['bk_status'].indexOf("失败") != -1 && whole_list[i]["clientname"] != pre_clientname) {
                        warning_client_num += 1;
                    }
                    pre_clientname = whole_list[i]["clientname"];
                }
                //'<a href="/backup_status/" target="_blank">' + data.clients_status.all_clients + '</a>'
                $("#error_clients").html('<a href="/backup_status/" target="_blank">' + warning_client_num + '</a>');
                if (warning_client_num > 0) {
                    $("#error_clients").find("a").css("color", "red");
                }
            },
        });
    }

    getClientsStatus();

    $("#utils").change(function () {
        getClientsStatus();
    })
});


