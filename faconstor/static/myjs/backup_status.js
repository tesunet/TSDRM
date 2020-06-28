$(document).ready(function () {
    $("#loading").show();

    function getBackupStatus(utils_manage_id) {
        $.ajax({
            type: 'POST',
            dataType: 'json',
            url: '../get_backup_status/',
            data: {
                'utils_manage_id': utils_manage_id
            },
            success: function (data) {
                if (data.ret == 0) {
                    alert(data.data)
                } else {
                    var backup_status = data.data;

                    function get_status_label(job_status) {
                        var status_label = "label label-sm label-danger";
                        if (["运行", "正常", "等待", "QueuedCompleted", "Queued", "PartialSuccess", "成功"].indexOf(job_status) != -1) {
                            status_label = "label label-sm label-success"
                        }
                        if (["阻塞", "已完成，但有一个或多个错误", "已完成，但有一个或多个警告"].indexOf(job_status) != -1) {
                            status_label = "label label-sm label-warning"
                        }
                        if (job_status == "无") {
                            status_label = ""
                        }
                        return status_label;
                    }
                    var pre_clientname = "";
                    var pre_idataagent = "";
                    var pre_type = "";
                    var sort = 0;
                    for (var i = 0; i < backup_status.length; i++) {
                        var clientname_hidden = "";
                        var idataagent_hidden = "";
                        var type_hidden = "";

                        if (pre_clientname == backup_status[i]["clientname"]) {
                            // 非首个客户端
                            clientname_hidden = "display:none";
                        } else {
                            sort+=1;
                        }
                        if (pre_clientname == backup_status[i]["clientname"]&&pre_idataagent == backup_status[i]["idataagent"]) {
                            idataagent_hidden = "display:none";
                        } 
                        if (pre_clientname == backup_status[i]["clientname"]&&pre_idataagent == backup_status[i]["idataagent"]&&pre_type == backup_status[i]["type"]) {
                            type_hidden = "display:none";
                        } 

                        var bk_status_label = get_status_label(backup_status[i].bk_status);
                        var aux_status_label = get_status_label(backup_status[i].aux_status);

                        $("tbody").append(
                            '<tr>' +
                            '<td rowspan="' + backup_status[i].clientname_rowspan + '" style="vertical-align:middle; ' + clientname_hidden + '">' + sort + '</td>' +
                            '<td rowspan="' + backup_status[i].clientname_rowspan + '" style="vertical-align:middle; ' + clientname_hidden + '">' + backup_status[i]["clientname"] + '</td>' +
                            '<td rowspan="' + backup_status[i].idataagent_rowspan + '" style="vertical-align:middle; ' + idataagent_hidden + '">' + backup_status[i]["idataagent"] + '</td>' +
                            '<td rowspan="' + backup_status[i].type_rowspan + '" style="vertical-align:middle; ' + type_hidden + '">' + backup_status[i]["type"] + '</td>' +
                            '<td style="vertical-align:middle">' + backup_status[i]["subclient"] + '</td>' +
                            '<td style="vertical-align:middle">' + backup_status[i]["startdate"] + '</td>' +
                            '<td style="vertical-align:middle"><span class="' + bk_status_label + '">' + backup_status[i]["bk_status"] + '</span></td>' +
                            '<td style="vertical-align:middle"><span class="' + aux_status_label + '">' + backup_status[i]["aux_status"] + '</span></td>' +
                            '</tr>'
                        );

                        pre_clientname = backup_status[i]["clientname"]
                        pre_idataagent = backup_status[i]["idataagent"]
                        pre_type = backup_status[i]["type"]
                    }
                    $("#loading").hide();
                }
            }
        });
    }

    getBackupStatus($('#utils_manage').val());
    $('#utils_manage').change(function () {
        $("tbody").empty();
        $("#loading").show();
        getBackupStatus($(this).val());
    });
});