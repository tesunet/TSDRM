function getFunctionDetail(id, node_type){
    $.ajax({
        type: "POST",
        dataType: "JSON",
        url: "../get_fun_detail/",
        data: {
            id: id,
        },
        success: function (data) {
            var status = data.status,
                info = data.info,
                data = data.data;
            if (status == 0){
                alert(info);
            } else {
                $("#title").text(data.name);
                $("#name").val(data.name);
                $("#pname").val(data.pname);
                $("#mytype").val(node_type);

                if (node_type == "fun") {
                    $("#url").val(data.url);
                    $("#icon").val(data.icon);
                    $('input:radio[name=radio2]')[0].checked = true;
                }
                if (node_type == "node") {
                    $('input:radio[name=radio2]')[1].checked = true;
                }
                changeType(node_type);
            }
        }
    });
}


function getFunctiontTree(){
    $.ajax({
        type: "POST",
        dataType: "json",
        url: "../get_fun_tree/",
        data: {
            id: $('#id').val(),
        },
        success: function (data) {
            var status = data.status,
            info = data.info,
            data = data.data;
            if (status == 0){
                alert(info);
            } else {
                $('#tree_2').jstree({
                    'core': {
                        "themes": {
                            "responsive": false
                        },
                        "check_callback": true,
                        'data': data
                    },
                    "types": {
                        "node": {
                            "icon": "fa fa-folder icon-state-warning icon-lg"
                        },
                        "fun": {
                            "icon": "fa fa-file icon-state-warning icon-lg"
                        }
                    },
                    "contextmenu": {
                        "items": {
                            "create": null,
                            "rename": null,
                            "remove": null,
                            "ccp": null,
                            "新建": {
                                "label": "新建",
                                "action": function (data) {
                                    var inst = jQuery.jstree.reference(data.reference),
                                        obj = inst.get_node(data.reference);
                                    if (obj.type == "fun") {
                                        alert("无法在功能下新建节点或功能。");
                                    }
                                    else {
                                        $('input:radio[name=radio2]')[0].checked = true;
                                        $("#title").text("新建")
                                        $("#id").val("0")
                                        $("#pid").val(obj.id)
                                        $("#name").val("")
                                        $("#pname").val(obj.text)
                                        $("#url").val("")
                                        $("#icon").val("")
                                        $("#save").show()
                                    }
                                }
                            },
                            "删除": {
                                "label": "删除",
                                "action": function (data) {
                                    var inst = jQuery.jstree.reference(data.reference),
                                        obj = inst.get_node(data.reference);
                                    if (obj.children.length > 0)
                                        alert("节点下还有其他节点或功能，无法删除。");
                                    else {
                                        if (confirm("确定要删除此节点？删除后不可恢复。")) {
                                            $.ajax({
                                                type: "POST",
                                                url: "../fundel/",
                                                data:
                                                    {
                                                        id: obj.id,
                                                    },
                                                success: function (data) {
                                                    if (data == 1) {
                                                        inst.delete_node(obj);
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
                        }
                        else {
                            if (data.parent == "#") {
                                alert("禁止新建根节点。");
                                location.reload()
                            }
                            else {
                                $.ajax({
                                    type: "POST",
                                    url: "../funmove/",
                                    data:
                                        {
                                            id: data.node.id,
                                            parent: data.parent,
                                            old_parent: data.old_parent,
                                            position: data.position,
                                            old_position: data.old_position,
                                        },
                                    success: function (data) {
                                        if (data == "类型") {
                                            alert("不能移动至功能下。");
                                            location.reload()
                                        }
                                        else {
                                            var selectid = $("#id").val()
                                            if (selectid == moveid) {
                                                var res = data.split('^')
                                                $("#pid").val(res[1])
                                                $("#pname").val(res[0])
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
                        var node = data.node;
                        $("#id").val(node.id);
                        $("#pid").val(node.parent);
                        if (node.parent == "#") {
                            $("#save").hide();
                            $("#formdiv").hide();
                        } else{
                            $("#formdiv").show();
                            $("#save").show();
                            getFunctionDetail(node.id, node.type);
                        }
                    });
            }
        }
    });
}

getFunctiontTree();

$('#save').click(function(){
    var save_type = "";
    if ($('input:radio[name=radio2]')[0].checked == true){
        save_type = "fun";
    } else {
        save_type = "node";
    }
    $.ajax({
        type: "POST",
        dataType: "JSON",
        url: "../fun_save/",
        data: $('#fun_form').serialize(),
        success: function(data){
            var status = data.status,
                info = data.info,
                select_id = data.data;
            if (status == 1){
                if ($("#id").val() == "0") {
                    $('#tree_2').jstree('create_node', $("#pid").val(), {
                        "text": $("#name").val(),
                        "id": select_id,
                        "type": save_type,
                    }, "last", false, false);

                    $("#id").val(select_id)
                    $('#tree_2').jstree('deselect_all');
                    $('#tree_2').jstree('select_node', $("#id").val(), true);
                }
                else {
                    var curnode = $('#tree_2').jstree('get_node', $("#id").val());
                    var name = $('#name').val();
                    var newtext = curnode.text.replace(curnode.text, name);
                    curnode.text = newtext;
                    curnode.type = save_type;  // 修改类型
                    $("#mytype").val(save_type);
                    $('#tree_2').jstree('set_text', $("#id").val(), newtext);
                    $('#title').text(newtext);
                }
            }   
            alert(info);
        }
    })
});

function changeType(mytype){
    if (mytype == "fun"){
        $('input:radio[name=radio2]')[0].checked = true;
    }
    if (mytype == "node"){
        $('input:radio[name=radio2]')[1].checked = true;
    }
}
changeType($('#mytype').val());

