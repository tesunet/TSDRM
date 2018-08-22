var Activate = function () {


    var handleActivate = function () {


        $('.activate-form').validate({
            errorElement: 'span', //default input error message container
            errorClass: 'help-block', // default input error message class
            focusInvalid: false, // do not focus the last invalid input
            ignore: "",
            rules: {
                poolname: {
                    required: true,
                },
                name: {
                    required: true,
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


    };

    return {
        //main function to initiate the module
        init: function () {

            handleActivate();
        }
    };

}();

$(document).ready(function () {
    Activate.init();
    $('#sample_2').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../vmresourcepooldata/",
        "columns": [
            {"data": "id"},
            {"data": "name"},
            {"data": "type"},
            {"data": "description"},
            {"data": null}
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

    $('#sample_2 tbody').on('click', 'button#select', function () {
        var table = $('#sample_2').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $("#poolid").val(data.id);
        $("#poolname").val(data.name);
        $('#static1').modal('hide');
        $("#name").empty();
        $.ajax({
            type: "POST",
            url: "../getvmresourcelist/",
            data:
                {pool_id: $("#poolid").val()},
            dataType: "json",
            success: function (data) {
                for (var i = 0; i < data.data.length; i++) {
                    $("#name").append("<option uuid=''" + data.data[i]['uuid'] + "' cpu='" +  data.data[i]["cpu"]  +  " ' memory='" + data.data[i]['memory'] + "' disk='" + data.data[i]['disk']+ "' value='" + data.data[i]["vm_name"] + "'>" + data.data[i]["vm_name"] + "</option>");
                }
            }
        });


    });

    $('#sample_1').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../vmresourcedata/",
        "columns": [
            {"data": "id"},
            {"data": "template_name"},
            {"data": "name"},
            {"data": "cpu"},
            {"data": "memory"},
            {"data": "disks"},
            {"data": "vm_num"},
            {"data": "state_tag"},
            {"data": null}
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
                url: "../vmresourcedel/",
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
        $("#poolid").val(data.pool_id);
        $("#poolname").val(data.pool_name);
        $("#id").val(data.id);
        $("#cpu_").val(data.cpu);
        $("#memory_").val(data.memory);
        $("#disk_").val(data.disks);
        $("#vm_num").val(data.vm_num);

        $("#template").val(data.template_name);
        $("#description").val(data.description);
        $("#system").val(data.system);
        $("#uuid").val(data.uuid);
        $("#name").empty();
        var selectedname=data.name;
        $("#name").append("<option value='" + selectedname + "'>" + selectedname + "</option>");
        $("#name").val(selectedname);
        $.ajax({
            type: "POST",
            url: "../getvmresourcelist/",
            data:
                {pool_id: data.pool_id,},
            dataType: "json",
            success: function (data) {
                $("#name").empty();
                for (var i = 0; i < data.data.length; i++) {
                    $("#name").append("<option uuid='" + data.data[i]['uuid'] + "'cpu='" +  data.data[i]["cpu"]  +  " ' memory='" + data.data[i]['memory'] + "' disk='" + data.data[i]['disk']+ "' value='" + data.data[i]["vm_name"] + "'>" + data.data[i]["vm_name"] + "</option>");
                }
                $("#name").val(selectedname);

            }
        });



    });


    $("#new").click(function () {
        $("#name").empty();
        $("#name").val("");
        $("#poolid").val("");
        $("#poolname").val("");
        $("#cpu_").val("");
        $("#memory_").val("");
        $("#disk_").val("");
        $("#vm_num").val("");
        $("#template").val("");
        $("#description").val("");
        $("#system").val("");
        $("#uuid").val("");

        $("#id").val("0");
    });

    // 联动
    $("#name").change(function () {
        var type1 = $("#name option:selected").attr("cpu");
        var type2 = $("#name option:selected").attr("memory");
        var type3 = $("#name option:selected").attr("disk");
        var uuid = $("#name option:selected").attr("uuid");
        $("#cpu_").val(type1);
        $("#memory_").val(type2);
        $("#disk_").val(type3);
        $("#uuid").val(uuid);
    });

    $('#save').click(function () {
        var table = $('#sample_1').DataTable();
        if ($("#formactivate").validate().form())
            $.ajax({
                type: "POST",
                url: "../vmresourcesave/",
                data: $('#formactivate').serialize(),
                success: function (data) {
                    if (data == "保存成功。") {
                        alert("保存成功。");
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
    });
});
