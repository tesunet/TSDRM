var csrfToken = $("[name='csrfmiddlewaretoken']").val();
var state = '',
    interval = 0,
    tmInterval = 0,
    headerTitle = '';
var allState = ['run', 'done', 'error', 'stop', 'confirm', 'edit'];
var util = {
    run: function () {
        util.initExtend();
        util.request();
        interval = setInterval(function () {
            if (state === 'DONE') {
                clearInterval(interval);
            }
            util.request();
        }, 3 * 1000); //3秒/次请求
    },
    request: function () {
        $.ajax({
            url: '/get_process_index_data/', //这里面是请求的接口地址
            type: 'POST',
            data: {
                p_run_id: $("#process_run_id").val(),
                csrfmiddlewaretoken: csrfToken
            },
            timeout: 2000,
            dataType: 'json',
            success: function (data) {
                util.makeHtml(data);
            },
            // error: function(xhr) {
            //     alert('网络错误')
            // }
        });
    },
    makeHtml: function (data) {
        state = data.state;
        if (headerTitle === '') {
            headerTitle = data.name;
            var process_run_url = $("#process_url").val() + "/" + $("#process_run_id").val()
            $('.header-title h2').html("<a href='"+ process_run_url +"' target='_parent' style='color:#778899'>"+headerTitle+"</a>");
        }

        var progressBar = $('.progress-par');
        var percent = parseInt(data.percent);
        progressBar.attr('style', 'width:' + percent + '%');
        progressBar.find('i').text(percent + '%');
        progressBar.addClass(state.toLocaleLowerCase());

        $('.progress-left-time').text(data.starttime);
        $('.progress-right-time').text(data.endtime);

        util.makeTimer(data.rtostate, data.starttime, data.endtime, data.rtoendtime);

        var leftData = [];
        var rightData = [];
        var curStep = [];
        var curIndex = 0;
        for (var j = 0; j < data.steps.length; j++) {
            if (data.steps[j].type === 'cur') {
                curIndex = j;
                break;
            }
        }
        for (var i = 0; i < data.steps.length; i++) {
            if (i === curIndex) {
                curStep = data.steps[i];
            } else if (i < curIndex) {
                leftData.push(data.steps[i]);
            } else {
                rightData.push(data.steps[i]);
            }
        }

        //current step
        var loadingNow = $(".progress-ring");
        var color = {
            run: '#5091C7',
            done: '#32c5d2 ',
            stop: '#ff0000',
            error: '#ff0000',
            confirm: '#e0b200',
            edit: '#c4c4c4'
        };
        var curState = curStep.state.toLocaleLowerCase();
        loadingNow.attr('data-name', curStep.name);
        loadingNow.attr('data-percent', curStep.percent);
        loadingNow.attr('data-color', '#f0f0f0,' + color[curState]);
        loadingNow.loadingNow();

        util.makeR(rightData);
        util.makeL(leftData);

        var stateArr = ['DONE', 'STOP', 'ERROR'];
        if ($.inArray(state, stateArr) >= 0) {
            setTimeout(function () {
                $('.progress-par span').css({
                    'background': 'url("/static/processindex/images/done.png") no-repeat',
                    'background-size': '90px 70px'
                });
            }, 1 * 1000);
            clearInterval(interval);
            clearInterval(tmInterval);
        }
    },
    makeR: function (rightData) {
        for (var n = 0; n < 4; n++) {
            var rbox1 = $('.rbox-' + (n + 1));
            rbox1.find('.con-text').html('<div class="text"></div>');
            for (var c = 0; c < allState.length; c++) {
                rbox1.removeClass('step-' + allState[c]);
            }
            rbox1.hide();
        }
        if (rightData.length > 0) {
            var rindex = 1;
            for (var i = 0; i < rightData.length; i++) {
                if (rindex > 4) {
                    break;
                }
                var rbox = $('.rbox-' + (i + 1));
                var html = rightData[i].name;
                rbox.find('.con-text').html('<div class="text"><p>' + html + '</p></div>');
                rbox.addClass('step-' + rightData[i].state.toLocaleLowerCase());
                rbox.show();
                rindex++;
            }
        }
    },
    makeL: function (leftData) {
        for (var n = 0; n < 4; n++) {
            var lbox1 = $('.lbox-' + (n + 1));
            lbox1.find('.con-text').html('<div class="text"></div>');
            for (var c = 0; c < allState.length; c++) {
                lbox1.removeClass('step-' + allState[c]);
            }
            lbox1.hide();
        }
        if (leftData.length > 0) {
            leftData = leftData.reverse();
            var index = 1;
            for (var i = 0; i < leftData.length; i++) {
                if (index > 4) {
                    break;
                }
                var lbox = $('.lbox-' + (i + 1));
                lbox.show();
                var html = '<p>' + leftData[i].name + '</p>';
                if (leftData[i].state.toLocaleLowerCase() === 'done') {
                    var timer = util.getTimerByIndex(i, leftData[i].starttime, leftData[i].endtime);
                    html += '<em>' + timer + '</em>';
                }
                lbox.find('.con-text').html('<div class="text">' + html + '</div>');
                lbox.addClass('step-' + leftData[i].state.toLocaleLowerCase());
                index++;
            }
        }
    },
    getTimerByIndex: function (index, startTime, endTime) {
        var timer = util.timeFn(startTime, endTime);
        var str = '';
        switch (index) {
            case 0:
            case 1:
                str = timer.hours + '小时' + timer.minutes + '分' + timer.seconds + '秒';
                break;
            case 2:
                str = timer.minutes + '分' + timer.seconds + '秒';
                break;
            case 3:
                str = timer.seconds + '秒';
                break;
            default:
                str = timer.hours + '小时' + timer.minutes + '分' + timer.seconds + '秒';
        }

        return str;
    },
    makeTimer: function (state, starTime, endTime, rtoEndTime) {
        var timer;
        if (state === 'DONE') {
            clearInterval(tmInterval);
            timer = util.timeFn(starTime, rtoEndTime);
            util.showTimer(timer);
        } else {
            if (!tmInterval) {
                clearInterval(tmInterval);
                tmInterval = setInterval(function () {
                    timer = util.timeFn(starTime, util.getNow());
                    util.showTimer(timer);
                }, 1 * 1000); //定时刷新时间
            }
        }
    },
    showTimer: function (timer) {
        var hours = timer.hours.split('');
        var minutes = timer.minutes.split('');
        var seconds = timer.seconds.split('');
        var headerTimeLi = $('.header-timeout li');
        headerTimeLi.eq(1).find('span').text(hours[0]);
        headerTimeLi.eq(2).find('span').text(hours[1]);
        headerTimeLi.eq(4).find('span').text(minutes[0]);
        headerTimeLi.eq(5).find('span').text(minutes[1]);
        headerTimeLi.eq(7).find('span').text(seconds[0]);
        headerTimeLi.eq(8).find('span').text(seconds[1]);
    },
    initExtend: function () {
        $.fn.loadingNow = function () {
            var defaultOpt = {
                trackColor: '#f0f0f0',
                progressColor: '#72B6E3',
                percent: 75,
                duration: 2000
            }; // 默认选项
            $(this).each(function () {
                var $target = $(this);
                var color = $target.data('color'); // 颜色
                var percent = parseInt($target.data('percent'), 10); // 百分比
                var duration = parseFloat($target.data('duration'), 10) * 1000; // 持续时间
                var trackColor, progressColor;
                if (color && color.split(',').length === 2) {
                    var colorSet = color.split(',');
                    trackColor = colorSet[0];
                    progressColor = colorSet[1];
                } else {
                    trackColor = defaultOpt.trackColor;
                    progressColor = defaultOpt.progressColor;
                }
                if (!percent)
                    percent = defaultOpt.percent;
                if (!duration)
                    duration = defaultOpt.duration;

                var textName = $target.attr('data-name');

                $target.html('<div class="inner-progress"></div><div class="progress-track"></div><div class="progress-left"></div><div class="progress-right"></div><div class="progress-cover"></div><div class="progress-text"><p>' + textName + '</p><p>' + percent + '%</p></div>');

                var x = $target.find('.progress-cover').height(); // 触发 Layout
                // http://stackoverflow.com/questions/12088819/css-transitions-on-new-elements

                $target.find('.progress-track, .progress-cover').css('border-color', trackColor);
                $target.find('.progress-left, .progress-right').css('border-color', progressColor);

                $target.find('.progress-left').css({
                    'transform': 'rotate(' + percent * 3.6 + 'deg)',
                    '-o-transform': 'rotate(' + percent * 3.6 + 'deg)',
                    '-ms-transform': 'rotate(' + percent * 3.6 + 'deg)',
                    '-moz-transform': 'rotate(' + percent * 3.6 + 'deg)',
                    '-webkit-transform': 'rotate(' + percent * 3.6 + 'deg)',
                    'transition': 'transform ' + duration + 'ms linear',
                    '-o-transition': '-o-transform ' + duration + 'ms linear',
                    '-ms-transition': '-ms-transform ' + duration + 'ms linear',
                    '-moz-transition': '-moz-transform ' + duration + 'ms linear',
                    '-webkit-transition': '-webkit-transform ' + duration + 'ms linear'
                });

                if (percent > 50) {
                    var animation = 'toggle ' + (duration * 50 / percent) + 'ms'
                    $target.find('.progress-right').css({
                        'opacity': 1,
                        'animation': animation,
                        'animation-timing-function': 'step-end'
                    });
                    $target.find('.progress-cover').css({
                        'opacity': 0,
                        'animation': animation,
                        'animation-timing-function': 'step-start'
                    });
                }
            });
        }
    },
    timeFn: function (d1, d2) {
        var dateBegin = new Date(d1.replace(/-/g, "/"));
        var dateEnd = new Date(d2.replace(/-/g, "/"));
        var dateDiff = dateEnd.getTime() - dateBegin.getTime();
        var dayDiff = Math.floor(dateDiff / (24 * 3600 * 1000));
        var leave1 = dateDiff % (24 * 3600 * 1000); //计算天数后剩余的毫秒数
        var hours = Math.floor(leave1 / (3600 * 1000)); //计算出小时数
        //计算相差分钟数
        var leave2 = leave1 % (3600 * 1000); //计算小时数后剩余的毫秒数
        var minutes = Math.floor(leave2 / (60 * 1000)); //计算相差分钟数
        //计算相差秒数
        var leave3 = leave2 % (60 * 1000); //计算分钟数后剩余的毫秒数
        var seconds = Math.round(leave3 / 1000);

        console.log(hours);
        console.log(minutes);
        console.log(seconds);
        hours = hours < 10 ? '0' + hours : '' + hours;
        minutes = minutes < 10 ? '0' + minutes : '' + minutes;
        seconds = seconds < 10 ? '0' + seconds : '' + seconds;
        return {hours: hours, minutes: minutes, seconds: seconds};
    },
    getNow: function () {
        var d = new Date();
        var now = d.getFullYear() + "-" + (d.getMonth() + 1) + "-" + d.getDate() + " " + d.getHours() + ":" + d.getMinutes() + ":" + d.getSeconds();
        return now;
    }
};
window.util = util;