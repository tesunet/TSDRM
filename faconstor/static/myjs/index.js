var Dashboard = function () {

    return {



        initCalendar: function () {
            if (!jQuery().fullCalendar) {
                return;
            }

            var date = new Date();
            var d = date.getDate();
            var m = date.getMonth();
            var y = date.getFullYear();

            var h = {};


            $('#calendar').removeClass("mobile");
            if (App.isRTL()) {
                h = {
                    right: 'title',
                    center: '',
                    left: 'prev,next,today,month,agendaWeek,agendaDay'
                };
            } else {
                h = {
                    left: 'title',
                    center: '',
                    right: 'prev,next,today,month,agendaWeek,agendaDay'
                };
            }


            $('#calendar').fullCalendar('destroy'); // destroy the calendar
            $('#calendar').fullCalendar({ //re-initialize the calendar
                disableDragging: false,
                header: h,
                editable: true,
                monthNames:['一月', '二月', '三月', '四月', '五月', '六月', '七月',
                            '八月', '九月', '十月', '十一月', '十二月'],
                dayNames:['星期一', '星期二', '星期三', '星期四',
                         '星期五', '星期六', '星期天'],
                dayNamesShort:['星期一', '星期二', '星期三', '星期四',
                         '星期五', '星期六', '星期天'],
                buttonText:{
                    today:    '回到当日',
                    month:    '月',
                    week:     '周',
                    day:      '日',
                    list:     'list'
                },
                events: [{
                    title: '系统1恢复',
                    start: new Date(y, m, 1),
                    backgroundColor: App.getBrandColor('yellow')
                }, {
                    title: '系统1恢复',
                    start: new Date(y, m, d - 5),
                    end: new Date(y, m, d - 2),
                    backgroundColor: App.getBrandColor('blue')
                }, {
                    title: '系统2恢复',
                    start: new Date(y, m, d - 3, 16, 0),
                    allDay: false,
                    backgroundColor: App.getBrandColor('red')
                }, {
                    title: '系统3恢复',
                    start: new Date(y, m, d + 6, 16, 0),
                    allDay: false,
                    backgroundColor: App.getBrandColor('green')
                }, {
                    title: '系统4恢复',
                    start: new Date(y, m, d + 9, 10, 30),
                    allDay: false
                }, {
                    title: '系统1恢复',
                    start: new Date(y, m, d, 14, 0),
                    end: new Date(y, m, d, 14, 0),
                    backgroundColor: App.getBrandColor('grey'),
                    allDay: false
                }, {
                    title: '系统2恢复',
                    start: new Date(y, m, d + 1, 19, 0),
                    end: new Date(y, m, d + 1, 22, 30),
                    backgroundColor: App.getBrandColor('purple'),
                    allDay: false
                }, {
                    title: '系统1恢复',
                    start: new Date(y, m, 28),
                    end: new Date(y, m, 29),
                    backgroundColor: App.getBrandColor('yellow'),
                    url: 'http://www.baidu.com/'
                }]
            });
        },


        initAmChart1: function () {
            if (typeof(AmCharts) === 'undefined' || $('#dashboard_amchart_1').size() === 0) {
                return;
            }


            $.ajax({
                type: "GET",
                url: "../get_dashboard_amchart_1/",
                data: {
                    type: $('#type_1').val(),
                },
                success: function (data) {
                    var chartData = new Array;
                    chartData = JSON.parse(data);
                    var chart = AmCharts.makeChart("dashboard_amchart_1", {
                        type: "serial",
                        fontSize: 12,
                        fontFamily: "Open Sans",
                        dataProvider: chartData,

                        addClassNames: true,
                        startDuration: 1,
                        color: "#6c7b88",
                        marginLeft: 0,

                        categoryField: "date",
                        categoryAxis: {
                            parseDates: false,
                            autoGridCount: false,
                            gridCount: 50,
                            gridAlpha: 0.1,
                            gridColor: "#FFFFFF",
                            axisColor: "#555555",
                        },

                        valueAxes: [{
                            id: "a1",
                            gridAlpha: 0,
                            axisAlpha: 0
                        },],
                        graphs: [{
                            id: "g1",
                            valueField: "times3",
                            title: "备份成功",
                            type: "column",
                            fillAlphas: 0.7,
                            valueAxis: "a1",
                            balloonText: "[[value]] 次",
                            legendValueText: "[[value]] 次",
                            legendPeriodValueText: "小计: [[value.sum]] 次",
                            lineColor: "#84b761",
                            alphaField: "alpha",
                            legendValueText: "[[description]]：[[value]] 次",
                            descriptionField: "date",
                        }, {
                            id: "g2",
                            valueField: "times2",
                            title: "备份失败",
                            type: "column",
                            fillAlphas: 0.7,
                            valueAxis: "a2",
                            balloonText: "[[value]] 次",
                            legendValueText: "[[value]] 次",
                            legendPeriodValueText: "小计: [[value.sum]] 次",
                            lineColor: "#F70909",
                            alphaField: "alpha",
                            legendValueText: "[[description]]：[[value]] 次",
                            descriptionField: "date",
                        }, {
                            id: "g3",
                            valueField: "times1",
                            title: "备份合计",
                            legendPeriodValueText: "合计: [[value.sum]] 次",
                            lineColor: "#OOOOOO",
                            alphaField: "alpha",
                            legendValueText: "[[description]]：[[value]] 次",
                            descriptionField: "date",
                        }],

                        chartCursor: {
                            zoomable: false,
                            categoryBalloonDateFormat: "DD",
                            cursorAlpha: 0,
                            categoryBalloonColor: "#e26a6a",
                            categoryBalloonAlpha: 0.8,
                            valueBalloonsEnabled: false
                        },
                        legend: {
                            bulletType: "round",
                            equalWidths: false,
                            valueWidth: 120,
                            useGraphSettings: true,
                            color: "#6c7b88"
                        }
                    });
                },
            });

        },

        initAmChart2: function () {
            if (typeof(AmCharts) === 'undefined' || $('#dashboard_amchart_2').size() === 0) {
                return;
            }

            $.ajax({
                type: "GET",
                url: "../get_dashboard_amchart_2/",
                data: {
                    type: $('#type_2').val(),
                },
                success: function (data) {
                    var chartData = new Array;
                    chartData = JSON.parse(data);
                    var chart = AmCharts.makeChart("dashboard_amchart_2", {
                        type: "serial",
                        fontSize: 12,
                        fontFamily: "Open Sans",
                        dataProvider: chartData,

                        addClassNames: true,
                        startDuration: 1,
                        color: "#6c7b88",
                        marginLeft: 0,

                        categoryField: "clientname",
                        rotate: true,
                        categoryAxis: {
                            parseDates: false,
                            autoGridCount: false,
                            gridCount: 50,
                            gridAlpha: 0.1,
                            gridColor: "#FFFFFF",
                            axisColor: "#555555",
                        },

                        valueAxes: [{
                            id: "a1",
                            title: "",
                            gridAlpha: 0,
                            axisAlpha: 0
                        },],
                        graphs: [{
                            id: "g1",
                            valueField: "times3",
                            title: "备份成功",
                            type: "column",
                            fillAlphas: 0.7,
                            valueAxis: "a1",
                            balloonText: "[[value]] 次",
                            legendValueText: "[[value]] 次",
                            legendPeriodValueText: "小计: [[value.sum]] 次",
                            lineColor: "#84b761",
                            alphaField: "alpha",
                            legendValueText: "[[description]]：[[value]]次",
                            descriptionField: "clientname",
                        }, {
                            id: "g2",
                            valueField: "times2",
                            title: "备份失败",
                            type: "column",
                            fillAlphas: 0.7,
                            valueAxis: "a1",
                            balloonText: "[[value]] 次",
                            legendValueText: "[[value]] 次",
                            legendPeriodValueText: "小计: [[value.sum]] 次",
                            lineColor: "#F70909",
                            alphaField: "alpha",
                            legendValueText: "[[description]]：[[value]]次",
                            descriptionField: "clientname",
                        }, {
                            id: "g3",
                            valueField: "times1",
                            title: "备份合计",
                            legendPeriodValueText: "合计: [[value.sum]] 次",
                            lineColor: "#OOOOOO",
                            alphaField: "alpha",
                            legendValueText: "[[description]]：[[value]] 次 最近：[[lasttime]]",
                            descriptionField: "clientname",
                        }],

                        chartCursor: {
                            zoomable: false,
                            categoryBalloonDateFormat: "DD",
                            cursorAlpha: 0,
                            categoryBalloonColor: "#e26a6a",
                            categoryBalloonAlpha: 0.8,
                            valueBalloonsEnabled: false
                        },
                        legend: {
                            bulletType: "round",
                            equalWidths: false,
                            valueWidth: 120,
                            useGraphSettings: true,
                            color: "#6c7b88"
                        }
                    });
                },
            });
        },

        initAmChart3: function () {
            if (typeof(AmCharts) === 'undefined' || $('#dashboard_amchart_1').size() === 0) {
                return;
            }


            $.ajax({
                type: "GET",
                url: "../get_dashboard_amchart_3/",
                data: {
                    type: $('#type_3').val(),
                },
                success: function (data) {
                    var chartData = new Array;
                    chartData = JSON.parse(data);
                    var chart = AmCharts.makeChart("dashboard_amchart_3", {
                        type: "serial",
                        fontSize: 12,
                        fontFamily: "Open Sans",
                        dataProvider: chartData,

                        addClassNames: true,
                        startDuration: 1,
                        color: "#6c7b88",
                        marginLeft: 0,

                        categoryField: "date",
                        categoryAxis: {
                            parseDates: false,
                            autoGridCount: false,
                            gridCount: 50,
                            gridAlpha: 0.1,
                            gridColor: "#FFFFFF",
                            axisColor: "#555555",
                        },

                        valueAxes: [{
                            id: "a1",
                            gridAlpha: 0,
                            axisAlpha: 0
                        },],
                        graphs: [{
                            id: "g1",
                            valueField: "ll",
                            title: "网络流量",
                            type: "column",
                            fillAlphas: 0.7,
                            valueAxis: "a1",
                            balloonText: "[[value]] MB",
                            legendValueText: "[[value]] MB",
                            legendPeriodValueText: "合计: [[value.sum]] MB",
                            lineColor: "#84b761",
                            alphaField: "alpha",
                            legendValueText: "[[description]]：[[value]] MB",
                            descriptionField: "date",
                        }, {
                            id: "g2",
                            valueField: "rl",
                            title: "磁盘容量",
                            type: "column",
                            fillAlphas: 0.7,
                            valueAxis: "a2",
                            balloonText: "[[value]] MB",
                            legendValueText: "[[value]] MB",

                            lineColor: "#98F5FF",
                            alphaField: "alpha",
                            legendValueText: "[[description]]：[[value]] MB",
                            descriptionField: "date",
                        }],

                        chartCursor: {
                            zoomable: false,
                            categoryBalloonDateFormat: "DD",
                            cursorAlpha: 0,
                            categoryBalloonColor: "#e26a6a",
                            categoryBalloonAlpha: 0.8,
                            valueBalloonsEnabled: false
                        },
                        legend: {
                            bulletType: "round",
                            equalWidths: false,
                            valueWidth: 120,
                            useGraphSettings: true,
                            color: "#6c7b88"
                        }
                    });
                },
            });

        },

        initAmChart4: function () {
            if (typeof(AmCharts) === 'undefined' || $('#dashboard_amchart_4').size() === 0) {
                return;
            }
            $.ajax({
                type: "GET",
                url: "../get_dashboard_amchart_4",
                data: {
                    type: $('#type_4').val(),
                },
                success: function (data) {
                    var chartData = new Array;
                    chartData = JSON.parse(data);
                    var chart = AmCharts.makeChart("dashboard_amchart_4", {
                        "type": "pie",
                        "theme": "light",
                        "dataProvider": chartData,
                        "valueField": "value",
                        "titleField": "country",
                        "outlineAlpha": 0.4,
                        "depth3D": 20,
                        "balloonText": "[[title]]<br><span style='font-size:14px'><b>[[value]]</b> ([[percents]]%)</span>",
                        "angle": 20,
                        "export": {
                            "enabled": true
                        }
                    });
                    jQuery('.chart-input').off().on('input change', function () {
                        var property = jQuery(this).data('property');
                        var target = chart;
                        var value = Number(this.value);
                        chart.startDuration = 0;

                        if (property == 'innerRadius') {
                            value += "%";
                        }

                        target[property] = value;
                        chart.validateNow();
                    });
                }
            });
        },



        init: function () {

            this.initCalendar();

            this.initAmChart1();
            this.initAmChart2();
            this.initAmChart3();
            this.initAmChart4();

        }
    };

}();
   
