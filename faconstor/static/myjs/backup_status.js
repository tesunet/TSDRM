$(document).ready(function () {
    $("#loading").show();
    $.ajax({
        type: 'POST',
        dataType: 'json',
        url: '../get_backup_status/',
        data: {
            "csrfmiddlewaretoken": $("[name='csrfmiddlewaretoken']").val(),
        },
        success: function (data) {
            if (data.ret == 0) {
                alert(data.data)
            } else {
                var whole_list = data.data;

                // 加载数据
                var content_el = '';
                for (var i = 0; i < whole_list.length; i++) {

                    var agent_job_list = whole_list[i].agent_job_list;
                    var agent_length = whole_list[i].agent_length;

                    for (var j = 0; j < agent_job_list.length; j++) {
                        var tr_el = '<tr>';
                        if (j == 0) {
                            tr_el += '<td rowspan="' + whole_list[i].agent_length + '" style="vertical-align:middle">' + (i + 1) + '</td><td rowspan="' + whole_list[i].agent_length + '" style="vertical-align:middle">' + agent_job_list[j].client_name + '</td>';
                        }
                        tr_el += '<td>' + agent_job_list[j].agent_type_name + '</td><td>' + agent_job_list[j].job_start_time + '</td><td><span class="' + agent_job_list[j].status_label + '">' + agent_job_list[j].job_backup_status + '</span></td>'

                        tr_el += '<td><span class="' + agent_job_list[j].aux_status_label + '">' + agent_job_list[j].aux_copy_status + '</span></td></tr>'
                        content_el += tr_el;
                    }
                }

                $("tbody").append(content_el);
                $("#loading").hide();
            }
        }
    })
});