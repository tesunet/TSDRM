$(document).ready(function() {
    var data = JSON.parse($("#walkthrough_pdf").val());
    $("table#process_data tbody").empty();
    $("table#group_data tbody").empty();

    $("#current_process").text(data.all_process_name);
    $("#summary").text("为了提高防范灾难风险的能力，保证业务连续性要求，在公司总经理室高度重视下，太平资产成立灾备演练项目组，于time进行核心系统灾备演练，并取得圆满成功。演练具体情况报告如下。".replace("time", data.walkthrough_starttime));
    $("#note").text(data.purpose);
    var elements = "";
    for (var k = 0; k < data.process_info_list.length; k++) {
        var step_info_list = data.process_info_list[k].step_info_list;

        elements += '<tr><td rowspan="' + (data.process_info_list[k].process_length+1) + '"><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + data.process_info_list[k].process_name + '</font></font></td>';
        for (var i = 0; i < step_info_list.length; i++) {
            // wrapper_step
            var stepWrapper = step_info_list[i];
            var innerStep = stepWrapper.inner_step_list;
            if (innerStep != "" && innerStep != null) {
                var innerStepLength = innerStep.length;
                var rowSpanString = ' rowspan="' + innerStepLength + '"';
            } else {
                rowSpanString = "";
            }

            if (stepWrapper.operator) {
                var stepWrapperOperator = stepWrapper.operator
            } else {
                var stepWrapperOperator = ""
            }
            elements += '<td' + rowSpanString + '><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">*' + stepWrapper.step_name + '</font></font></td>';
            // inner_step
            if (innerStep != "" && innerStep != null) {
                for (var j = 0; j < innerStep.length; j++) {
                    if (innerStep[j].operator) {
                        var stepInnerOperator = innerStep[j].operator
                    } else {
                        var stepInnerOperator = ""
                    }
                    

                    elements += '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">**' + innerStep[j].step_name + '</font></font></td>' +
                        '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + stepInnerOperator + '</font></font></td>' +
                        '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + innerStep[j].start_time + '</font></font></td>' +
                        '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + innerStep[j].end_time + '</font></font></td>' +
                        '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + innerStep[j].rto + '</font></font></td></tr>'
                }
            } else {
                var cur_starttime = "", cur_endtime="", cur_rto="";
                if (stepWrapper.start_time){
                    cur_starttime = stepWrapper.start_time;
                }else {
                    cur_starttime = ""
                }
                if (stepWrapper.end_time) {
                    cur_endtime = stepWrapper.end_time;
                }else{
                    cur_endtime = "";
                }
                if (stepWrapper.rto) {
                    cur_rto = stepWrapper.rto;
                } else{
                    cur_rto = "";
                }
                elements += '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;"></font></font></td>' +
                    '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + stepWrapperOperator + '</font></font></td>' +
                    '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + cur_starttime + '</font></font></td>' +
                    '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + cur_endtime + '</font></font></td>' +
                    '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + cur_rto + '</font></font></td></tr>'
            }
        }
        var process_start_time="", process_end_time="", process_rto = "";
        try {
            process_start_time = data.process_info_list[k].start_time;
            process_end_time = data.process_info_list[k].end_time;
            process_rto = data.process_info_list[k].rto;

        }
        catch (err) {
            //..
        }


        elements += '<tr><td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;"><font color="#ff0000">*</font>总环节</font></font></td>';
        elements += '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;"></font></font></td>' +
            '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;"></font></font></td>' +
            '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + process_start_time + '</font></font></td>' +
            '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + process_end_time + '</font></font></td>' +
            '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + process_rto + '</font></font></td></tr>';
    }
    // 添加流程总RTO


    $("table#process_data tbody").append(elements);

    var groupElements = "";
    for (var i = 0; i < data.total_list.length; i++) {
        var currentGroup = data.total_list[i];
        var userList = currentGroup.current_users_and_departments;
        if (userList != "" && userList != null) {
            var userListLength = userList.length;
            var rowSpanString01 = ' rowspan="' + userListLength + '"';
        } else {
            rowSpanString01 = "";
        }
        groupElements += '<tr><td' + rowSpanString01 + '><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + currentGroup.group + '</font></font></td>';
        if (userList != "" && userList != null) {
            for (var j = 0; j < userList.length; j++) {
                groupElements += '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + userList[j].fullname + '</font></font></td>' +
                    '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + userList[j].depart_name + '</font></font></td></tr>'
            }
        } else {
            groupElements += '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;"></font></font></td>' +
                '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;"></font></font></td></tr>'
        }
    }
    $("table#group_data tbody").append(groupElements);
});