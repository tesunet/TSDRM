var Activate = function () {


    var handleActivate = function () {


        $('.activate-form').validate({
            errorElement: 'span', //default input error message container
            errorClass: 'help-block', // default input error message class
            focusInvalid: false, // do not focus the last invalid input
            ignore: "",
            rules: {
                email: {
                    required: true,
                    email: true
                },
                phone: {
                    required: true,
                    phone: true
                },

                username: {
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
        "ajax": "../childuserdata/",
        "columns": [
            {"data": "id"},
            {"data": "username"},
            {"data": "email"},
            {"data": "phone"},
            {"data": "fullname"},
            {"data": "company"},
            {"data": "tell"},
            {"data": "state"},
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
                url: "../childuserdel/",
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
        $("#username").attr("readonly", "readonly")
        $("#id").val(data.id);
        $("#username").val(data.username);
        $("#email").val(data.email);
        $("#phone").val(data.phone);
        $("#fullname").val(data.fullname);
        $("#company").val(data.company);
        $("#tell").val(data.tell);
        var selectedhost = data.selectedhost;
        $("#my_multi_select1").empty();
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../getallclients/",
            data:
                {
                    id: $("#id").val(),
                },
            success: function (data) {
                for (var i = 0; i < data.data.length; i++) {
                    $("#my_multi_select1").append("<option value='" + data.data[i]["clientName"] + "'>" + data.data[i]["clientName"] + "</option>");
                }
                for (var i = 0; i < selectedhost.length; i++) {
                    try {
                        $("#my_multi_select1 option[value='" + selectedhost[i] + "']").prop("selected", true);
                    } catch (err) {
                    }
                }
                $('#my_multi_select1').multiSelect('refresh');
            },
            error: function (e) {
                alert("页面出现错误，请于管理员联系。");
            }
        });

    });

    $("#new").click(function () {
        $("#username").removeAttr("readonly");
        $("#id").val("0");
        $("#username").val("");
        $("#email").val("");
        $("#phone").val("");
        $("#fullname").val("");
        $("#company").val("");
        $("#tell").val("");

        $("#my_multi_select1").empty();
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../getallclients/",
            data:
                {
                    id: $("#id").val(),
                },
            success: function (data) {
                for (var i = 0; i < data.data.length; i++) {
                    $("#my_multi_select1").append("<option value='" + data.data[i]["clientName"] + "'>" + data.data[i]["clientName"] + "</option>");
                }
                $('#my_multi_select1').multiSelect('refresh');
            },
            error: function (e) {

                alert("页面出现错误，请于管理员联系。");
            }
        });


    });


    $('#save').click(function () {
        var table = $('#sample_1').DataTable();
        if ($("#formactivate").validate().form())

            $.ajax({
                type: "POST",
                url: "../childusersave/",
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
    $('#my_multi_select1').multiSelect({
        selectableHeader: "<input type='text' class='search-input' autocomplete='off' placeholder='未选择'>",
        selectionHeader: "<input type='text' class='search-input' autocomplete='off' placeholder='已选择'>",
        afterInit: function (ms) {
            var that = this,
                $selectableSearch = that.$selectableUl.prev(),
                $selectionSearch = that.$selectionUl.prev(),
                selectableSearchString = '#' + that.$container.attr('id') + ' .ms-elem-selectable:not(.ms-selected)',
                selectionSearchString = '#' + that.$container.attr('id') + ' .ms-elem-selection.ms-selected';

            that.qs1 = $selectableSearch.quicksearch(selectableSearchString)
                .on('keydown', function (e) {
                    if (e.which === 40) {
                        that.$selectableUl.focus();
                        return false;
                    }
                });

            that.qs2 = $selectionSearch.quicksearch(selectionSearchString)
                .on('keydown', function (e) {
                    if (e.which == 40) {
                        that.$selectionUl.focus();
                        return false;
                    }
                });
        },
        afterSelect: function () {
            this.qs1.cache();
            this.qs2.cache();
        },
        afterDeselect: function () {
            this.qs1.cache();
            this.qs2.cache();
        }
    });
});