$(document).ready(function () {
    $('#hosts_dt').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../hosts_manage_data/",
        "columns": [
            {"data": "host_id"},
            {"data": "host_ip"},
            {"data": "host_name"},
            {"data": "os"},
            {"data": "type"},
            {"data": "username"},
            {"data": "password"},
            {"data": null}
        ],

        "columnDefs": [{
            "targets": -2,
            "visible": false,
        }, {
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
    $('#hosts_dt tbody').on('click', 'button#delrow', function () {
        if (confirm("确定要删除该条数据？")) {
            var table = $('#hosts_dt').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $.ajax({
                type: "POST",
                url: "../hosts_manage_del/",
                data: {
                    host_id: data.host_id,
                },
                success: function (data) {
                    if (data.ret == 1) {
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
    $('#hosts_dt tbody').on('click', 'button#edit', function () {
        var table = $('#hosts_dt').DataTable();
        var data = table.row($(this).parents('tr')).data();

        $("#host_id").val(data.host_id);
        $("#host_ip").val(data.host_ip);
        $("#host_name").val(data.host_name);
        $("#os").val(data.os);
        $("#type").val(data.type);
        $("#username").val(data.username);
        $("#password").val(data.password);

        // 动态参数
        $('#param_se').empty();
        var variable_param_list = data.variable_param_list;
        for (var i = 0; i < variable_param_list.length; i++) {
            $('#param_se').append('<option value="' + variable_param_list[i].variable_name + '">' + variable_param_list[i].param_name + ': ' + variable_param_list[i].param_value + '</option>');
        }
    });

    $("#new").click(function () {
        $("#host_id").val("0");
        $("#host_ip").val("");
        $("#host_name").val("");
        $("#os").val("");
        $("#type").val("");
        $("#username").val("");
        $("#password").val("");
    });

    $('#save').click(function () {
        var table = $('#hosts_dt').DataTable();
        var params_list = [];

        // 构造参数Map>> Array (动态参数)
        $('#param_se option').each(function () {
            // 构造单个参数信息
            var txt_param_list = $(this).text().split(":");
            var val_param = $(this).prop("value");
            var param_dict = {
                "param_name": txt_param_list[0],
                "variable_name": val_param,
                "param_value": txt_param_list[1]
            };
            params_list.push(param_dict)
        });
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../host_save/",
            data: {
                host_id: $("#host_id").val(),
                host_ip: $("#host_ip").val(),
                host_name: $("#host_name").val(),
                os: $("#os").val(),
                type: $("#type").val(),
                username: $("#username").val(),
                password: $("#password").val(),
                config: JSON.stringify(params_list)
            },
            success: function (data) {
                if (data.ret == 1) {
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

    $("#os").change(function () {
        if ($(this).val() == 'Linux') {
            $("#type").val("SSH");
        } else if ($(this).val() == 'Windows') {
            $("#type").val("BAT");
        } else {
            $("#type").val("");
        }
    });
    $("#type").change(function () {
        if ($(this).val() == 'SSH') {
            $("#os").val("Linux");
        } else if ($(this).val() == 'BAT') {
            $("#os").val("Windows");
        } else {
            $("#os").val("");
        }
    });

    $('#error').click(function () {
        $(this).hide()
    });

    $('#param_se').contextmenu({
        target: '#context-menu2',
        onItem: function (context, e) {
            if ($(e.target).text() == "新增") {
                $('#param_operate').val('new');

                // 清空所有子节点
                $('#params').empty();

                // 新增节点
                $("#params").append(
                    '<div class="form-group">' +
                    '<label class="col-md-2 control-label"><span style="color:red; "></span>参数名称</label>' +
                    '<div class="col-md-10">' +
                    '<input id="param_name" type="text" name="param_name" class="form-control" placeholder="">' +
                    '<div class="form-control-focus"></div>' +
                    '</div>' +
                    '</div>' +
                    '<div class="form-group">' +
                    '<label class="col-md-2 control-label"><span style="color:red; "></span>变量设置</label>' +
                    '<div class="col-md-10">' +
                    '<input id="variable_name" type="text" name="variable_name" class="form-control" placeholder="">' +
                    '<div class="form-control-focus"></div>' +
                    '</div>' +
                    '</div>' +
                    '<div class="form-group">' +
                    '<label class="col-md-2 control-label"><span style="color:red; "></span>参数值</label>' +
                    '<div class="col-md-10">' +
                    '<input id="param_value" type="text" name="param_value" class="form-control" placeholder="">' +
                    '<div class="form-control-focus"></div>' +
                    '</div>' +
                    '</div>'
                );

                $("button#param_edit").click();
            }
            if ($(e.target).text() == "修改") {
                $('#param_operate').val('edit');
                if ($("#param_se").find('option:selected').length == 0)
                    alert("请选择要修改的参数。");
                else {
                    if ($("#param_se").find('option:selected').length > 1)
                        alert("修改时请不要选择多条记录。");
                    else {
                        var alpha_param = $("#param_se").val();
                        var params_t = $("#param_se").find('option:selected').text();

                        var params_t_list = params_t.split(":");

                        var txt_param = params_t_list[0];
                        var v_param = params_t_list[1];

                        $("#params").empty();
                        $("#params").append(
                            '<div class="form-group">' +
                            '<label class="col-md-2 control-label"><span style="color:red; "></span>参数名称</label>' +
                            '<div class="col-md-10">' +
                            '<input id="param_name" type="text" name="param_name" value="' + txt_param + '" class="form-control" placeholder="">' +
                            '<div class="form-control-focus"></div>' +
                            '</div>' +
                            '</div>' +
                            '<div class="form-group">' +
                            '<label class="col-md-2 control-label"><span style="color:red; "></span>变量设置</label>' +
                            '<div class="col-md-10">' +
                            '<input id="variable_name" type="text" name="variable_name" value="' + alpha_param + '" class="form-control" placeholder="">' +
                            '<div class="form-control-focus"></div>' +
                            '</div>' +
                            '</div>' +
                            '<div class="form-group">' +
                            '<label class="col-md-2 control-label"><span style="color:red; "></span>参数值</label>' +
                            '<div class="col-md-10">' +
                            '<input id="param_value" type="text" name="param_value" value="' + v_param + '" class="form-control" placeholder="">' +
                            '<div class="form-control-focus"></div>' +
                            '</div>' +
                            '</div>'
                        );
                        $("button#param_edit").click();
                    }
                }

            }
            if ($(e.target).text() == "删除") {
                $('#param_operate').val('delete');
                if ($("#param_se").find('option:selected').length == 0)
                    alert("请选择要删除的参数。");
                else {
                    if (confirm("确定要删除该参数吗？")) {
                        $("#param_se").find('option:selected').remove();
                    }
                }
            }
        }
    });
    $('#params_save').click(function () {
        var param_operate = $('#param_operate').val();
        var param_name = $('#param_name').val();
        var variable_name = $('#variable_name').val();
        var param_value = $('#param_value').val();

        var add = true;
        // 判断参数变量名是否重复
        $('#param_se option').each(function () {
            if ($(this).prop("value") == variable_name && variable_name != "") {
                alert("变量名不可重复添加。")
                add = false;
                return false;
            }
        });

        if (add) {
            if (param_operate == "new") {
                $('#param_se').append('<option value="' + variable_name + '">' + param_name + ': ' + param_value + '</option>');
            }
            if (param_operate == "edit") {
                // 指定value的option修改text
                $('#param_se option[value="' + variable_name + '"]').text(param_name + ": " + param_value);
            }
            $("#static01").modal("hide");
        }
    });
});