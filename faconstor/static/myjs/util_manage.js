$(document).ready(function () {
    $('#util_manage_dt').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../util_manage_data/",
        "columns": [
            {"data": "id"},
            {"data": "code"},
            {"data": "name"},
            {"data": "util_type"},
            {"data": null}
        ],
        "columnDefs": [{
            "targets": -1,
            "data": null,
            "width": "100px",
            "defaultContent": "<button  id='edit' title='编辑' data-toggle='modal'  data-target='#static'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button><button title='删除'  id='delrow' class='btn btn-xs btn-primary' type='button'><i class='fa fa-trash-o'></i></button>"
        }],
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
    // 行按钮
    $('#util_manage_dt tbody').on('click', 'button#delrow', function () {
        if (confirm("确定要删除该条数据？")) {
            var table = $('#util_manage_dt').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $.ajax({
                type: "POST",
                url: "../util_manage_del/",
                data: {
                    util_manage_id: data.id,
                },
                success: function (data) {
                    if (data.status == 1) {
                        table.ajax.reload();
                    }
                    alert(data.info);
                },
                error: function (e) {
                    alert("删除失败，请于管理员联系。");
                }
            });

        }
    });
    $('#util_manage_dt tbody').on('click', 'button#edit', function () {
        var table = $('#util_manage_dt').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $("#util_manage_id").val(data.id);

        $('#code').val(data.code);
        $('#name').val(data.name);
        $('#util_type').val(data.util_type);
        $('#webaddr').val(data.commvault_credit.webaddr);
        $('#port').val(data.commvault_credit.port);
        $('#hostusernm').val(data.commvault_credit.hostusername);
        $('#hostpasswd').val(data.commvault_credit.hostpasswd);
        $('#usernm').val(data.commvault_credit.username);
        $('#passwd').val(data.commvault_credit.passwd);
        $('#SQLServerHost').val(data.sqlserver_credit.SQLServerHost);
        $('#SQLServerUser').val(data.sqlserver_credit.SQLServerUser);
        $('#SQLServerPasswd').val(data.sqlserver_credit.SQLServerPasswd);
        $('#SQLServerDataBase').val(data.sqlserver_credit.SQLServerDataBase);

        displayCreditDiv(data.util_type);
    });

    $("#new").click(function () {
        $('#util_manage_form')[0].reset();
        $("#util_manage_id").val("0");
    });

    $('#save').click(function () {
        var table = $('#util_manage_dt').DataTable();

        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../util_manage_save/",
            data: $('#util_manage_form').serialize(),
            success: function (data) {
                if (data.status == 1) {
                    $('#static').modal('hide');
                    table.ajax.reload();
                }
                alert(data.info);
            },
            error: function (e) {
                alert("页面出现错误，请于管理员联系。");
            }
        });
    });

    $('#util_type').change(function(){
        var util_type = $(this).val();
        displayCreditDiv(util_type);
    });

    function displayCreditDiv(util_type){
        if (util_type.toUpperCase() == 'COMMVAULT'){
            $('#credit_div').show();
        } else {
            $('#credit_div').hide();
        }
    }
});