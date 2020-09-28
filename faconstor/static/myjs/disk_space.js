$(document).ready(function() {
    $("#loading").show();

    function getMADiskSpace() {
        $.ajax({
            type: "POST",
            url: "../get_ma_disk_space/",
            data: {
                util: $("#utils_manage").val(),
            },
            success: function(data) {
                var capacity_available_percent = 0,
                    space_reserved_percent = 0,
                    used_space_percent = 0;

                if (data.status == 1) {
                    capacity_available_percent = data.data.capacity_available_percent,
                        space_reserved_percent = data.data.space_reserved_percent,
                        used_space_percent = data.data.used_space_percent;
                }
                AmCharts.makeChart("disk_space_container", {
                    "type": "pie",
                    "theme": "light",
                    "fontSize": 15,
                    "fontFamily": 'Open Sans',

                    "color": '#000',
                    "colors": ["#228B22", "#FF6600", "#FF0F00"],

                    "dataProvider": [{
                        "name": "可用空间",
                        "value": capacity_available_percent
                    }, {
                        "name": "保留空间",
                        "value": space_reserved_percent
                    }, {
                        "name": "已用空间",
                        "value": used_space_percent
                    }],
                    "valueField": "value",
                    "titleField": "name",
                    "outlineAlpha": 0.4,
                    "depth3D": 15,
                    "balloonText": "[[title]]<br><span style='font-size:15px'><b>[[value]]</b> ([[percents]]%)</span>",
                    "angle": 30,
                });
            }
        });
    }

    getMADiskSpace();

    function getDiskSpace(utils_manage_id) {
        $.ajax({
            type: 'POST',
            dataType: 'json',
            url: '../get_disk_space/',
            data: {
                'utils_manage_id': utils_manage_id
            },
            success: function(data) {
                if (data.status == 1) {
                    // 磁盘容量表
                    var disk_space = data.data;

                    var pre_display_name = "";
                    var pre_library_name = "";
                    var sort = 0;
                    for (var i = 0; i < disk_space.length; i++) {
                        var display_name_hidden = "";
                        var library_name_hidden = "";

                        if (pre_display_name == disk_space[i]["DisplayName"]) {
                            display_name_hidden = "display:none";
                        } else {
                            sort += 1;
                        }
                        if (pre_display_name == disk_space[i]["DisplayName"] && pre_library_name == disk_space[i]["LibraryName"]) {
                            library_name_hidden = "display:none";
                        }

                        // GB
                        var CapacityAvailable = (disk_space[i]["CapacityAvailable"] / 1024).toFixed(0)
                        var SpaceReserved = (disk_space[i]["SpaceReserved"] / 1024).toFixed(0)
                        var TotalSpaceMB = (disk_space[i]["TotalSpaceMB"] / 1024).toFixed(0)

                        $("tbody").append(
                            '<tr>' +
                            '<td rowspan="' + disk_space[i].display_name_rowspan + '" style="vertical-align:middle; ' + display_name_hidden + '">' + sort + '</td>' +
                            '<td rowspan="' + disk_space[i].display_name_rowspan + '" style="vertical-align:middle; ' + display_name_hidden + '">' + disk_space[i]["DisplayName"] + '</td>' +
                            '<td rowspan="' + disk_space[i].library_name_rowspan + '" style="vertical-align:middle; ' + library_name_hidden + '">' + disk_space[i]["LibraryName"] + '</td>' +
                            '<td style="vertical-align:middle">' + disk_space[i]["BarCode"] + '</td>' +
                            '<td style="vertical-align:middle">' + disk_space[i]["MountPathName"] + '</td>' +
                            '<td style="vertical-align:middle">' + CapacityAvailable + ' GB</td>' +
                            '<td style="vertical-align:middle">' + SpaceReserved + ' GB</td>' +
                            '<td style="vertical-align:middle">' + TotalSpaceMB + ' GB</td>' +
                            '<td style="vertical-align:middle">' + disk_space[i]["LastBackupTime"] + '</td>' +
                            '<td style="vertical-align:middle">' + disk_space[i]["Offline"] + '</td>' +
                            '<td style="vertical-align:middle"><button id="edit" title="图表" data-toggle="modal" data-target="#static" class="btn btn-xs btn-primary" type="button"><input value="' + disk_space[i]["MediaID"] + '" hidden><i class="fa fa-bar-chart"></i></button></td>' +
                            '</tr>'
                        );

                        pre_display_name = disk_space[i]["DisplayName"]
                        pre_library_name = disk_space[i]["LibraryName"]
                    }
                    $("#loading").hide();
                } else {
                    alert(data.info);
                }
            }
        });
    }
    // 不换算单位
    Highcharts.setOptions({
        lang: {
            numericSymbols: null
        }
    })
    var chart = new Highcharts.Chart({
        chart: {
            type: 'column',
            renderTo: 'disk_space_hc',
            style: {
                fontFamily: 'Open Sans'
            }
        },
        title: {
            text: '每月磁盘数据',
            x: -20 //center
        },

        xAxis: {
            title: {
                text: '时间'
            },
            reversed: true,
        },
        colors: [
            '#3598dc',
            '#e7505a',
            '#32c5d2',
            '#8e44ad',
        ],
        yAxis: {
            title: {
                text: '容量 (GB)'
            },
            plotLines: [{
                value: 0,
                width: 1,
                color: '#808080'
            }]
        },
        tooltip: {
            valueSuffix: 'GB'
        },
        legend: {
            layout: 'vertical',
            align: 'right',
            verticalAlign: 'middle',
            borderWidth: 0
        },
        series: [{}]
    });

    function setDiskSpaceChart(chart, data) {
        while (chart.series.length > 0) {
            chart.series[0].remove(true);
        }

        // 设置横轴
        chart.xAxis[0].setCategories(data.categories);

        var disk_list = data.disk_list;
        for (var i = 0; i < disk_list.length; i++) {
            chart.addSeries({
                "name": disk_list[i].name,
                "data": disk_list[i].capacity_list,
                "color": disk_list[i].color,
            });
        }
    }

    $('#disk_space tbody').on('click', 'button#edit', function() {
        var media_id = $(this).find('input').val();
        var utils_id = $("#utils_manage").val();
        $.ajax({
            type: "POST",
            url: "../get_disk_space_daily/",
            data: {
                media_id: media_id,
                utils_id: utils_id
            },
            success: function(data) {
                setDiskSpaceChart(chart, data);
            }
        });
    });

    getDiskSpace($('#utils_manage').val());

    $('#utils_manage').change(function() {
        $("tbody").empty();
        $("#loading").show();
        getDiskSpace($(this).val());
        getMADiskSpace();
    });


    $('#weekly_total_space').click(function() {
        $.ajax({
            type: "POST",
            url: "../get_disk_space_daily/",
            data: {
                utils_id: $("#utils_manage").val()
            },
            success: function(data) {
                setDiskSpaceChart(chart, data);
            },
            error: function() {
                console.log('error')
            }
        });
    })
});