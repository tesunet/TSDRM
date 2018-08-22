var Dashboard = function () {

    return {

        initJQVMAP: function () {
            if (!jQuery().vectorMap) {
                return;
            }

            var showMap = function (name) {
                jQuery('.vmaps').hide();
                jQuery('#vmap_' + name).show();
            }

            var setMap = function (name) {
                var data = {
                    map: 'world_en',
                    backgroundColor: null,
                    borderColor: '#333333',
                    borderOpacity: 0.5,
                    borderWidth: 1,
                    color: '#c6c6c6',
                    enableZoom: true,
                    hoverColor: '#c9dfaf',
                    hoverOpacity: null,
                    values: sample_data,
                    normalizeFunction: 'linear',
                    scaleColors: ['#b6da93', '#909cae'],
                    selectedColor: '#c9dfaf',
                    selectedRegion: null,
                    showTooltip: true,
                    onLabelShow: function (event, label, code) {

                    },
                    onRegionOver: function (event, code) {
                        if (code == 'ca') {
                            event.preventDefault();
                        }
                    },
                    onRegionClick: function (element, code, region) {
                        var message = 'You clicked "' + region + '" which has the code: ' + code.toUpperCase();
                        alert(message);
                    }
                };

                data.map = name + '_en';
                var map = jQuery('#vmap_' + name);
                if (!map) {
                    return;
                }
                map.width(map.parent().parent().width());
                map.show();
                map.vectorMap(data);
                map.hide();
            }

            setMap("world");
            setMap("usa");
            setMap("europe");
            setMap("russia");
            setMap("germany");
            showMap("world");

            jQuery('#regional_stat_world').click(function () {
                showMap("world");
            });

            jQuery('#regional_stat_usa').click(function () {
                showMap("usa");
            });

            jQuery('#regional_stat_europe').click(function () {
                showMap("europe");
            });
            jQuery('#regional_stat_russia').click(function () {
                showMap("russia");
            });
            jQuery('#regional_stat_germany').click(function () {
                showMap("germany");
            });

            $('#region_statistics_loading').hide();
            $('#region_statistics_content').show();

            App.addResizeHandler(function () {
                jQuery('.vmaps').each(function () {
                    var map = jQuery(this);
                    map.width(map.parent().width());
                });
            });
        },

        initCalendar: function () {
            if (!jQuery().fullCalendar) {
                return;
            }

            var date = new Date();
            var d = date.getDate();
            var m = date.getMonth();
            var y = date.getFullYear();

            var h = {};

            if ($('#calendar').width() <= 400) {
                $('#calendar').addClass("mobile");
                h = {
                    left: 'title, prev, next',
                    center: '',
                    right: 'today,month,agendaWeek,agendaDay'
                };
            } else {
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
            }


            $('#calendar').fullCalendar('destroy'); // destroy the calendar
            $('#calendar').fullCalendar({ //re-initialize the calendar
                disableDragging: false,
                header: h,
                editable: true,
                events: [{
                    title: 'All Day',
                    start: new Date(y, m, 1),
                    backgroundColor: App.getBrandColor('yellow')
                }, {
                    title: 'Long Event',
                    start: new Date(y, m, d - 5),
                    end: new Date(y, m, d - 2),
                    backgroundColor: App.getBrandColor('blue')
                }, {
                    title: 'Repeating Event',
                    start: new Date(y, m, d - 3, 16, 0),
                    allDay: false,
                    backgroundColor: App.getBrandColor('red')
                }, {
                    title: 'Repeating Event',
                    start: new Date(y, m, d + 6, 16, 0),
                    allDay: false,
                    backgroundColor: App.getBrandColor('green')
                }, {
                    title: 'Meeting',
                    start: new Date(y, m, d + 9, 10, 30),
                    allDay: false
                }, {
                    title: 'Lunch',
                    start: new Date(y, m, d, 14, 0),
                    end: new Date(y, m, d, 14, 0),
                    backgroundColor: App.getBrandColor('grey'),
                    allDay: false
                }, {
                    title: 'Birthday',
                    start: new Date(y, m, d + 1, 19, 0),
                    end: new Date(y, m, d + 1, 22, 30),
                    backgroundColor: App.getBrandColor('purple'),
                    allDay: false
                }, {
                    title: 'Click for Google',
                    start: new Date(y, m, 28),
                    end: new Date(y, m, 29),
                    backgroundColor: App.getBrandColor('yellow'),
                    url: 'http://google.com/'
                }]
            });
        },

        initCharts: function () {
            if (!jQuery.plot) {
                return;
            }

            function showChartTooltip(x, y, xValue, yValue) {
                $('<div id="tooltip" class="chart-tooltip">' + yValue + '<\/div>').css({
                    position: 'absolute',
                    display: 'none',
                    top: y - 40,
                    left: x - 40,
                    border: '0px solid #ccc',
                    padding: '2px 6px',
                    'background-color': '#fff'
                }).appendTo("body").fadeIn(200);
            }

            var data = [];
            var totalPoints = 250;

            // random data generator for plot charts

            function getRandomData() {
                if (data.length > 0) data = data.slice(1);
                // do a random walk
                while (data.length < totalPoints) {
                    var prev = data.length > 0 ? data[data.length - 1] : 50;
                    var y = prev + Math.random() * 10 - 5;
                    if (y < 0) y = 0;
                    if (y > 100) y = 100;
                    data.push(y);
                }
                // zip the generated y values with the x values
                var res = [];
                for (var i = 0; i < data.length; ++i) res.push([i, data[i]])
                return res;
            }

            function randValue() {
                return (Math.floor(Math.random() * (1 + 50 - 20))) + 10;
            }

            var visitors = [
                ['02/2013', 1500],
                ['03/2013', 2500],
                ['04/2013', 1700],
                ['05/2013', 800],
                ['06/2013', 1500],
                ['07/2013', 2350],
                ['08/2013', 1500],
                ['09/2013', 1300],
                ['10/2013', 4600]
            ];


            if ($('#site_statistics').size() != 0) {

                $('#site_statistics_loading').hide();
                $('#site_statistics_content').show();

                var plot_statistics = $.plot($("#site_statistics"), [{
                        data: visitors,
                        lines: {
                            fill: 0.6,
                            lineWidth: 0
                        },
                        color: ['#f89f9f']
                    }, {
                        data: visitors,
                        points: {
                            show: true,
                            fill: true,
                            radius: 5,
                            fillColor: "#f89f9f",
                            lineWidth: 3
                        },
                        color: '#fff',
                        shadowSize: 0
                    }],

                    {
                        xaxis: {
                            tickLength: 0,
                            tickDecimals: 0,
                            mode: "categories",
                            min: 0,
                            font: {
                                lineHeight: 14,
                                style: "normal",
                                variant: "small-caps",
                                color: "#6F7B8A"
                            }
                        },
                        yaxis: {
                            ticks: 5,
                            tickDecimals: 0,
                            tickColor: "#eee",
                            font: {
                                lineHeight: 14,
                                style: "normal",
                                variant: "small-caps",
                                color: "#6F7B8A"
                            }
                        },
                        grid: {
                            hoverable: true,
                            clickable: true,
                            tickColor: "#eee",
                            borderColor: "#eee",
                            borderWidth: 1
                        }
                    });

                var previousPoint = null;
                $("#site_statistics").bind("plothover", function (event, pos, item) {
                    $("#x").text(pos.x.toFixed(2));
                    $("#y").text(pos.y.toFixed(2));
                    if (item) {
                        if (previousPoint != item.dataIndex) {
                            previousPoint = item.dataIndex;

                            $("#tooltip").remove();
                            var x = item.datapoint[0].toFixed(2),
                                y = item.datapoint[1].toFixed(2);

                            showChartTooltip(item.pageX, item.pageY, item.datapoint[0], item.datapoint[1] + ' visits');
                        }
                    } else {
                        $("#tooltip").remove();
                        previousPoint = null;
                    }
                });
            }


            if ($('#site_activities').size() != 0) {
                //site activities
                var previousPoint2 = null;
                $('#site_activities_loading').hide();
                $('#site_activities_content').show();

                var data1 = [
                    ['DEC', 300],
                    ['JAN', 600],
                    ['FEB', 1100],
                    ['MAR', 1200],
                    ['APR', 860],
                    ['MAY', 1200],
                    ['JUN', 1450],
                    ['JUL', 1800],
                    ['AUG', 1200],
                    ['SEP', 600]
                ];


                var plot_statistics = $.plot($("#site_activities"),

                    [{
                        data: data1,
                        lines: {
                            fill: 0.2,
                            lineWidth: 0,
                        },
                        color: ['#BAD9F5']
                    }, {
                        data: data1,
                        points: {
                            show: true,
                            fill: true,
                            radius: 4,
                            fillColor: "#9ACAE6",
                            lineWidth: 2
                        },
                        color: '#9ACAE6',
                        shadowSize: 1
                    }, {
                        data: data1,
                        lines: {
                            show: true,
                            fill: false,
                            lineWidth: 3
                        },
                        color: '#9ACAE6',
                        shadowSize: 0
                    }],

                    {

                        xaxis: {
                            tickLength: 0,
                            tickDecimals: 0,
                            mode: "categories",
                            min: 0,
                            font: {
                                lineHeight: 18,
                                style: "normal",
                                variant: "small-caps",
                                color: "#6F7B8A"
                            }
                        },
                        yaxis: {
                            ticks: 5,
                            tickDecimals: 0,
                            tickColor: "#eee",
                            font: {
                                lineHeight: 14,
                                style: "normal",
                                variant: "small-caps",
                                color: "#6F7B8A"
                            }
                        },
                        grid: {
                            hoverable: true,
                            clickable: true,
                            tickColor: "#eee",
                            borderColor: "#eee",
                            borderWidth: 1
                        }
                    });

                $("#site_activities").bind("plothover", function (event, pos, item) {
                    $("#x").text(pos.x.toFixed(2));
                    $("#y").text(pos.y.toFixed(2));
                    if (item) {
                        if (previousPoint2 != item.dataIndex) {
                            previousPoint2 = item.dataIndex;
                            $("#tooltip").remove();
                            var x = item.datapoint[0].toFixed(2),
                                y = item.datapoint[1].toFixed(2);
                            showChartTooltip(item.pageX, item.pageY, item.datapoint[0], item.datapoint[1] + 'M$');
                        }
                    }
                });

                $('#site_activities').bind("mouseleave", function () {
                    $("#tooltip").remove();
                });
            }
        },

        initEasyPieCharts: function () {
            if (!jQuery().easyPieChart) {
                return;
            }

            $('.easy-pie-chart .number.transactions').easyPieChart({
                animate: 1000,
                size: 75,
                lineWidth: 3,
                barColor: App.getBrandColor('yellow')
            });

            $('.easy-pie-chart .number.visits').easyPieChart({
                animate: 1000,
                size: 75,
                lineWidth: 3,
                barColor: App.getBrandColor('green')
            });

            $('.easy-pie-chart .number.bounce').easyPieChart({
                animate: 1000,
                size: 75,
                lineWidth: 3,
                barColor: App.getBrandColor('red')
            });

            $('.easy-pie-chart-reload').click(function () {
                $('.easy-pie-chart .number').each(function () {
                    var newValue = Math.floor(100 * Math.random());
                    $(this).data('easyPieChart').update(newValue);
                    $('span', this).text(newValue);
                });
            });
        },

        initSparklineCharts: function () {
            if (!jQuery().sparkline) {
                return;
            }
            $("#sparkline_bar").sparkline([8, 9, 10, 11, 10, 10, 12, 10, 10, 11, 9, 12, 11, 10, 9, 11, 13, 13, 12], {
                type: 'bar',
                width: '100',
                barWidth: 5,
                height: '55',
                barColor: '#35aa47',
                negBarColor: '#e02222'
            });

            $("#sparkline_bar2").sparkline([9, 11, 12, 13, 12, 13, 10, 14, 13, 11, 11, 12, 11, 11, 10, 12, 11, 10], {
                type: 'bar',
                width: '100',
                barWidth: 5,
                height: '55',
                barColor: '#ffb848',
                negBarColor: '#e02222'
            });

            $("#sparkline_bar5").sparkline([8, 9, 10, 11, 10, 10, 12, 10, 10, 11, 9, 12, 11, 10, 9, 11, 13, 13, 12], {
                type: 'bar',
                width: '100',
                barWidth: 5,
                height: '55',
                barColor: '#35aa47',
                negBarColor: '#e02222'
            });

            $("#sparkline_bar6").sparkline([9, 11, 12, 13, 12, 13, 10, 14, 13, 11, 11, 12, 11, 11, 10, 12, 11, 10], {
                type: 'bar',
                width: '100',
                barWidth: 5,
                height: '55',
                barColor: '#ffb848',
                negBarColor: '#e02222'
            });

            $("#sparkline_line").sparkline([9, 10, 9, 10, 10, 11, 12, 10, 10, 11, 11, 12, 11, 10, 12, 11, 10, 12], {
                type: 'line',
                width: '100',
                height: '55',
                lineColor: '#ffb848'
            });
        },

        initMorisCharts: function () {
            if (Morris.EventEmitter && $('#sales_statistics').size() > 0) {
                // Use Morris.Area instead of Morris.Line
                dashboardMainChart = Morris.Area({
                    element: 'sales_statistics',
                    padding: 0,
                    behaveLikeLine: false,
                    gridEnabled: false,
                    gridLineColor: false,
                    axes: false,
                    fillOpacity: 1,
                    data: [{
                        period: '2011 Q1',
                        sales: 1400,
                        profit: 400
                    }, {
                        period: '2011 Q2',
                        sales: 1100,
                        profit: 600
                    }, {
                        period: '2011 Q3',
                        sales: 1600,
                        profit: 500
                    }, {
                        period: '2011 Q4',
                        sales: 1200,
                        profit: 400
                    }, {
                        period: '2012 Q1',
                        sales: 1550,
                        profit: 800
                    }],
                    lineColors: ['#399a8c', '#92e9dc'],
                    xkey: 'period',
                    ykeys: ['sales', 'profit'],
                    labels: ['Sales', 'Profit'],
                    pointSize: 0,
                    lineWidth: 0,
                    hideHover: 'auto',
                    resize: true
                });

            }
        },

        initChat: function () {
            var cont = $('#chats');
            var list = $('.chats', cont);
            var form = $('.chat-form', cont);
            var input = $('input', form);
            var btn = $('.btn', form);

            var handleClick = function (e) {
                e.preventDefault();

                var text = input.val();
                if (text.length == 0) {
                    return;
                }

                var time = new Date();
                var time_str = (time.getHours() + ':' + time.getMinutes());
                var tpl = '';
                tpl += '<li class="out">';
                tpl += '<img class="avatar" alt="" src="' + Layout.getLayoutImgPath() + 'avatar1.jpg"/>';
                tpl += '<div class="message">';
                tpl += '<span class="arrow"></span>';
                tpl += '<a href="#" class="name">Bob Nilson</a>&nbsp;';
                tpl += '<span class="datetime">at ' + time_str + '</span>';
                tpl += '<span class="body">';
                tpl += text;
                tpl += '</span>';
                tpl += '</div>';
                tpl += '</li>';

                var msg = list.append(tpl);
                input.val("");

                var getLastPostPos = function () {
                    var height = 0;
                    cont.find("li.out, li.in").each(function () {
                        height = height + $(this).outerHeight();
                    });

                    return height;
                }

                cont.find('.scroller').slimScroll({
                    scrollTo: getLastPostPos()
                });
            }

            $('body').on('click', '.message .name', function (e) {
                e.preventDefault(); // prevent click event

                var name = $(this).text(); // get clicked user's full name
                input.val('@' + name + ':'); // set it into the input field
                App.scrollTo(input); // scroll to input if needed
            });

            btn.click(handleClick);

            input.keypress(function (e) {
                if (e.which == 13) {
                    handleClick(e);
                    return false; //<---- Add this line
                }
            });
        },

        initDashboardDaterange: function () {
            if (!jQuery().daterangepicker) {
                return;
            }

            $('#dashboard-report-range').daterangepicker({
                "ranges": {
                    'Today': [moment(), moment()],
                    'Yesterday': [moment().subtract('days', 1), moment().subtract('days', 1)],
                    'Last 7 Days': [moment().subtract('days', 6), moment()],
                    'Last 30 Days': [moment().subtract('days', 29), moment()],
                    'This Month': [moment().startOf('month'), moment().endOf('month')],
                    'Last Month': [moment().subtract('month', 1).startOf('month'), moment().subtract('month', 1).endOf('month')]
                },
                "locale": {
                    "format": "MM/DD/YYYY",
                    "separator": " - ",
                    "applyLabel": "Apply",
                    "cancelLabel": "Cancel",
                    "fromLabel": "From",
                    "toLabel": "To",
                    "customRangeLabel": "Custom",
                    "daysOfWeek": [
                        "Su",
                        "Mo",
                        "Tu",
                        "We",
                        "Th",
                        "Fr",
                        "Sa"
                    ],
                    "monthNames": [
                        "January",
                        "February",
                        "March",
                        "April",
                        "May",
                        "June",
                        "July",
                        "August",
                        "September",
                        "October",
                        "November",
                        "December"
                    ],
                    "firstDay": 1
                },
                //"startDate": "11/08/2015",
                //"endDate": "11/14/2015",
                opens: (App.isRTL() ? 'right' : 'left'),
            }, function (start, end, label) {
                $('#dashboard-report-range span').html(start.format('MMMM D, YYYY') + ' - ' + end.format('MMMM D, YYYY'));
            });

            $('#dashboard-report-range span').html(moment().subtract('days', 29).format('MMMM D, YYYY') + ' - ' + moment().format('MMMM D, YYYY'));
            $('#dashboard-report-range').show();
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

        initWorldMapStats: function () {
            if ($('#mapplic').size() === 0) {
                return;
            }

            $('#mapplic').mapplic({
                source: '../assets/global/plugins/mapplic/world.json',
                height: 265,
                animate: false,
                sidebar: false,
                minimap: false,
                locations: true,
                deeplinking: true,
                fullscreen: false,
                hovertip: true,
                zoombuttons: false,
                clearbutton: false,
                developer: false,
                maxscale: 2,
                skin: 'mapplic-dark',
                zoom: true
            });

            $("#widget_sparkline_bar").sparkline([8, 7, 9, 8.5, 8, 8.2, 8, 8.5, 9, 8, 9], {
                type: 'bar',
                width: '100',
                barWidth: 5,
                height: '30',
                barColor: '#4db3a4',
                negBarColor: '#e02222'
            });

            $("#widget_sparkline_bar2").sparkline([8, 7, 9, 8.5, 8, 8.2, 8, 8.5, 9, 8, 9], {
                type: 'bar',
                width: '100',
                barWidth: 5,
                height: '30',
                barColor: '#f36a5a',
                negBarColor: '#e02222'
            });

            $("#widget_sparkline_bar3").sparkline([8, 7, 9, 8.5, 8, 8.2, 8, 8.5, 9, 8, 9], {
                type: 'bar',
                width: '100',
                barWidth: 5,
                height: '30',
                barColor: '#5b9bd1',
                negBarColor: '#e02222'
            });

            $("#widget_sparkline_bar4").sparkline([8, 7, 9, 8.5, 8, 8.2, 8, 8.5, 9, 8, 9], {
                type: 'bar',
                width: '100',
                barWidth: 5,
                height: '30',
                barColor: '#9a7caf',
                negBarColor: '#e02222'
            });
        },

        init: function () {

            this.initJQVMAP();
            this.initCalendar();
            this.initCharts();
            this.initEasyPieCharts();
            this.initSparklineCharts();
            this.initChat();
            this.initDashboardDaterange();
            this.initMorisCharts();

            this.initAmChart1();
            this.initAmChart2();
            this.initAmChart3();
            this.initAmChart4();

            this.initWorldMapStats();
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




