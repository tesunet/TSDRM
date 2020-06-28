$(document).ready(function () {

    function getClientManage() {
        var utils_manage_id = $("#utils_manage").val();
        $('#client_manage_dt').dataTable({
            "bAutoWidth": true,
            "bSort": false,
            "bProcessing": true,
            "destroy":true,
            "ajax": "../manualrecoverydata/?utils_manage_id=" + utils_manage_id,
            "columns": [
                {"data": "client_name"},
                {"data": "model"},
                {"data": "client_os"},

            ],
            "columnDefs": [{
                "targets": 0,
                "mRender": function (data, type, full) {
                    return "<a id='edit' data-toggle='modal' data-target='#static1'>" + data + "</a><input type='text' value='" + full.data_path + "' hidden>" + "<input type='text' value='" + full.copy_priority + "' hidden>" + "<input type='text' value='" + full.target_client + "' hidden>" + "<input type='text' value='" + full.client_manage_id + "' hidden>"
                }
            }],
            "oLanguage": {
                "sLengthMenu": "&nbsp;&nbsp;每页显示 _MENU_ 条记录",
                "sInfo": "从 _START_ 到 _END_ /共 _TOTAL_ 条数据",
                "sInfoEmpty": '',
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
    }

    getClientManage();

    $('#utils_manage').change(function () {
        getClientManage();
    });

    $('#static1').on('show.bs.modal', function (e) {
        var el = e.relatedTarget;
        var jQuery_el = $(el);
        var agent = jQuery_el.parent().next().html();
        var data_path = jQuery_el.next().val();
        var copy_priority = jQuery_el.next().next().val();
        var target_client = jQuery_el.next().next().next().val();
        var origin_id = jQuery_el.next().next().next().next().val();

        $("#agent").val(agent);
        $("#data_path").val(data_path);
        $("#copy_priority").val(copy_priority);
        $("#destClient").val(target_client);
        $("#sourceClient").val(el.innerText);

        $('#backup_point').dataTable({
            "bAutoWidth": true,
            "bProcessing": true,
            "bSort": false,
            "destroy": true,
            "ajax": "../../oraclerecoverydata?origin_id=" + origin_id,
            "columns": [
                {"data": "jobId"},
                {"data": "jobType"},
                {"data": "Level"},
                {"data": "StartTime"},
                {"data": "LastTime"},
                {"data": null},
            ],
            "columnDefs": [{
                "targets": -1,
                "data": null,
                "defaultContent": "<button  id='select' title='选择'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-check'></i></button>"
            }],

            "oLanguage": {
                "sLengthMenu": "&nbsp;&nbsp;每页显示 _MENU_ 条记录",
                "sZeroRecords": "抱歉， 没有找到",
                "sInfo": "从 _START_ 到 _END_ /共 _TOTAL_ 条数据",
                "sInfoEmpty": '',
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
        $('#backup_point tbody').on('click', 'button#select', function () {
            var table = $('#backup_point').DataTable();
            var data = table.row($(this).parents('tr')).data();
            var pre_data = table.row($(this).parents('tr').next()).data();
            $('#pre_restore_time').val(pre_data.LastTime);
            $("#datetimepicker").val(data.LastTime);
            $("input[name='optionsRadios'][value='1']").prop("checked", false);
            $("input[name='optionsRadios'][value='2']").prop("checked", true);
            $("#browseJobId").val(data.jobId);
            $("#data_sp").val(data.data_sp);
        });

        $("#recovery_time_redio_group").click(function () {
            if ($("input[name='optionsRadios']:checked").val() == 1) {
                $("#datetimepicker").val("");
            }
        });
    });

    $('#datetimepicker').datetimepicker({
        format: 'yyyy-mm-dd hh:ii:ss',
        pickerPosition: 'top-right'
    });
    $('#recovery').click(function () {
        if ($("input[name='optionsRadios']:checked").val() == "2" && $('#datetimepicker').val() == "")
            alert("请输入时间。");
        else {
            if ($('#destClient').val() == "")
                alert("请选择目标客户端。");
            else {
                var myrestoreTime = "";
                if ($("input[name='optionsRadios']:checked").val() == "2" && $('#datetimepicker').val() != "") {
                    myrestoreTime = $('#datetimepicker').val();
                }
                $.ajax({
                    type: "POST",
                    url: "../../dooraclerecovery/",
                    data: {
                        sourceClient: $('#sourceClient').val(),
                        destClient: $('#destClient').val(),
                        restoreTime: myrestoreTime,
                        browseJobId: $("#browseJobId").val(),
                        // 判断是oracle还是oracle rac
                        agent: $("#agent").val(),
                        data_path: $("#data_path").val(),
                        copy_priority: $("#copy_priority").val(),
                        data_sp: $("#data_sp").val(),
                    },
                    success: function (data) {
                        alert(data);
                        $("#static1").modal("hide");
                    },
                    error: function (e) {
                        alert("恢复失败，请于客服联系。");
                    }
                });
            }
        }
    });
});