$(document).ready(function () {
    $("#loading").show();

    function getStoragePolicy(utils_manage_id) {
        $.ajax({
            type: 'POST',
            dataType: 'json',
            url: '../get_storage_policy/',
            data: {
                'utils_manage_id': utils_manage_id
            },
            success: function (data) {
                if (data.ret == 0) {
                    alert(data.data)
                } else {
                    var storage_policy = data.data;

                    var pre_clientname = "";
                    var pre_idataagent = "";
                    var pre_type = "";
                    var sort = 0;
                    for (var i = 0; i < storage_policy.length; i++) {
                        var clientname_hidden = "";
                        var idataagent_hidden = "";
                        var type_hidden = "";

                        if (pre_clientname == storage_policy[i]["clientname"]) {
                            // 非首个客户端
                            clientname_hidden = "display:none";
                        } else {
                            sort+=1;
                        }
                        if (pre_clientname == storage_policy[i]["clientname"]&&pre_idataagent == storage_policy[i]["idataagent"]) {
                            idataagent_hidden = "display:none";
                        } 
                        if (pre_clientname == storage_policy[i]["clientname"]&&pre_idataagent == storage_policy[i]["idataagent"]&&pre_type == storage_policy[i]["type"]) {
                            type_hidden = "display:none";
                        } 

                        $("tbody").append(
                            '<tr>' +
                            '<td rowspan="' + storage_policy[i].clientname_rowspan + '" style="vertical-align:middle; ' + clientname_hidden + '">' + sort + '</td>' +
                            '<td rowspan="' + storage_policy[i].clientname_rowspan + '" style="vertical-align:middle; ' + clientname_hidden + '">' + storage_policy[i]["clientname"] + '</td>' +
                            '<td rowspan="' + storage_policy[i].idataagent_rowspan + '" style="vertical-align:middle; ' + idataagent_hidden + '">' + storage_policy[i]["idataagent"] + '</td>' +
                            '<td rowspan="' + storage_policy[i].type_rowspan + '" style="vertical-align:middle; ' + type_hidden + '">' + storage_policy[i]["type"] + '</td>' +
                            '<td style="vertical-align:middle">' + storage_policy[i]["subclient"] + '</td>' +
                            '<td style="vertical-align:middle">' + storage_policy[i]["storage_policy"] + '</td>' +
                            '</tr>'
                        );

                        pre_clientname = storage_policy[i]["clientname"]
                        pre_idataagent = storage_policy[i]["idataagent"]
                        pre_type = storage_policy[i]["type"]
                    }
                    $("#loading").hide();
                }
            }
        });
    }

    getStoragePolicy($('#utils_manage').val());

    $('#utils_manage').change(function () {
        $("tbody").empty();
        $("#loading").show();
        getStoragePolicy($(this).val());
    });
});