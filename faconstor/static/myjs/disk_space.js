$(document).ready(function () {
    $("#loading").show();
    var pie_chart = new Highcharts.Chart({
        chart: {
            plotBackgroundColor: null,
            plotBorderWidth: null,
            plotShadow: false,
            type: 'pie',
            renderTo: 'disk_space_container'
        },
        title: {
            text: '磁盘容量'
        },
        tooltip: {
            pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
        },
        plotOptions: {
            DiskSpace: {
                allowPointSelect: true,
                cursor: 'pointer',
                dataLabels: {
                    enabled: true,
                    format: '<b>{point.name}</b>: {point.percentage:.1f} %',
                    style: {
                        color: (Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black'
                    }
                }
            }
        },
        series: [{
            name: 'DiskSpace',
            colorByPoint: true,
            data: []
        }]
    });

    function getMADiskSpace() {
        pie_chart.series[0].setData([])
        $.ajax({
            type: "POST",
            url: "../get_ma_disk_space/",
            data: {
                utils_id: $("#utils_manage").val(),
            },
            success: function (data) {
                //定义一个数组
                var browsers = []
                //迭代，把异步获取的数据放到数组中
                $.each(data.data, function (i, d) {
                    browsers.push([d.name, d.y]);
                });
                //设置数据
                pie_chart.series[0].setData(browsers);
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
            success: function (data) {
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
                        var CapacityAvailable = (disk_space[i]["CapacityAvailable"]/1024).toFixed(0)
                        var SpaceReserved = (disk_space[i]["SpaceReserved"]/1024).toFixed(0)
                        var TotalSpaceMB = (disk_space[i]["TotalSpaceMB"]/1024).toFixed(0)

                        $("tbody").append(
                            '<tr>' +
                            '<td rowspan="' + disk_space[i].display_name_rowspan + '" style="vertical-align:middle; ' + display_name_hidden + '">' + sort + '</td>' +
                            '<td rowspan="' + disk_space[i].display_name_rowspan + '" style="vertical-align:middle; ' + display_name_hidden + '">' + disk_space[i]["DisplayName"] + '</td>' +
                            '<td rowspan="' + disk_space[i].library_name_rowspan + '" style="vertical-align:middle; ' + library_name_hidden + '">' + disk_space[i]["LibraryName"] + '</td>' +
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

    chart = new Highcharts.Chart({
        chart: {
            renderTo: 'disk_space_hc',
            style: {
                fontFamily: 'Open Sans'
            }
        },
        title: {
            text: '每周磁盘数据',
            x: -20 //center
        },

        xAxis: {
            title: {
                text: '周'
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
    })

    $('#disk_space tbody').on('click', 'button#edit', function () {
        var media_id = $(this).find('input').val();
        var utils_id = $("#utils_manage").val();
        $.ajax({
            type: "POST",
            url: "../get_disk_space_daily/",
            data: {
                media_id: media_id,
                utils_id: utils_id
            },
            success: function (data) {
                while (chart.series.length > 0) {
                    chart.series[0].remove(true);
                }
                for (var i = 0; i < data.data.length; i++) {
                    chart.addSeries({
                        "name": data.data[i].name,
                        "data": data.data[i].capacity_list,
                        "color": data.data[i].color,
                    });
                }
                // 动态生成横坐标
                // 从1开始
                var category_list = [];
                for (var j = 1; j <= 20; j++) {
                    category_list.push(j)
                }
                chart.xAxis[0].setCategories(category_list);
            }
        });
    });

    getDiskSpace($('#utils_manage').val());

    $('#utils_manage').change(function () {
        $("tbody").empty();
        $("#loading").show();
        getDiskSpace($(this).val());
        getMADiskSpace();
    });


    $('#weekly_total_space').click(function () {
        console.log(1)
        $.ajax({
            type: "POST",
            url: "../get_disk_space_daily/",
            data: {
                utils_id: $("#utils_manage").val()
            },
            success: function (data) {
                console.log(data)
                while (chart.series.length > 0) {
                    chart.series[0].remove(true);
                }
                for (var i = 0; i < data.data.length; i++) {
                    chart.addSeries({
                        "name": data.data[i].name,
                        "data": data.data[i].capacity_list,
                        "color": data.data[i].color,
                    });
                }
                // 动态生成横坐标
                // 从1开始
                var category_list = [];
                for (var j = 1; j <= 20; j++) {
                    category_list.push(j)
                }
                chart.xAxis[0].setCategories(category_list);
            },
            error: function () {
                console.log('error')
            }
        });
    })
});