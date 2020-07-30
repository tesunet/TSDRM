$(document).ready(function () {
    $("#loading").show();

    function getBackupContent(utils_manage_id) {
        $.ajax({
            type: 'POST',
            dataType: 'json',
            url: '../get_backup_content/',
            data: {
                'utils_manage_id': utils_manage_id
            },
            success: function (data) {
                if (data.ret == 0) {
                    alert(data.data)
                } else {
                    var backup_content = data.data;

                    var pre_clientname = "";
                    var pre_idataagent = "";
                    var pre_type = "";
                    var pre_subclient = "";
                    var sort = 0;
                    for (var i = 0; i < backup_content.length; i++) {
                        var clientname_hidden = "";
                        var idataagent_hidden = "";
                        var type_hidden = "";
                        var subclient_hidden = "";

                        if (pre_clientname == backup_content[i]["clientname"]) {
                            // 非首个客户端
                            clientname_hidden = "display:none";
                        } else {
                            sort += 1;
                        }
                        if (pre_clientname == backup_content[i]["clientname"] && pre_idataagent == backup_content[i]["idataagent"]) {
                            idataagent_hidden = "display:none";
                        }
                        if (pre_clientname == backup_content[i]["clientname"] && pre_idataagent == backup_content[i]["idataagent"] && pre_type == backup_content[i]["type"]) {
                            type_hidden = "display:none";
                        }
                        if (pre_clientname == backup_content[i]["clientname"] && pre_idataagent == backup_content[i]["idataagent"] && pre_type == backup_content[i]["type"] && pre_subclient == backup_content[i]['subclient']) {
                            subclient_hidden = "display:none";
                        }
                        // 备份大小、应用大小
                        var numbytescomp = (backup_content[i]["numbytescomp"] / 1024 / 1024 / 1024).toFixed(2)
                        var numbytesuncomp = (backup_content[i]["numbytesuncomp"] / 1024 / 1024 / 1024).toFixed(2)

                        $("tbody").append(
                            '<tr>' +
                            '<td rowspan="' + backup_content[i].clientname_rowspan + '" style="vertical-align:middle; ' + clientname_hidden + '">' + sort + '</td>' +
                            '<td rowspan="' + backup_content[i].clientname_rowspan + '" style="vertical-align:middle; ' + clientname_hidden + '">' + backup_content[i]["clientname"] + '</td>' +
                            '<td rowspan="' + backup_content[i].idataagent_rowspan + '" style="vertical-align:middle; ' + idataagent_hidden + '">' + backup_content[i]["idataagent"] + '</td>' +
                            '<td rowspan="' + backup_content[i].type_rowspan + '" style="vertical-align:middle; ' + type_hidden + '">' + backup_content[i]["type"] + '</td>' +
                            '<td rowspan="' + backup_content[i].subclient_rowspan + '" style="vertical-align:middle; ' + subclient_hidden + '">' + backup_content[i]["subclient"] + '</td>' +
                            '<td style="vertical-align:middle">' + backup_content[i]["content"] + '</td>' +
                            '<td style="vertical-align:middle">' + numbytesuncomp + ' GB</td>' +
                            '<td style="vertical-align:middle">' + numbytescomp + ' GB</td>' +
                            '</tr>'
                        );

                        pre_clientname = backup_content[i]["clientname"]
                        pre_idataagent = backup_content[i]["idataagent"]
                        pre_type = backup_content[i]["type"]
                        pre_subclient = backup_content[i]["subclient"]
                    }
                    $("#loading").hide();
                }
            }
        });
    }

    getBackupContent($('#utils_manage').val());

    $('#utils_manage').change(function () {
        $("tbody").empty();
        $("#loading").show();
        getBackupContent($(this).val());
    });
});