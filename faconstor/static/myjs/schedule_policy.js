$(document).ready(function () {
    $("#loading").show();

    function getSchedulePolicy(utils_manage_id){
        $.ajax({
        type: 'POST',
        dataType: 'json',
        url: '../get_schedule_policy/',
        data: {
            'utils_manage_id': utils_manage_id
        },
        success: function (data) {
            if (data.ret == 0) {
                alert(data.data)
            } else {
                var schedule_policy = data.data;

                var pre_clientname = "";
                var pre_idataagent = "";
                var pre_type = "";
                var sort = 0;
                for (var i = 0; i < schedule_policy.length; i++) {
                    var clientname_hidden = "";
                    var idataagent_hidden = "";
                    var type_hidden = "";

                    if (pre_clientname == schedule_policy[i]["clientname"]) {
                        // 非首个客户端
                        clientname_hidden = "display:none";
                    } else {
                        sort+=1;
                    }
                    if (pre_clientname == schedule_policy[i]["clientname"]&&pre_idataagent == schedule_policy[i]["idataagent"]) {
                        idataagent_hidden = "display:none";
                    } 
                    if (pre_clientname == schedule_policy[i]["clientname"]&&pre_idataagent == schedule_policy[i]["idataagent"]&&pre_type == schedule_policy[i]["type"]) {
                        type_hidden = "display:none";
                    } 

                    // 是否展示操作按钮
                    var disable_tag = ''
                    if (schedule_policy[i]["scheduePolicy"] == '无'){
                        disable_tag = 'disabled'
                    }

                    $("tbody").append(
                        '<tr>' +
                        '<td rowspan="' + schedule_policy[i].clientname_rowspan + '" style="vertical-align:middle; ' + clientname_hidden + '">' + sort + '</td>' +
                        '<td rowspan="' + schedule_policy[i].clientname_rowspan + '" style="vertical-align:middle; ' + clientname_hidden + '">' + schedule_policy[i]["clientname"] + '</td>' +
                        '<td rowspan="' + schedule_policy[i].idataagent_rowspan + '" style="vertical-align:middle; ' + idataagent_hidden + '">' + schedule_policy[i]["idataagent"] + '</td>' +
                        '<td rowspan="' + schedule_policy[i].type_rowspan + '" style="vertical-align:middle; ' + type_hidden + '">' + schedule_policy[i]["type"] + '</td>' +
                        '<td style="vertical-align:middle">' + schedule_policy[i]["subclient"] + '</td>' +
                        '<td style="vertical-align:middle">' + schedule_policy[i]["scheduePolicy"] + '</td>' +
                        '<td style="vertical-align:middle">' + schedule_policy[i]["schedbackuptype"] + '</td>' +
                        '<td style="vertical-align:middle">' + schedule_policy[i]["schedpattern"] + '</td>' +
                        '<td><button name="schedule_type" title="编辑" data-toggle="modal" data-target="#static" class="btn btn-xs btn-primary" type="button" '+ disable_tag +'><i class="fa fa-cogs"></i></button>' +
                        '<input value="' + schedule_policy[i]["option"]["scheduleName"] + '" hidden>' +
                        '<input value="' + schedule_policy[i]["option"]["schedpattern"] + '" hidden>' +
                        '<input value="' + schedule_policy[i]["option"]["schednextbackuptime"] + '" hidden>' +
                        '<input value="' + schedule_policy[i]["option"]["schedinterval"] + '" hidden>' +
                        '<input value="' + schedule_policy[i]["option"]["schedbackupday"] + '" hidden>' +
                        '<input value="' + schedule_policy[i]["option"]["schedbackuptype"] + '" hidden>' +
                        '<td>' + 
                        '</tr>'
                    );

                    pre_clientname = schedule_policy[i]["clientname"]
                    pre_idataagent = schedule_policy[i]["idataagent"]
                    pre_type = schedule_policy[i]["type"]
                }
                $("#loading").hide();
            }
        }
    });
    }

    getSchedulePolicy($('#utils_manage').val());

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

    $('#utils_manage').change(function () {
        $("tbody").empty();
        $("#loading").show();
        getSchedulePolicy($(this).val());
    });
});