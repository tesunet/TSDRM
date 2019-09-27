﻿﻿var csrfToken = $("[name='csrfmiddlewaretoken']").val();
var walkthrough_state=""
    refresh= true,
    interval = 0,
    tmInterval = 0,
    headerTitle = '',
    end = false;
var allState = ['run', 'done', 'error', 'stop', 'confirm', 'edit'];
var util = {
    run: function () {
        util.request();
        interval = setInterval(function () {
            util.request();
        }, 3 * 1000); //3秒/次请求
    },
    request: function () {
        if(refresh) {
            $.ajax({
                url: '/get_walkthrough_index_data/', //这里面是请求的接口地址
                //url: '/static/processindex/data.json', //这里面是请求的接口地址
                type: 'POST',
                data: {
                    walkthrough_id: $("#walkthrough_id").val(),
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
        }
    },
    makeHtml: function (walkthroughindexdata) {
        walkthrough_state = walkthroughindexdata.walkthrough_state;
        var sTag = $("#s_tag").val()
         util.makeCommand(walkthroughindexdata.showtasks,walkthroughindexdata.oldwalkthroughinfo.showtasks);
        // 判断是否为计划

        if (walkthrough_state === "PLAN") {
            $(".walkthrough_run").hide();
            $(".header-timeout").hide();
            $(".end_pic").hide();
            $(".start_hand").show();

        } else if (walkthrough_state === "DONE" && sTag !== "true") {
            $(".walkthrough_run").hide();
            $(".header-timeout").hide();
            $(".start_hand").hide();
            $(".end_pic").show();
        } else {
            $(".end_pic").hide();
            $(".start_hand").hide();
            $(".walkthrough_run").show();
            $(".header-timeout").show();
        }

        if (headerTitle === '') {
            var date = new Date;
            var year = date.getFullYear();
            $('.header-title h1').html("<span >" + year + "太平资产自动化灾备演练" + "</span>");
        }
        $(".progress_list").html("");
        $(".end").html("");
        curstate="DONE"
        for (var processnum = 0; processnum < walkthroughindexdata.processruns.length; processnum++) {
            data=walkthroughindexdata.processruns[processnum]
            olddata=null
            if (walkthroughindexdata.oldwalkthroughinfo.processruns) {
                for (var oldprocessnum = 0; oldprocessnum < walkthroughindexdata.oldwalkthroughinfo.processruns.length; oldprocessnum++) {
                    if (data.processrun_id == walkthroughindexdata.oldwalkthroughinfo.processruns[oldprocessnum].processrun_id) {
                        olddata = walkthroughindexdata.oldwalkthroughinfo.processruns[oldprocessnum]
                        break
                    }
                }
            }

            if(data.state!="DONE")
                curstate=""

            if(data.walkthroughstate=="DONE")
                $(".progress_list").append("<div class=\"processname1\"><h3>" + data.name + "</h3> </div>");
            else if(data.walkthroughstate=="RUN")
                $(".progress_list").append("<div class=\"processname\"><h3>" + data.name + "</h3> </div>");
            else
                $(".progress_list").append("<div class=\"processname2\"><h3>" + data.name + "</h3> </div>");

            if(data.state=="DONE"){
                if(olddata) {
                    if (olddata.state == "DONE")
                        $(".end").append("<div class=\"endprocess3\"><h3>" + data.name + "</h3></div>");
                    else
                        $(".end").append("<div class=\"endprocess2\"><h3>" + data.name + "</h3></div>");
                }
                else
                    $(".end").append("<div class=\"endprocess3\"><h3>" + data.name + "</h3></div>");
            }
            else{
                $(".end").append("<input value='" + data.processrun_id + "'  hidden/><div class=\"endprocess\"><h3>" + data.name +  "</h3></div>");
            }


            if (data.walkthroughstate == 'RUN') {
                var state=data.state
                headerTitle = data.name;
                 var process_run_url = data.processurl + "/" + data.processrun_id;
                $('.progress_run h2').html("<a href='" + process_run_url + "' target='_blank' style='color:#e8e8e8 '>" + headerTitle + "</a>");

                var progressBar = $('.progress-par');
                var percent = parseInt(data.percent);
                progressBar.attr('style', 'width:' + percent + '%');
                progressBar.find('i').text(percent + '%')
                for (var cindex = 0; cindex < allState.length; cindex++) {
                    progressBar.removeClass(allState[cindex]);
                }
                progressBar.addClass(state.toLocaleLowerCase());

                $('.progress-left-time').text(data.starttime);
                $('.progress-right-time').text(data.endtime);

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
                var color = {
                    run: '#00a0e9',
                    done: '#87ae64',
                    stop: '#ff0000',
                    error: '#ff0000',
                    confirm: '#e0b200',
                    edit: '#cccfd0'
                };
                var curState = curStep.state.toLocaleLowerCase();
                var curStepPercent = curStep.percent;

                // 启动应用服务步骤：当前时间减去当前步骤开始时间的秒数作为百分比，如未结束，差值大于99，停留在99%。
                // 没有子步骤 不需要确认 有脚本
                if (curStep.c_tag === "yes") {
                    var deltaTime = curStep.delta_time;
                    if (deltaTime <= 99) {
                        curStepPercent = deltaTime
                    } else {
                        curStepPercent = 99
                    }
                }

                Circles.create({
                    id: 'current-circles',
                    radius: 120, //半径宽度，基准100px。半径100，则是200px的宽度
                    value: curStepPercent,
                    maxValue: 100,
                    width: 10, //圆环宽度
                    text: function (value) {
                        return '<div class="inner-progress inner-' + curState + '"></div><div class="inner-progress1"></div><div class="con-text"><div class="text"><p>' + curStep.name + '</p><p>' + value + '%</p></div></div>';
                    },
                    colors: ['#f0f0f0', color[curState]],
                    duration: 400, //动画时长
                    wrpClass: 'circles-wrp',
                    textClass: 'circles-text',
                    styleWrapper: true,
                    styleText: true
                });

                util.makeR(rightData);
                util.makeL(leftData);

                var stateArr = ['DONE', 'STOP', 'ERROR'];
                if ($.inArray(state, stateArr) >= 0) {
                    setTimeout(function () {
                        $('.progress-par span').css({
                            'background': 'url("/static/processindex/images/done.png") no-repeat',
                            'background-size': '180px 140px'
                        });
                    }, 1 * 1000);

                    //停止
                    if ($.inArray(state, ['DONE', 'STOP']) >= 0) {
                        clearInterval(interval);
                        clearInterval(tmInterval);
                        end = true;
                    } else {
                        end = false;
                    }
                    // 步骤出错，仍旧记时
                } else {
                    end = false;
                    $('.progress-par span').css({
                        'background': 'url("/static/processindex/images/loading.gif") no-repeat',
                        'background-size': '180px 140px'
                    });
                }
                $('.progress_run').css({ 'animation': '' });
                if(olddata)
                {
                    if(olddata.walkthroughstate != 'RUN'){
                        $('.progress_run').css({ 'animation': 'bounceIn 1s ease-in-out' });
                    }

                }

                // 写入RTO
                util.makeTimer(walkthroughindexdata.walkthrough_starttime, walkthroughindexdata.walkthrough_endtime);
            }
        }
        $(".endprocess").click(function () {
            var processrun_id = $(this).prev().val();
            $.ajax({
                    url: "/processcontinue/",
                    type: "post",
                    data: {
                        "processrun_id": processrun_id,
                        csrfmiddlewaretoken: csrfToken
                    },
                    success: function (data) {
                        if (data.data == "0") {
                            alert("启动系统关闭程序！");
                        } else {
                            alert("业务人员未完成数据验证，请勿关闭该系统！")
                        }
                    }
                });
           });


        if (curstate === 'DONE') {
            clearInterval(interval);
        }
    },
    makeCommand: function (showtasks,oldshowtasks) {
        var console = $(".console");
        console.html("")
        if (oldshowtasks) {
            var showtext = ""
            for (var i = 0; i < showtasks.length; i++) {
                var isshow=false;
                for(var j = 0; j < oldshowtasks.length; j++) {
                    if (showtasks[i].taskid == oldshowtasks[j].taskid) {
                        isshow = true
                        break
                    }
                }
                if(isshow) {
                        console.append("<span class=\"prompt\">➜</span> ");
                        console.append("<span class=\"path\">~</span>" + showtasks[i].taskcontent);
                        console.append("<br>");
                        console.append("<br>");
                    }
                    else{
                        showtext = "➜" + "~" + showtasks[i].taskcontent + "^"
                }
            }
            if(showtext.length>0) {
                var str = showtext
                var myindex = 0;
                //$text.html()和$(this).html('')有区别
                var timer = setInterval(function () {
                        refresh = false;
                        var current = str.substr(myindex, 1);
                        myindex++;
                        if(current=="➜")
                            console.append("<span class=\"prompt\">➜</span> ");
                        else if(current=="~")
                            console.append("<span class=\"path\">~</span>");
                        else if(current=="^"){
                            console.append("<br>");
                            console.append("<br>");
                            console[0].scrollTop = console[0].scrollHeight;
                        }
                        else{
                            console.append(current);
                        }
                        if (myindex >= str.length) {
                            clearInterval(timer);
                            refresh =true;
                        }
                    },
                    100);
            }

            console[0].scrollTop = console[0].scrollHeight;
        }
       else {
            for (var i = 0; i < showtasks.length; i++) {
                console.append("<span class=\"prompt\">➜</span> ");
                console.append("<span class=\"path\">~</span>" +  showtasks[i].taskcontent);
                console.append("<br>");
                console.append("<br>");
            }
            console[0].scrollTop = console[0].scrollHeight;
        }
    },
    makeR: function (rightData) {
        for (var n = 0; n < 5; n++) {
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
                if (rindex > 5) {
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
        for (var n = 0; n < 5; n++) {
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
                if (index > 5) {
                    break;
                }
                var lbox = $('.lbox-' + (i + 1));
                lbox.show();
                var html = '<p>' + leftData[i].name + '</p>';
                /*                if (leftData[i].state.toLocaleLowerCase() === 'done') {
                                    var timer = util.getTimerByIndex(i, leftData[i].starttime, leftData[i].endtime);
                                    html += '<em>' + timer + '</em>';
                                }*/
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
    makeTimer: function (starTime, endTime) {
        var timer;
        if (walkthrough_state === 'DONE') {
            clearInterval(tmInterval);
            timer = util.timeFn(starTime, endTime);
            util.showTimer(timer);
        } else {
            clearInterval(tmInterval);
            tmInterval = setInterval(function () {
                var currentTime = 0
                $.ajax({
                    url: '/get_server_time_very_second/',
                    type: 'POST',
                    data: {
                        csrfmiddlewaretoken: csrfToken
                    },
                    dataType: 'json',
                    success: function (data) {
                        currentTime = data.current_time
                        timer = util.timeFn(starTime, currentTime);
                        util.showTimer(timer);
                    },
                });
            }, 1 * 1000); //定时刷新时间
        }
    },
    showTimer: function (timer) {
        var hours = timer.hours.split('');
        var minutes = timer.minutes.split('');
        var seconds = timer.seconds.split('');
        var headerTimeLi = $('.header-timeout li');
        headerTimeLi.eq(3).find('span').text(hours[0]);
        headerTimeLi.eq(4).find('span').text(hours[1]);
        headerTimeLi.eq(6).find('span').text(minutes[0]);
        headerTimeLi.eq(7).find('span').text(minutes[1]);
        headerTimeLi.eq(9).find('span').text(seconds[0]);
        headerTimeLi.eq(10).find('span').text(seconds[1]);
    },
    timeFn: function (d1, d2) {
        var dateBegin = new Date(d1.replace(/-/g, "/"));
        // console.log(d2)
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

        hours = hours < 10 ? '0' + hours : '' + hours;
        minutes = minutes < 10 ? '0' + minutes : '' + minutes;
        seconds = seconds < 10 ? '0' + seconds : '' + seconds;
        return {hours: hours, minutes: minutes, seconds: seconds};
    },
    getNow: function () {
        // var d = new Date();
        // var now = d.getFullYear() + "-" + (d.getMonth() + 1) + "-" + d.getDate() + " " + d.getHours() + ":" + d.getMinutes() + ":" + d.getSeconds();
        // return now;
    }
};
window.util = util;