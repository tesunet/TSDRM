$(document).ready(function () {
    $('#sample_1').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../scriptdata/",
        "columns": [
            {"data": "id"},
            {"data": "code"},
            {"data": "name"},
            {"data": "interface_type"},
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
    $('#sample_1 tbody').on('click', 'button#delrow', function () {
        if (confirm("确定要删除该条数据？")) {
            var table = $('#sample_1').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $.ajax({
                type: "POST",
                url: "../scriptdel/",
                data: {
                    id: data.id
                },
                success: function (data) {
                    if (data == 1) {
                        table.ajax.reload();
                        alert("删除成功！");
                    } else
                        alert("删除失败，请于管理员联系。");
                },
                error: function (e) {
                    alert("删除失败，请于管理员联系。");
                }
            });

        }
    });
    $('#sample_1 tbody').on('click', 'button#edit', function () {
        var table = $('#sample_1').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $("#id").val(data.id);
        $("#code").val(data.code);
        $("#name").val(data.name);

        // 判断是否为commvault
        if (data.interface_type == "commvault") {
            $("#host_id_div").hide();
            $("#script_text_div").hide();
            $("#success_text_div").hide();
            $("#log_address_div").hide();
            $("#origin_div").show();
            $("#commv_interface_div").show();
        } else {
            $("#host_id_div").show();
            $("#script_text_div").show();
            $("#success_text_div").show();
            $("#log_address_div").show();
            $("#origin_div").hide();
            $("#commv_interface_div").hide();
        }

        $("#ip").val(data.host_id);
        $("#filename").val(data.filename);
        $("#scriptpath").val(data.scriptpath);
        $("#success_text").val(data.success_text);
        $("#log_address").val(data.log_address);

        // add
        $("#script_text").val(data.script_text);

        // commvault
        $("#interface_type").val(data.interface_type);
        $("#origin").val(data.origin);
        $("#commv_interface").val(data.commv_interface);
    });

    $("#new").click(function () {
        $("#id").val("0");
        $("#code").val("");
        $("#name").val("");

        $("#ip").val("");
        $("#filename").val("");
        $("#scriptpath").val("");
        $("#success_text").val("");
        $("#log_address").val("");
        $("#script_text").val("");

        // commvault
        $("#origin").val("");
        $("#commv_interface").val("");
        $("#interface_type").val("");

        $("#host_id_div").hide();
        $("#script_text_div").hide();
        $("#success_text_div").hide();
        $("#log_address_div").hide();
        $("#origin_div").hide();
        $("#commv_interface_div").hide();
    });

    // interface_type change
    $("#interface_type").change(function () {
        var interface_type = $(this).val();
        if (interface_type == "commvault") {
            $("#host_id_div").hide();
            $("#script_text_div").hide();
            $("#success_text_div").hide();
            $("#log_address_div").hide();
            $("#origin_div").show();
            $("#commv_interface_div").show();
        } else {
            $("#host_id_div").show();
            $("#script_text_div").show();
            $("#success_text_div").show();
            $("#log_address_div").show();
            $("#origin_div").hide();
            $("#commv_interface_div").hide();
        }
    });

    $('#save').click(function () {
        var table = $('#sample_1').DataTable();

        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../scriptsave/",
            data: {
                id: $("#id").val(),
                code: $("#code").val(),
                name: $("#name").val(),
                ip: $("#ip").val(),
                script_text: $("#script_text").val(),
                success_text: $("#success_text").val(),
                log_address: $("#log_address").val(),

                // commvault接口
                interface_type: $("#interface_type").val(),
                origin: $("#origin").val(),
                commv_interface: $("#commv_interface").val()
            },
            success: function (data) {
                var myres = data["res"];
                var mydata = data["data"];
                if (myres == "新增成功。") {
                    $("#id").val(data["data"]);
                    $('#static').modal('hide');
                    table.ajax.reload();
                }
                if (myres == "修改成功。") {
                    $('#static').modal('hide');
                    table.ajax.reload();
                }

                alert(myres);
            },
            error: function (e) {
                alert("页面出现错误，请于管理员联系。");
            }
        });
    });

    $('#error').click(function () {
        $(this).hide()
    })
});