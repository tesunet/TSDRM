$(document).ready(function () {
    $("#loading").show();
    $.ajax({
        type: 'POST',
        dataType: 'json',
        url: '../get_storage_policy/',
        data: {
            "csrfmiddlewaretoken": $("[name='csrfmiddlewaretoken']").val(),
        },
        success: function (data) {
            if (data.ret == 0) {
                alert(data.data)
            } else {
                // 加载数据
                var storage_data = data.data.whole_list;
                var row_dict = data.data.row_dict;
                var storage_el = ""
                var pre_client_name = "",
                    pre_agent = "",
                    pre_backup_set = "",
                    // pre_sub_client = "",
                    pre_storage_policy = "";
                var client_row_list = row_dict.client_row_list,
                    agent_row_list = row_dict.agent_row_list,
                    backupset_row_list = row_dict.backupset_row_list,
                    // subclient_row_list = row_dict.subclient_row_list,
                    storage_row_list = row_dict.storage_row_list;

                agent_row_list = JSON.parse(JSON.stringify(agent_row_list));
                backupset_row_list = JSON.parse(JSON.stringify(backupset_row_list));
                // subclient_row_list = JSON.parse(JSON.stringify(subclient_row_list));
                storage_row_list = JSON.parse(JSON.stringify(storage_row_list));

                var client_num = 0;
                for (var i = 0; i < storage_data.length; i++) {

                    storage_el += "<tr>"
                    for (var key in storage_data[i]) {
                        var client_row_span = "",
                            agent_row_span = "",
                            backupset_row_span = "",
                            subclient_row_span = "",
                            storage_row_span = "";

                        // 首个client
                        if (key == "clientName" && storage_data[i]["clientName"] != pre_client_name) {
                            client_num += 1
                            var client_row = client_row_list.shift();
                            client_row_span = 'rowspan="' + client_row + '" style="vertical-align:middle"';
                            storage_el += '<td ' + client_row_span + '>' + client_num + '</td>';
                            storage_el += '<td ' + client_row_span + '>' + storage_data[i][key] + '</td>';

                            pre_agent = ""
                            pre_backup_set = ""
                            // pre_sub_client = ""
                            pre_storage_policy = ""
                        }

                        // 首个app
                        if (key == "appName" && storage_data[i]["appName"] != pre_agent) {
                            var agent_row = agent_row_list.shift();
                            agent_row_span = 'rowspan="' + agent_row + '" style="vertical-align:middle"';
                            storage_el += '<td ' + agent_row_span + '>' + storage_data[i][key] + '</td>';

                            pre_backup_set = ""
                            // pre_sub_client = ""
                            pre_storage_policy = ""
                        }

                        // 首个backupset
                        if (key == "backupsetName" && storage_data[i]["backupsetName"] != pre_backup_set) {
                            var backupset_row = backupset_row_list.shift();
                            backupset_row_span = 'rowspan="' + backupset_row + '" style="vertical-align:middle"';
                            storage_el += '<td ' + backupset_row_span + '>' + storage_data[i][key] + '</td>';

                            // pre_sub_client = ""
                            pre_storage_policy = ""
                        }

                        // // 首个subclient
                        // if (key == "subclientName" && storage_data[i]["subclientName"] != pre_sub_client) {
                        //     var subclient_row = subclient_row_list.shift();
                        //     subclient_row_span = 'rowspan="' + subclient_row + '" style="vertical-align:middle"';
                        //     storage_el += '<td ' + subclient_row_span + '>' + storage_data[i][key] + '</td>';
                        //
                        //     pre_storage_policy = "";
                        // }

                        if (key == "storagePolicy"  && storage_data[i]["storagePolicy"] != pre_storage_policy) {
                            storage_el += '<td>' + storage_data[i][key] + '</td>';
                        }
                    }

                    pre_client_name = storage_data[i]["clientName"]
                    pre_agent = storage_data[i]["appName"]
                    pre_backup_set = storage_data[i]["backupsetName"]
                    // pre_sub_client = storage_data[i]["subclientName"]
                    pre_storage_policy = storage_data[i]["storagePolicy"]

                    storage_el += "</tr>"
                }

                $("tbody").append(storage_el);
                $("#loading").hide();
            }
        }
    })
});