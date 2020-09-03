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

    $('#cv_joblist').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "iDisplayLength": 25,
        "bProcessing": true,
        "ajax": "../get_cv_joblist/?util=" + $('#util').val() + "&startdate=" + $('#starttime').val() +
            "&enddate=" + $('#endtime').val() + "&clientid=" + $('#clientid').val() + "&jobstatus=" + $('#jobstatus').val(),
        "columns": [
            {"data": "jobid"},
            {"data": "clientname"},
            {"data": "idataagent"},
            {"data": "instance"},
            {"data": "startdate"},
            {"data": "enddate"},
            {"data": "jobstatus"},
        ],
        "columnDefs": [
            {
                "targets": -1,
                "mRender": function (data, type, full) {
                    return "<span class='" + full.jobstatus_label + "' disabled id='" + full.jobid + "'>" + full.jobstatus + "</span>"
                }
            },
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

        },
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
        var table = $('#cv_joblist').DataTable();
        table.ajax.url("../get_cv_joblist?util=" + $('#util').val() + "&startdate=" + $('#starttime').val() + "&enddate=" + $('#endtime').val() + "&clientid=" + $('#clientid').val() + "&jobstatus=" + $('#jobstatus').val()).load();
    })

});