if (App.isAngularJsApp() === false) {
    jQuery(document).ready(function () {
        Dashboard.init(); // init metronic core componets
    });
}

$(document).ready(function () {
    $('#option4_2').click(function () {
        $('#type_4').val("2")
        Dashboard.initAmChart4();
    })
    $('#option4_3').click(function () {
        $('#type_4').val("3")
        Dashboard.initAmChart4();
    })
    $('#option4_4').click(function () {
        $('#type_4').val("4")
        Dashboard.initAmChart4();
    })
    $('#option4_1').click(function () {
        $('#type_4').val("1")
        Dashboard.initAmChart4();
    })

    $('#option1_2').click(function () {
        $('#type_1').val("2")
        Dashboard.initAmChart1();
    })
    $('#option1_3').click(function () {
        $('#type_1').val("3")
        Dashboard.initAmChart1();
    })
    $('#option1_4').click(function () {
        $('#type_1').val("4")
        Dashboard.initAmChart1();
    })
    $('#option1_1').click(function () {
        $('#type_1').val("1")
        Dashboard.initAmChart1();
    })

    $('#option2_2').click(function () {
        $('#type_2').val("2")
        Dashboard.initAmChart2();
    })
    $('#option2_3').click(function () {
        $('#type_2').val("3")
        Dashboard.initAmChart2();
    })
    $('#option2_4').click(function () {
        $('#type_2').val("4")
        Dashboard.initAmChart2();
    })
    $('#option2_1').click(function () {
        $('#type_2').val("1")
        Dashboard.initAmChart2();
    })

    $('#option3_2').click(function () {
        $('#type_3').val("2")
        Dashboard.initAmChart3();
    })
    $('#option3_3').click(function () {
        $('#type_3').val("3")
        Dashboard.initAmChart3();
    })
    $('#option3_4').click(function () {
        $('#type_3').val("4")
        Dashboard.initAmChart3();
    })
    $('#option3_1').click(function () {
        $('#type_3').val("1")
        Dashboard.initAmChart3();
    })
});


