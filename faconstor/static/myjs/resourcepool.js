var Activate = function () {


    var handleActivate = function () {


        $('.activate-form').validate({
            errorElement: 'span', //default input error message container
            errorClass: 'help-block', // default input error message class
            focusInvalid: false, // do not focus the last invalid input
            ignore: "",
            rules: {
                name: {
                    required: true,
                },
                ip: {
                    required: true,
                },
                username: {
                    required: true
                },
                password: {
                    required: true
                },
            },

            messages: { // custom messages for radio buttons and checkboxes
            },

            invalidHandler: function (event, validator) { //display error alert on form submit

            },

            highlight: function (element) { // hightlight error inputs
                $(element)
                    .closest('.form-group').addClass('has-error'); // set error class to the control group
            },

            success: function (label) {
                label.closest('.form-group').removeClass('has-error');
                label.remove();
            },


            submitHandler: function (form) {
                form.submit();
            }
        });


    }

    return {
        //main function to initiate the module
        init: function () {

            handleActivate();
        }
    };

}();

$(document).ready(function () {
    Activate.init();
    $('#sample_1').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../resourcepooldata/",
        "columns": [
            {"data": "id"},
            {"data": "name"},
            {"data": "type"},
            {"data": "description"},
            {"data": null},
        ],

        "columnDefs": [{
            "targets": -1,
            "data": null,
            "defaultContent": "<button  id='edit' title='编辑' data-toggle='modal'  data-target='#static'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button><button title='删除'  id='delrow' class='btn btn-xs btn-primary' type='button'><i class='fa fa-trash-o'></i></button>"
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
    // 行按钮
    $('#sample_1 tbody').on('click', 'button#delrow', function () {
        if (confirm("确定要删除该条数据？")) {
            var table = $('#sample_1').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $.ajax({
                type: "POST",
                url: "../resourcepooldel/",
                data:
                    {
                        id: data.id
                    },
                success: function (data) {
                    if (data == 1) {
                        table.ajax.reload();
                        alert("删除成功！");
                    }
                    else
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
        var mysupplier = data.supplier
        $("#supplier").empty();
        $.ajax({
            type: "POST",
            url: "../getvendorlist/",
            data:
                {
                    type: data.type
                },
            dataType: "json",
            success: function (data) {
                for (var i = 0; i < data.length; i++) {
                    $("#supplier").append("<option value='" + data[i]["vendorGUID"] + "'>" + data[i]["name"] + "</option>");

                }
                $("#supplier").val(mysupplier);
            },
        });
        $("#id").val(data.id);
        $("#name").val(data.name);
        $("#type").val(data.type);
        $("#description").val(data.description);

        $("#ip").val(data.ip);
        $("#username").val(data.username);
        $("#password").val(data.password);
        if ($("#type").val() != "虚机资源") {
            $('#datacenter_').hide();
            $('#cluster_').hide();
        }else{
            $('#datacenter_').show();
            $('#cluster_').show();
        }
        $('#datacenter').val(data.datacenter);
        $('#cluster').val(data.cluster);
    });
    $("#type").change(function () {
        $("#supplier").empty();
        $.ajax({
            type: "POST",
            url: "../getvendorlist/",
            data:
                {
                    type: $("#type").val()
                },
            dataType: "json",
            success: function (data) {
                for (var i = 0; i < data.length; i++) {
                    $("#supplier").append("<option value='" + data[i]["vendorGUID"] + "'>" + data[i]["name"] + "</option>");

                }
            },
        });
        if ($("#type").val() != "虚机资源") {
            $('#datacenter_').hide();
            $('#cluster_').hide();
        }else{
            $('#datacenter_').show();
            $('#cluster_').show();
        }
    });

    $("#new").click(function () {
        $("#supplier").empty();
        $("#id").val("0");
        $("#name").val("");
        $("#description").val("");
        $("#type").val("");
        $("#supplier").val("");
        $("#ip").val("");
        $("#username").val("");
        $("#password").val("");
        if ($("#type").val() != "虚机资源") {
            $('#datacenter_').hide();
            $('#cluster_').hide();
        }else{
            $('#datacenter_').show();
            $('#cluster_').show();
        }
        $('#datacenter').val("");
        $('#cluster').val("");
    });

    // 选择隐藏

    $('#save').click(function () {
        var table = $('#sample_1').DataTable();
        if ($("#formactivate").validate().form())

            $.ajax({
                type: "POST",
                url: "../resourcepoolsave/",
                data: $('#formactivate').serialize(),
                success: function (data) {
                    alert(data);
                    if (data == "保存成功。") {
                        $('#static').modal('hide');
                        table.ajax.reload();
                    }
                },
                error: function (e) {
                    alert("保存失败，请于客服联系。");
                }
            });
        else
            alert("输入有误，请重新输入。");
    })


});