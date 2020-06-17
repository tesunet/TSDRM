$(document).ready(function () {
    $("#loading").show();
    $.ajax({
        type: 'POST',
        dataType: 'json',
        url: '../get_schedule_policy/',
        data: {
            "csrfmiddlewaretoken": $("[name='csrfmiddlewaretoken']").val(),
        },
        success: function (data) {
            if (data.ret == 0) {
                alert(data.data)
            } else {
                // 加载数据
                var schedule_data = data.data.whole_list;
                var row_dict = data.data.row_dict;
                var schedule_el = ""
                var pre_client_name = "",
                    pre_agent = "",
                    pre_backup_set = "",
                    // pre_sub_client = "",
                    pre_schedule_policy = "",
                    pre_schedule_type = "",
                    pre_description = "",
                    pre_schedpattern = "";
                var client_row_list = row_dict.client_row_list,
                    agent_row_list = row_dict.agent_row_list,
                    backupset_row_list = row_dict.backupset_row_list,
                    // subclient_row_list = row_dict.subclient_row_list,
                    schedule_row_list = row_dict.schedule_row_list,
                    schedule_type_row_list = row_dict.schedule_type_row_list;

                agent_row_list = JSON.parse(JSON.stringify(agent_row_list));
                backupset_row_list = JSON.parse(JSON.stringify(backupset_row_list));
                // subclient_row_list = JSON.parse(JSON.stringify(subclient_row_list));
                schedule_row_list = JSON.parse(JSON.stringify(schedule_row_list));
                schedule_type_row_list = JSON.parse(JSON.stringify(schedule_type_row_list));

                var client_num = 0;
                for (var i = 0; i < schedule_data.length; i++) {

                    schedule_el += "<tr>"
                    for (var key in schedule_data[i]) {
                        var client_row_span = "",
                            agent_row_span = "",
                            backupset_row_span = "",
                            // subclient_row_span = "",
                            schedule_row_span = "",
                            scheduletype_row_span = "";

                        // 首个client
                        if (key == "clientName" && schedule_data[i]["clientName"] != pre_client_name) {
                            client_num += 1
                            var client_row = client_row_list.shift();
                            client_row_span = 'rowspan="' + client_row + '" style="vertical-align:middle"';
                            schedule_el += '<td ' + client_row_span + '>' + client_num + '</td>';
                            schedule_el += '<td ' + client_row_span + '>' + schedule_data[i][key] + '</td>';

                            pre_agent = "";
                            pre_backup_set = "";
                            // pre_sub_client = "";
                            pre_schedule_policy = "";
                            pre_schedule_type = "";
                            pre_description = "";
                            pre_schedpattern = "";
                        }

                        // 首个app
                        if (key == "appName" && schedule_data[i]["appName"] != pre_agent) {
                            var agent_row = agent_row_list.shift();
                            agent_row_span = 'rowspan="' + agent_row + '" style="vertical-align:middle"';
                            schedule_el += '<td ' + agent_row_span + '>' + schedule_data[i][key] + '</td>';

                            pre_backup_set = "";
                            // pre_sub_client = "";
                            pre_schedule_policy = "";
                            pre_schedule_type = "";
                            pre_description = "";
                            pre_schedpattern = "";
                        }

                        // 首个backupset
                        if (key == "backupsetName" && schedule_data[i]["backupsetName"] != pre_backup_set) {
                            var backupset_row = backupset_row_list.shift();
                            backupset_row_span = 'rowspan="' + backupset_row + '" style="vertical-align:middle"';
                            schedule_el += '<td ' + backupset_row_span + '>' + schedule_data[i][key] + '</td>';

                            // pre_sub_client = "";
                            pre_schedule_policy = "";
                            pre_schedule_type = "";
                            pre_description = "";
                            pre_schedpattern = "";
                        }

                        // // 首个subclient
                        // if (key == "subclientName" && schedule_data[i]["subclientName"] != pre_sub_client) {
                        //     var subclient_row = subclient_row_list.shift();
                        //     subclient_row_span = 'rowspan="' + subclient_row + '" style="vertical-align:middle"';
                        //     schedule_el += '<td ' + subclient_row_span + '>' + schedule_data[i][key] + '</td>';
                        //
                        //     pre_schedule_policy = "";
                        //     pre_schedule_type = "";
                        //     pre_description = "";
                        // }

                        // 首个schedulepolicy
                        if (key == "scheduePolicy" && schedule_data[i]["scheduePolicy"] != pre_schedule_policy) {
                            var schedule_row = schedule_row_list.shift();
                            schedule_row_span = 'rowspan="' + schedule_row + '" style="vertical-align:middle"';
                            schedule_el += '<td ' + schedule_row_span + '>' + schedule_data[i][key] + '</td>';

                            pre_schedule_type = "";
                            pre_description = "";
                            pre_schedpattern = "";
                        }

                        // 首个schedule_type
                        if (key == "schedbackuptype" && schedule_data[i]["schedbackuptype"] != pre_schedule_type) {
                            var schedule_type_row = schedule_type_row_list.shift();
                            scheduletype_row_span = 'rowspan="' + schedule_type_row + '" style="vertical-align:middle"';
                            schedule_el += '<td ' + scheduletype_row_span + '>' + schedule_data[i][key] + '</td>';

                            pre_description = "";
                            pre_schedpattern = "";
                        }

                        if (key == "schedpattern" && schedule_data[i]["schedpattern"] != pre_schedpattern) {
                            schedule_el += '<td ' + scheduletype_row_span + '>' + schedule_data[i][key] + ' (' + schedule_data[i]['schedbackupday'] + ')' + '</td>';
                        }

                        if (key == "option" && schedule_data[i]["schedpattern"] != pre_schedpattern) {
                            var disable_tag = ''
                            if (schedule_data[i]["scheduePolicy"] == '无'){
                                disable_tag = 'disabled'
                            }

                            schedule_el += '<td><button name="schedule_type" title="编辑" data-toggle="modal" data-target="#static" class="btn btn-xs btn-primary" type="button" '+ disable_tag +'><i class="fa fa-cogs"></i></button>' +
                                '<input value="' + schedule_data[i][key]["scheduleName"] + '" hidden>' +
                                '<input value="' + schedule_data[i][key]["schedpattern"] + '" hidden>' +
                                '<input value="' + schedule_data[i][key]["schednextbackuptime"] + '" hidden>' +
                                '<input value="' + schedule_data[i][key]["schedinterval"] + '" hidden>' +
                                '<input value="' + schedule_data[i][key]["schedbackupday"] + '" hidden>' +
                                '<input value="' + schedule_data[i][key]["schedbackuptype"] + '" hidden>' +
                                '<td>';
                        }
                    }

                    pre_client_name = schedule_data[i]["clientName"]
                    pre_agent = schedule_data[i]["appName"]
                    pre_backup_set = schedule_data[i]["backupsetName"]
                    // pre_sub_client = schedule_data[i]["subclientName"]
                    pre_schedule_policy = schedule_data[i]["scheduePolicy"]
                    pre_schedule_type = schedule_data[i]["schedbackuptype"]
                    pre_schedpattern = schedule_data[i]["schedpattern"]

                    schedule_el += "</tr>";
                }

                $("tbody").append(schedule_el);
                $("#loading").hide();
            }
        }
    });

    // 点击事件
    $('#schedule tbody').on('click', 'button[name="schedule_type"]', function () {
        var siblingInput = $(this).siblings();
        $("#scheduleName").val(siblingInput[0].value);
        $("#schedpattern").val(siblingInput[1].value);
        $("#schednextbackuptime").val(siblingInput[2].value);
        $("#schedinterval").val(siblingInput[3].value);
        $("#schedbackupday").val(siblingInput[4].value);
        $("#schedbackuptype").val(siblingInput[5].value);
    });


});