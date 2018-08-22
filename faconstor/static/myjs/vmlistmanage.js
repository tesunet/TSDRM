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
        "ajax": "../getvmtemplate/",
        "columns": [
            {"data": "id"},
            {"data": "template_name"},
            {"data": "name"},
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
        $("#datacenter").empty();
        $("#template_name").val(data.template_name);
        $('#static1').modal('hide');
        var id = $("#id").val();
        $.ajax({
            type: "POST",
            url: "../getvmtemplate/",
            data:
                {template_name: data.template_name, "id": id},
            dataType: "json",
            success: function (data) {
                $("#cpu_").val(data.data[0]["cpu"]);
                $("#memory_").val(data.data[0]["memory"]);
                $("#disk_").val(data.data[0]["disks"]);
                $("#name").val(data.data[0]["name"]);
                $("#poolid").val(data.data[0]["pool_id"]);
                $("#template_id").val(data.data[0]["id"]);
                $("#system").val(data.data[0]["system"]);
                $("#datacenter").val(data.data[0]["datacenter"]);
                $("#cluster").val(data.data[0]["cluster"]);

                var poolid = $("#poolid").val();
                $.ajax({
                    type: "POST",
                    url: "../get_dc/",
                    data:
                        {poolid: poolid},
                    dataType: "json",
                    success: function (data) {
                        for (var i = 0; i < data.data.length; i++) {
                            $("#datacenter").append("<option value='" + data.data[i]["dcname"] + "'>" + data.data[i]["dcname"] + "</option>");
                        }
                        var datacenter = $("#datacenter option:selected").val();
                        $.ajax({
                            type: "POST",
                            url: "../get_cluster/",
                            data: {poolid: poolid, datacenter: datacenter},
                            dataType: "json",
                            success: function (data) {
                                for (var i = 0; i < data.data.length; i++) {
                                    $("#cluster").append("<option value='" + data.data[i]["clustername"] + "'>" + data.data[i]["clustername"] + "</option>");
                                }
                            }
                        });
                    }
                });
            }
        });
    });


    $('#sample_1').dataTable({
        "bAutoWidth": true,
        "bSort": false,
        "bProcessing": true,
        "ajax": "../vmlistmanagedata/",
        "columns": [
            {"data": "id"},
            {"data": "instance_name"},
            {"data": "template_template_name"},
            {"data": "name"},
            {"data": "cpu"},
            {"data": "memory"},
            {"data": "disks"},
            {"data": "state_tag"},
            {"data": null},
        ],

        "columnDefs": [{
            "targets": -1,
            "data": null,
            "width": "90px",
            "defaultContent": "<button  id='edit' title='编辑' data-toggle='modal'  data-target='#static'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button><button title='逻辑删除'  id='delrow' class='btn btn-xs btn-primary' type='button'><i class='fa fa-trash-o'></i></button><button title='物理删除'  id='destroyvm' class='btn btn-xs btn-danger' type='button'><i class='fa fa-trash-o'></i></button>"
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

    $('#sample_1 tbody').on('click', 'button#destroyvm', function () {
        if (confirm("确定要删除该数据/销毁当前虚机？")) {
            var table = $('#sample_1').DataTable();
            var data = table.row($(this).parents('tr')).data();
            $.ajax({
                type: "POST",
                url: "../vmresourcedestroy/",
                data:
                    {
                        id: data.id,
                        ip:data.ip,
                        pool_id:data.pool_id,
                        uuid:data.uuid,
                        name:data.name,
                    },
                success: function (data) {
                    if (data == 1) {
                        table.ajax.reload();
                        alert("销毁成功！");
                    }
                    else
                        alert("销毁失败，请于管理员联系。");
                },
                error: function (e) {
                    alert("销毁失败，请于管理员联系。");
                }
            });

        }
    });

    $('#sample_1 tbody').on('click', 'button#edit', function () {
        // hide select button
        $("#bt_select").hide();
        $("#templatediv").addClass("input-group")


        $("#datacenter").empty();
        $("#cluster").empty();
        var table = $('#sample_1').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $("#template_name").val(data.template_template_name);
        $("#id").val(data.id);
        $("#poolid").val(data.pool_id);
        $("#template_id").val(data.template_id);
        $("#uuid").val(data.uuid);
        $("#cpu_").val(data.cpu);
        $("#memory_").val(data.memory);
        $("#disk_").val(data.disks);
        $("#name").val(data.template_name);
        $("#ip").val(data.ip);
        $("#hostname").val(data.hostname);
        $("#clone_tag").val(data.clone);
        $("#datacenter").val(data.datacenter);
        $("#cluster").val(data.cluster);


        $("#onstate").hide();
        $("#offstate").hide();

        var poolid = data.pool_id;
        var name = data.name;

        $.ajax({
            type: "POST",
            url: "../get_dc_clt_from_pool/",
            dataType: 'json',
            data: {poolid: poolid},
            success: function (data) {
                $("#datacenterinput").val(data["datacenter"]);
                $("#clusterinput").val(data["cluster"]);
            },
        });

        if (data.clone == "0") {
            $("#div1").hide();
            $("#div2").show();
            $("#div3").hide();

            $.ajax({
                type: "POST",
                url: "../get_progress/",
                dataType: 'json',
                data: {poolid: data.pool_id, name: data.template_name, id: data.id},
                success: function (data) {
                    if (data["state"] == "3") {
                        $("#uuid").val(data["uuid"]);
                        $("#div1").hide();
                        $("#div2").hide();
                        $("#div3").show();

                        $("#clone_tag").val("1");
                        $.ajax({
                            type: "POST",
                            url: "../get_vm_state/",
                            dataType: 'json',
                            data: {poolid: poolid, name: name},
                            success: function (data) {
                                if (data['state'] == "poweredOn") {
                                    $("#onstate").show();
                                    $("#offstate").hide();
                                } else if (data['state'] == "poweredOff") {
                                    $("#onstate").hide();
                                    $("#offstate").show();
                                } else {
                                    $("#onstate").hide();
                                    $("#offstate").hide();
                                    alert('未定位到当前虚机');
                                }
                            }
                        });
                        table.ajax.reload();
                    } else {
                        $("#progress").attr("style", "width: " + data["progress"] + "%;");

                    }
                },
            })
        }
        else {
            $("#div1").hide();
            $("#div2").hide();
            $("#div3").show();
            $.ajax({
                type: "POST",
                url: "../get_vm_state/",
                dataType: 'json',
                data: {poolid: poolid, name: name},
                success: function (data) {
                    if (data['state'] == "poweredOn") {
                        $("#onstate").show();
                        $("#offstate").hide();
                    } else if (data['state'] == "poweredOff") {
                        $("#onstate").hide();
                        $("#offstate").show();
                    } else {
                        $("#onstate").hide();
                        $("#offstate").hide();
                        alert('未定位到当前虚机');
                    }
                }
            });
        }

        $("#datacenter").append("<option value='" + data.datacenter + "'>" + data.datacenter + "</option>");
        $("#cluster").append("<option value='" + data.cluster + "'>" + data.cluster + "</option>");
        $("#instancename").val(data.instance_name);
        $("#currentvm").val(data.name);
        $("#datacenter").attr("readonly", "readonly");
        $("#cluster").attr("readonly", "readonly");
        $("#instancename").attr("readonly", "readonly");
        $("#currentvm").attr("readonly", "readonly");
        $("#bt_select").attr("readonly", "readonly");

        $("#description").val(data.description);
        $("#system").val(data.system);
    });


    $("#datacenter").change(function () {
        var datacenter = $("#datacenter option:selected").val();
        $.ajax({
            type: "POST",
            url: "../get_cluster/",
            data: {poolid: poolid, datacenter: datacenter},
            dataType: "json",
            success: function (data) {
                for (var i = 0; i < data.data.length; i++) {
                    $("#cluster").append("<option value='" + data.data[i]["clustername"] + "'>" + data.data[i]["clustername"] + "</option>");
                }
            }
        });

    });


    $("#new").click(function () {
        $("#template_id").val("");
        $("#template_name").val("");
        $("#uuid").val("");
        $("#cpu_").val("");
        $("#memory_").val("");
        $("#disk_").val("");
        $("#name").val("");
        $("#datacenter").val("");
        $("#cluster").val("");
        $("#instancename").val("");
        $("#currentvm").val("");
        $("#description").val("");
        $("#system").val("");
        $("#ip").val("");
        $("#hostname").val("");


        $("#bt_select").show();
        $("#datacenter").show();
        $("#cluster").show();
        $("#instancename").removeAttr("readonly");
        $("#currentvm").removeAttr("readonly");
        $("#bt_select").removeAttr("readonly");

        $("#templatediv").removeClass("input-group")

        $("#id").val("0");
        $("#clone_tag").val("0");
        $("#div1").show();
        $("#div2").hide();
        $("#div3").hide();
    });

    $("#refresh").click(function () {
        var table = $('#sample_1').DataTable();
        $.ajax({
            type: "POST",
            url: "../get_progress/",
            dataType: 'json',
            data: {poolid: $("#poolid").val(), name: $("#name").val(), id: $("#id").val()},
            success: function (data) {
                if (data["state"] == "3") {
                    $("#uuid").val(data["uuid"]);
                    $("#div1").hide()
                    $("#div2").hide()
                    $("#div3").show()
                    $("#clone_tag").val("1");
                    table.ajax.reload();
                } else {
                    $("#progress").attr("style", "width: " + data["progress"] + "%;");

                }
            },
        })
    });

    $("#ipsave").click(function () {
        var table = $('#sample_1').DataTable();

        $.ajax({
            type: "POST",
            url: "../vm_ipsave/",
            dataType: 'json',
            data: {
                id: $("#id").val(),
                uuid: $("#uuid").val(),
                poolid: $("#poolid").val(),
                path: $("#ip_path").val(),
                ip: $("#ip_ip").val(),
                mask: $("#ip_mask").val(),
                gateway: $("#ip_gateway").val(),
                dns: $("#ip_dns").val(),
                user: $("#ip_user").val(),
                password: $("#ip_password").val()
            },
            success: function (data) {
                if (data["value"] == "1") {

                    $("#ip").val($("#ip_ip").val());
                    table.ajax.reload();
                    alert(data["text"]);
                } else {
                    alert(data["text"]);

                }
            },
        })
    });

    $("#hostsave").click(function () {
        var table = $('#sample_1').DataTable();
        $.ajax({
            type: "POST",
            url: "../vm_hostsave/",
            dataType: 'json',
            data: {
                id: $("#id").val(),
                uuid: $("#uuid").val(),
                poolid: $("#poolid").val(),
                path: $("#host_path").val(),
                hostname: $("#host_name").val(),
                user: $("#host_user").val(),
                password: $("#host_password").val()
            },
            success: function (data) {
                if (data["value"] == "1") {

                    $("#hostname").val($("#host_name").val());
                    table.ajax.reload();
                    alert(data["text"]);
                } else {
                    alert(data["text"]);

                }
            },
        })
    });
    $("#disksave").click(function () {
        var table = $('#sample_1').DataTable();
        $.ajax({
            type: "POST",
            url: "../vm_disksave/",
            dataType: 'json',
            data: {
                id: $("#id").val(),
                name: $("#currentvm").val(),
                uuid: $("#uuid").val(),
                poolid: $("#poolid").val(),
                disksize: $("#disksize").val(),
                disktype: $("#disktype").val(),
                selectdisk: $("#selectdisk").val(),
                path: $("#disk_path").val(),
                user: $("#disk_user").val(),
                password: $("#disk_password").val()
            },
            success: function (data) {
                if (data["value"] == "1") {

                    $("#disk_").val(data["size"]);
                    table.ajax.reload();
                    alert(data["text"]);
                } else {
                    alert(data["text"]);

                }
            },
        })
    });
    $("#installcvsave").click(function () {
        var table = $('#sample_1').DataTable();
        $.ajax({
            type: "POST",
            url: "../vm_installcvsave/",
            dataType: 'json',
            data: {
                id: $("#id").val(),
                uuid: $("#uuid").val(),
                poolid: $("#poolid").val(),
                hostname: $("#hostname").val(),
                path: $("#installcv_path").val(),
                user: $("#installcv_user").val(),
                password: $("#installcv_password").val()
            },
            success: function (data) {
                if (data["value"] == "1") {
                    alert(data["text"]);
                } else {
                    alert(data["text"]);

                }
            },
        })
    });
    $("#bt_registercv").click(function () {
        var table = $('#sample_1').DataTable();
        $.ajax({
            type: "POST",
            url: "../registercvsave/",
            dataType: 'json',
            data: {hostname: $("#hostname").val()},
            success: function (data) {
                if (data["value"] == "1") {
                    alert(data["text"]);
                } else {
                    alert(data["text"]);

                }
            },
        })
    });

    $("#clone").click(function () {
        var table = $('#sample_1').DataTable();
        if ($("#formactivate").validate().form()) {
            $.ajax({
                type: "POST",
                dataType: 'json',
                url: "../clonevm/",
                data: $('#formactivate').serialize(),
                success: function (data) {
                    if (data["value"] == "1") {
                        $("#id").val(data["id"]);
                        $("#div1").hide();
                        $("#div2").show();
                        $("#div3").hide();

                        var poolid = data['pool_id'];
                        $.ajax({
                            type: "POST",
                            url: "../get_dc_clt_from_pool/",
                            dataType: 'json',
                            data: {poolid: poolid},
                            success: function (data) {
                                $("#datacenter").val(data["datacenter"]);
                                $("#cluster").val(data["cluster"]);
                            },
                        });


                        table.ajax.reload();
                    } else {
                        alert(data);

                    }
                },
                error: function (e) {
                    alert("克隆失败，请于客服联系。");
                }
            })
        }
        else
            alert("输入有误，请重新输入。");
    });

    $("#bt_shutdown").click(function () {
        var table = $('#sample_1').DataTable();
        $.ajax({
            type: "POST",
            url: "../shutdownvm/",
            dataType: 'json',
            data: {
                currentvm: $("#currentvm").val(),
                poolid: $("#poolid").val(),
            },
            success: function (data) {
                alert(data['text']);
                $("#onstate").hide();
                $("#offstate").show();
            },
        });
    });

    $("#bt_reboot").click(function () {
        var table = $('#sample_1').DataTable();
        $.ajax({
            type: "POST",
            url: "../rebootvm/",
            dataType: 'json',
            data: {
                uuid: $("#uuid").val(),
                hostname: $("#hostname").val(),
                poolid: $("#poolid").val(),
            },
            success: function (data) {
                alert(data['text']);
            },
        });
    });

    $("#bt_startup").click(function () {
        var table = $('#sample_1').DataTable();
        $.ajax({
            type: "POST",
            url: "../poweronvm/",
            dataType: 'json',
            data: {
                currentvm: $("#currentvm").val(),
                poolid: $("#poolid").val(),
            },
            success: function (data) {
                alert(data['text']);
                $("#onstate").show();
                $("#offstate").hide();
            },
        });
    });
});