$("#restore_task").on("click", function () {
    $("#restore_info").removeAttr("hidden");
    $("#backup_info").attr("hidden", true);
});

$("#backup_task").on("click", function () {
    $("#restore_info").attr("hidden", true);
    $("#backup_info").removeAttr("hidden");
});

$("ul#locate").on("click", " li", function () {
    var job_id = $(this).attr("id");
    $("input#clientname").val($("#a".replace("a", job_id)).find("input#clientname_tag").val());
    $("input#idataagent").val($("#a".replace("a", job_id)).find("input#idataagent_tag").val());
    $("textarea#jobfailedreason").text($("#a".replace("a", job_id)).find("input#jobfailedreason_tag").val());
    $("input#jobid").val(job_id);
});

$("ul#locate_task").on("click", " li", function () {
    var task_id = $(this).attr("id");
    $("#mytask").val($("#a".replace("a", task_id)).find("input#task_id").val());
    $("#processname").val($("#a".replace("a", task_id)).find("input#process_name").val());
    $("#sendtime").val($("#a".replace("a", task_id)).find("input#send_time").val());
    $("#signrole").val($("#a".replace("a", task_id)).find("input#sign_role").val());
    $("#processrunreason").val($("#a".replace("a", task_id)).find("input#process_run_reason").val());
});


$("button#not_display").on("click", function () {
    var job_id = $("input#jobid").val();
    var csrfToken = $("[name='csrfmiddlewaretoken']").val();
    $.ajax({
        type: "POST",
        url: "../not_display_jobs/",
        data: {
            "jobid": $("input#jobid").val(),
            "csrfmiddlewaretoken": csrfToken,
        },
        success: function (data) {
            if (data["result"] == "0") {
                alert("取消显示成功!");
            } else {
                alert("取消显示失败,请联系系统管理员!")
            }
            $('#static').modal('hide');
            $("li#a".replace("a", job_id)).remove();
        }
    });
});


$("#sign_save").click(function () {
    var csrfToken = $("[name='csrfmiddlewaretoken']").val();
    $.ajax({
        type: "POST",
        url: "../processsignsave/",
        data: {
            "task_id": $("#mytask").val(),
            "sign_info": $("#sign_info").val(),
            "csrfmiddlewaretoken": csrfToken,
        },
        success: function (data) {
            if (data["res"] == "签字成功,同时启动流程。") {
                window.location.href = data["data"];
            }
            else
                alert(data["res"]);
                $('#static01').modal('hide');
        },
        error: function (e) {
            alert("流程启动失败，请于管理员联系。");
        }
    });
});




