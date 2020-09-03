$(document).ready(function () {

    $.ajax({
        type: 'POST',
        dataType: 'json',
        url: '../get_client_name/',
        data: {
            "utils":$('#util').val(),
        },
        success: function (data) {
            if (data.ret == 0){
                alert(data.data)
            }else {
                var pre = '<option selected value="" >全部</option>';
                for (i = 0; i < data.data.length; i++) {
                    pre += '<option value="' + data.data[i].client_id + '">' + data.data[i].client_name + '</option>';
                }
                $("#clientid").append(pre)
            }

        }
    });


    $('#display_error_job').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "iDisplayLength": 25,
        "bProcessing": true,
        "ajax": "../get_display_error_job/?util=" + $('#util').val()  + "&startdate=" + $('#starttime').val() +
            "&enddate=" + $('#endtime').val() + "&clientid=" + $('#clientid').val(),
        "columns": [
            {"data": "jobid"},
            {"data": "clientname"},
            {"data": "idataagent"},
            {"data": "instance"},
            {"data": "startdate"},
            {"data": "enddate"},
            {"data": "jobfailedreason"},
            {"data": null}
        ],

        "columnDefs": [
            {
                "targets": -2,
                "mRender": function (data, type, full) {
                    var jobfailedreason = full.jobfailedreason.slice(0,25) + '...'
                    return "<span id='" + full.jobid + "'>" + jobfailedreason + "</span>"
                }
            },
            {
                "targets": -1,
                "data": null,
                "width": "40px",
                "defaultContent": "<button  id='edit' title='详情' data-toggle='modal'  data-target='#static'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button>"
            }
        ],
        "oLanguage": {
            "sLengthMenu": "每页显示 _MENU_ 条记录",
            "sZeroRecords": "抱歉， 没有找到",
            "sInfo": "从 _START_ 到 _END_ /共 _TOTAL_ 条数据",
            "sInfoEmpty": "没有数据",
            "sInfoFiltered": "(从 _MAX_ 条数据中检索)",
            "sSearch": "搜索",
            "oPaginate": {
                "sFirst": "首页",
                "sPrevious": "前一页",
                "sNext": "后一页",
                "sLast": "尾页"
            },
            "sZeroRecords": "没有检索到数据",

        }
    });

    $('#display_error_job tbody').on('click', 'button#edit', function () {
        var table = $('#display_error_job').DataTable();
        var data = table.row($(this).parents('tr')).data();

        $("#jobid").val(data.jobid);
        $("#clientname").val(data.clientname);
        $("#idataagent").val(data.idataagent);
        $("#enddate").val(data.enddate);
        $("#jobfailedreason").val(data.jobfailedreason);
    });

    $('#starttime').datetimepicker({
        autoclose: true,
        minView: "month",
        format: 'yyyy-mm-dd',
    });
    $('#endtime').datetimepicker({
        autoclose: true,
        minView: "month",
        format: 'yyyy-mm-dd',
    });
    $('#cx').click(function () {
        var table = $('#display_error_job').DataTable();
        table.ajax.url("../get_display_error_job?util=" + $('#util').val() + "&startdate=" + $('#starttime').val() + "&enddate=" + $('#endtime').val() + "&clientid=" + $('#clientid').val()).load();
    })

});