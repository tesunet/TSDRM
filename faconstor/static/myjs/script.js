$('#tree_2').jstree({
    'core': {
        "themes": {
            "responsive": false
        },
        "check_callback": true,
        'data': treeData
    },

    "types": {
        "NODE": {
            "icon": "fa fa-folder-open icon-state-warning icon-lg"
        },
        "INTERFACE": {
            "icon": "fa fa-file-code-o icon-state-warning icon-lg"
        }
    },
    "contextmenu": {
        "items": {
            "create": null,
            "rename": null,
            "remove": null,
            "ccp": null,
            "新建节点": {
                "label": "新建节点",
                "action": function (data) {
                    var inst = jQuery.jstree.reference(data.reference),
                        obj = inst.get_node(data.reference);
                    if (obj.type == "INTERFACE") {
                        alert("无法在接口下新建节点。");
                    } else {
                        $("#title").text("新建");
                        $("#id").val("0");
                        $("#pid").val(obj.id);
                        $("#my_type").val(obj.type);
                        $("#node_name").val("");
                        $("#node_pname").val(obj.text);
                        $("#remark").val("");

                        $("#interface").hide();
                        $("#node").show();
                        $("#node_save").show();
                    }
                }
            },
            "新建接口": {
                "label": "新建接口",
                "action": function (data) {
                    var inst = jQuery.jstree.reference(data.reference),
                        obj = inst.get_node(data.reference);
                    if (obj.type == "INTERFACE") {
                        alert("无法在接口下新建接口。");
                    } else {
                        $("#title").text("新建")
                        $("#id").val("0")
                        $("#pid").val(obj.id)
                        $("#my_type").val(obj.type)
                        $("#pname").val(obj.text)

                        $("#code").val("");
                        $("#name").val("");
                        $("#interface_type").val("");
                        $("#origin").val("");
                        $("#commv_interface").val("");
                        $("#ip").val("");
                        $("#script_text").val("");
                        $("#success_text").val("");
                        $("#log_address").val("");
                        $("#remark").val("");

                        $("#interface").show()
                        $("#node").hide()
                        $("#interface_save").show()
                    }
                }
            },
            "删除": {
                "label": "删除",
                "action": function (data) {
                    var inst = jQuery.jstree.reference(data.reference),
                        obj = inst.get_node(data.reference);
                    if (obj.children.length > 0)
                        alert("节点下还有其他节点或者接口，无法删除。");
                    else {
                        if (confirm("确定要删除？删除后不可恢复。")) {
                            $.ajax({
                                type: "POST",
                                url: "../scriptdel/",
                                data:
                                    {
                                        id: obj.id,
                                    },
                                success: function (data) {
                                    if (data == 1) {
                                        inst.delete_node(obj);
                                        alert("删除成功！");
                                    } else
                                        alert("删除失败，请于管理员联系。");
                                },
                                error: function (e) {
                                    alert("删除失败，请于管理员联系。");
                                }
                            });
                        }
                    }
                }
            },

        }
    },
    "plugins": ["contextmenu", "dnd", "types", "role"]
})
    .on('move_node.jstree', function (e, data) {
        var moveid = data.node.id;
        if (data.old_parent == "#") {
            alert("根节点禁止移动。");
            location.reload()
        } else {
            if (data.parent == "#") {
                alert("禁止新建根节点。");
                location.reload()
            } else {
                $.ajax({
                    type: "POST",
                    url: "../script_move/",
                    data:
                        {
                            id: data.node.id,
                            parent: data.parent,
                            old_parent: data.old_parent,
                            position: data.position,
                            old_position: data.old_position,
                        },
                    success: function (data) {
                        if (data == "重名") {
                            alert("目标组织下存在重名。");
                            location.reload()
                        } else {
                            if (data == "接口") {
                                alert("不能移动至接口下。");
                                location.reload()
                            } else {
                                if (data != "0") {
                                    if (selectid == moveid) {
                                        var res = data.split('^')
                                        $("#pid").val(res[1])
                                        $("#pname").val(res[0])
                                        $("#node_pname").val(res[0])
                                    }
                                }
                            }
                        }
                    },
                    error: function (e) {
                        alert("移动失败，请于管理员联系。");
                        location.reload()
                    }
                });


            }
        }
    })
    .bind('select_node.jstree', function (event, data) {
        $("#form_div").show();
        var type = data.node.original.type;

        $("#id").val(data.node.id);
        $("#pid").val(data.node.parent);
        $("#my_type").val(type);
        $("#pname").val(data.node.data.pname);
        $("#title").text(data.node.text);

        if (type == "INTERFACE") {
            // 接口编号 接口名称 接口类型 选择源客户端 类名 选择主机 脚本内容 SUCCESSTEXT 日志地址 接口说明
            $("#code").val(data.node.data.code);
            $("#name").val(data.node.data.name);
            $("#ip").val(data.node.data.ip);
            $("#script_text").val(data.node.data.script_text);
            $("#success_text").val(data.node.data.success_text);
            $("#log_address").val(data.node.data.log_address);
            $("#remark").val(data.node.data.remark);
            // Commvault
            $("#origin").val(data.node.data.origin);
            $("#commv_interface").val(data.node.data.commv_interface);
            $("#interface_type").val(data.node.data.interface_type);

            if (data.node.data.interface_type == "Commvault") {
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

            $("#interface").show()
            $("#node").hide()
        }
        if (type == "NODE") {
            $("#node_pname").val(data.node.data.pname)
            $("#node_name").val(data.node.text)
            $("#node_remark").val(data.node.data.remark)
            $("#interface").hide()
            $("#node").show()
        }
        if (data.node.parent == "#") {
            $("#node_save").hide()
            $("#interface_save").hide()
        } else {
            $("#node_save").show()
            $("#interface_save").show()
        }
    });

// interface_type change
$("#interface_type").change(function () {
    var interface_type = $(this).val();
    if (interface_type == "Commvault") {
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

$("#error").click(function () {
    $(this).hide();
});
