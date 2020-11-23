$(document).ready(function () {

     $.ajax({
        type: 'POST',
        dataType: 'json',
        url: '../get_client_name/',
        data: {
            "utils":$('#util').val(),
        },
        success: function (data) {
            if (data.ret == 0){
                alert(data.data)
            }else {
                var pre = '<option selected value="" >全部</option>';
                for (i = 0; i < data.data.length; i++) {
                    pre += '<option value="' + data.data[i].client_id + '">' + data.data[i].client_name + '</option>';
                }
                $("#clientid").append(pre)
            }

        }
    });

    $('#cv_joblist').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "iDisplayLength": 25,
        "bProcessing": true,
        "ajax": "../get_cv_joblist/?util=" + $('#util').val() + "&startdate=" + $('#starttime').val() +
            "&enddate=" + $('#endtime').val() + "&clientid=" + $('#clientid').val() + "&jobstatus=" + $('#jobstatus').val(),
        "columns": [
            {"data": "jobid"},
            {"data": "clientname"},
            {"data": "idataagent"},
            {"data": "instance"},
            {"data": "startdate"},
            {"data": "enddate"},
            {"data": "jobstatus"},
            {"data": null}
        ],
        "columnDefs": [
            {
                "targets": -2,
                "mRender": function (data, type, full) {
                    return "<span class='" + full.jobstatus_label + "' disabled id='" + full.jobid + "'>" + full.jobstatus + "</span>"
                }
            },
            {
                "targets": -1,
                "data": null,
                "width": "40px",
                "mRender": function (full) {
                    if(full.jobfailedreason != '' && full.jobfailedreason !=null )
                        return "<button  id='edit' title='详情' data-toggle='modal'  data-target='#static1'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button>"
                    else
                        return ""
                },
            }
        ],

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

        },
    });
    $('#cv_joblist tbody').on('click', 'button#edit', function () {
        var table = $('#cv_joblist').DataTable();
        var data = table.row($(this).parents('tr')).data();

        $("#jobid").val(data.jobid);
        $("#clientname").val(data.clientname);
        $("#idataagent").val(data.idataagent);
        $("#enddate").val(data.enddate);
        $("#jobfailedreason").val(data.jobfailedreason);

    });


    $('#starttime').datetimepicker({
        autoclose: true,
        minView: "month",
        format: 'yyyy-mm-dd',
    });
    $('#endtime').datetimepicker({
        autoclose: true,
        minView: "month",
        format: 'yyyy-mm-dd',
    });


    $('#cx').click(function () {
        var table = $('#cv_joblist').DataTable();
        table.ajax.url("../get_cv_joblist?util=" + $('#util').val() + "&startdate=" + $('#starttime').val() + "&enddate=" + $('#endtime').val() + "&clientid=" + $('#clientid').val() + "&jobstatus=" + $('#jobstatus').val()).load();
        get_jobbytype()
    })

    $('#util').change(function() {
        var table = $('#cv_joblist').DataTable();
        table.ajax.url("../get_cv_joblist?util=" + $('#util').val() + "&startdate=" + $('#starttime').val() + "&enddate=" + $('#endtime').val() + "&clientid=" + $('#clientid').val() + "&jobstatus=" + $('#jobstatus').val()).load();
        get_jobbackupsize_daily();
        get_jobbytype()
    });

    get_jobbackupsize_daily();
    get_jobbytype();
});

function get_jobbackupsize_daily() {
    var chart = null;
    $.getJSON('../get_jobbackupsize_daily?util='+ $("#util").val(), function (data) {
        chart = new Highcharts.Chart({
            chart: {
                renderTo: 'job_backupsize',
                style: {
                    fontFamily: 'Open Sans'
                },
                zoomType: 'x'
            },
            title: {
                text: '每日备份数据量'
            },
            subtitle: {
                text: document.ontouchstart === undefined ?
                '鼠标拖动可以进行缩放' : '手势操作进行缩放'
            },
            xAxis: {
                type: 'datetime',
                dateTimeLabelFormats: {
                    millisecond: '%Y-%m-%d',
                    second: '%Y-%m-%d',
                    minute: '%Y-%m-%d',
                    hour: '%Y-%m-%d',
                    day: '%Y-%m-%d',
                    week: '%Y-%m-%d',
                    month: '%Y-%m',
                    year: '%Y'
                }
            },
            tooltip: {
                dateTimeLabelFormats: {
                    millisecond: '%Y-%m-%d',
                    second: '%Y-%m-%d',
                    minute: '%Y-%m-%d',
                    hour: '%Y-%m-%d',
                    day: '%Y-%m-%d',
                    week: '%Y-%m-%d',
                    month: '%Y-%m-%d',
                    year: '%Y-%m-%d',
                }
            },
            yAxis: {
                title: {
                    text: '备份量(GB)'
                }
            },
            legend: {
                enabled: false
            },
            plotOptions: {
                area: {
                    fillColor: {
                        linearGradient: {
                            x1: 0,
                            y1: 0,
                            x2: 0,
                            y2: 1
                        },
                        stops: [
                            [0, new Highcharts.getOptions().colors[0]],
                            [1, new Highcharts.Color(Highcharts.getOptions().colors[0]).setOpacity(0).get('rgba')]
                        ]
                    },
                    marker: {
                        radius: 2
                    },
                    lineWidth: 1,
                    states: {
                        hover: {
                            lineWidth: 1
                        }
                    },
                    threshold: null
                }
            },
            series: [{
                type: 'area',
                name: '备份量',
                tooltip: {  // 为当前数据列指定特定的 tooltip 选项
                            valueSuffix: ' GB'
                        },
                data: data.data
            }]
        });
    });
}

function get_jobbytype() {
    $.ajax({
            type: "GET",
            url: "../get_jobbytype/",
            data: {
                util:$('#util').val(),
                startdate:$('#starttime').val(),
                enddate:$('#endtime').val(),
                clientid:$('#clientid').val(),
                jobstatus:$('#jobstatus').val(),
            },
            success: function(data) {
                var chart = new Highcharts.Chart({
                    chart: {
                        renderTo: 'jobbytype',
                        type: 'column'
                    },
                    title: {
                        text: '备份任务汇总'
                    },
                    xAxis: {
                        categories: data.data.idataagent_list,
                    },
                    yAxis: [{
                        min: 0,
                        title: {
                            text: '备份量'
                        }
                    }, {
                        title: {
                            text: '备份次数'
                        },
                        opposite: true
                    }],
                    legend: {
                        shadow: false
                    },
                    tooltip: {
                        shared: true
                    },
                    plotOptions: {
                        column: {
                            grouping: false,
                            shadow: false,
                            borderWidth: 0
                        }
                    },
                    series: [{
                        name: '备份量(GB)',
                        color: 'rgba(165,170,217,1)',
                        data: data.data.totalBackupSize_list,
                        tooltip: {  // 为当前数据列指定特定的 tooltip 选项
                            valueSuffix: ' GB'
                        },
                        pointPadding: 0.4, // 通过 pointPadding 和 pointPlacement 控制柱子位置
                        pointPlacement: -0.1
                    }, {
                        name: '备份次数',
                        color: 'rgba(248,161,63,1)',
                        data: data.data.totalBackupTimes_list,
                        tooltip: {  // 为当前数据列指定特定的 tooltip 选项
                            valueSuffix: ' 次'
                        },
                        pointPadding: 0.4,
                        pointPlacement: 0.1,
                        yAxis: 1  // 指定数据列所在的 yAxis
                    }]
                });
            },
        error: function() {
            console.log('error')
        }
    });
}