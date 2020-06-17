$(document).ready(function () {
    $("#loading").show();
    $.ajax({
        type: 'POST',
        dataType: 'json',
        url: '../get_backup_content/',
        data: {
            "csrfmiddlewaretoken": $("[name='csrfmiddlewaretoken']").val(),
        },
        success: function (data) {
            if (data.ret == 0) {
                alert(data.data)
            } else {
                // 加载数据
                var content_data = data.data.whole_list;
                var row_dict = data.data.row_dict;
                var content_el = ""
                var pre_client_name = "",
                    pre_agent = "",
                    pre_backup_set = "",
                    // pre_sub_client = "",
                    pre_content = "";
                var client_row_list = row_dict.client_row_list,
                    agent_row_list = row_dict.agent_row_list,
                    backupset_row_list = row_dict.backupset_row_list,
                    // subclient_row_list = row_dict.subclient_row_list,
                    content_row_list = row_dict.content_row_list;

                agent_row_list = JSON.parse(JSON.stringify(agent_row_list));
                backupset_row_list = JSON.parse(JSON.stringify(backupset_row_list));
                // subclient_row_list = JSON.parse(JSON.stringify(subclient_row_list));
                content_row_list = JSON.parse(JSON.stringify(content_row_list));

                var client_num = 0;
                for (var i = 0; i < content_data.length; i++) {

                    content_el += "<tr>"
                    for (var key in content_data[i]) {
                        var client_row_span = "",
                            agent_row_span = "",
                            backupset_row_span = "",
                            subclient_row_span = "",
                            content_row_span = "";

                        // 首个client
                        if (key == "clientName" && content_data[i]["clientName"] != pre_client_name) {
                            client_num += 1
                            var client_row = client_row_list.shift();
                            client_row_span = 'rowspan="' + client_row + '" style="vertical-align:middle"';
                            content_el += '<td ' + client_row_span + '>' + client_num + '</td>';
                            content_el += '<td ' + client_row_span + '>' + content_data[i][key] + '</td>';

                            pre_agent = ""
                            pre_backup_set = ""
                            // pre_sub_client = ""
                            pre_content = ""
                        }

                        // 首个app
                        if (key == "appName" && content_data[i]["appName"] != pre_agent) {
                            var agent_row = agent_row_list.shift();
                            agent_row_span = 'rowspan="' + agent_row + '" style="vertical-align:middle"';
                            content_el += '<td ' + agent_row_span + '>' + content_data[i][key] + '</td>';

                            pre_backup_set = ""
                            // pre_sub_client = ""
                            pre_content = ""
                        }

                        // 首个backupset
                        if (key == "backupsetName" && content_data[i]["backupsetName"] != pre_backup_set) {
                            var backupset_row = backupset_row_list.shift();
                            backupset_row_span = 'rowspan="' + backupset_row + '" style="vertical-align:middle"';
                            content_el += '<td ' + backupset_row_span + '>' + content_data[i][key] + '</td>';

                            // pre_sub_client = ""
                            pre_content = ""
                        }

                        // 首个subclient
                        // if (key == "subclientName" && content_data[i]["subclientName"] != pre_sub_client) {
                        //     var subclient_row = subclient_row_list.shift();
                        //     subclient_row_span = 'rowspan="' + subclient_row + '" style="vertical-align:middle"';
                        //     content_el += '<td ' + subclient_row_span + '>' + content_data[i][key] + '</td>';
                        //
                        //     pre_content = "";
                        // }

                        if (key == "content" && content_data[i]["content"] != pre_content) {
                            content_el += '<td>' + content_data[i][key] + '</td>';
                        }
                    }

                    pre_client_name = content_data[i]["clientName"]
                    pre_agent = content_data[i]["appName"]
                    pre_backup_set = content_data[i]["backupsetName"]
                    // pre_sub_client = content_data[i]["subclientName"]
                    pre_content = content_data[i]["content"]

                    content_el += "</tr>"
                }

                $("tbody").append(content_el);
                $("#loading").hide();
            }
        }
    })
});