function getProcessDetail(id, node_type){
    $.ajax({
        type: "POST",
        dataType: "JSON",
        url: "../get_process_detail/",
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
                $("#title").text(data.process_name);
                $("#my_type").val(node_type);
                if (node_type == "PROCESS") {
                    $("#processdiv").show();
                    $("#nodediv").hide();
                    $("#pname").val(data.pname);
                    $("#name").val(data.process_name);
                    $("#remark").val(data.process_remark);
                    $("#sign").val(data.process_sign);
                    $("#rto").val(data.process_rto);
                    $("#rpo").val(data.process_rpo);
                    $("#sort").val(data.process_sort);
                    $("#process_color").val(data.process_color);
                    $("#cv_client").val(data.cv_client);
                    $("#process_main_database").val(data.main_database);
                    $("#type").val(data.type);
                    $("#processtype").empty()
                    if (data.processtype=="1") {
                        $('#processtype').append('<option value="1">主流程</option>');
                        $('#processtype_div').show();
                    }else{
                        $('#processtype').append('<option value="2">回切流程</option>');
                        $('#processtype').append('<option value="3">排错流程</option>');
                        $('#processtype_div').hide();
                    }
                    $("#processtype").val(data.processtype);
            
                    if (data.type == "Oracle ADG" || data.type == "MYSQL") {
                        $("#adg_div").show();
                    } else {
                        $("#adg_div").hide();
                    }
                    if (data.type == "Commvault") {
                        $("#cv_clients_div").show();
                    } else {
                        $("#cv_clients_div").hide();
                    }
                    
                    // 回切流程
                    getProcessBack(data.type);
                    $('#process_back').val(data.p_back);
                    // 动态参数
                    $('#param_se').empty();
                    var variable_param_list = data.variable_param_list;
                    for (var i = 0; i < variable_param_list.length; i++) {
                        $('#param_se').append('<option value="' + variable_param_list[i].variable_name + '">' + variable_param_list[i].param_name + ':' + variable_param_list[i].variable_name + ':' + variable_param_list[i].param_value + '</option>');
                    }
                }
                if (node_type == "NODE") {
                    $("#node_pname").val(data.pname)
                    $("#node_name").val(data.process_name)
                    $("#node_remark").val(data.remark)
                    $("#processdiv").hide()
                    $("#nodediv").show()
                }
            }
        }
    });
}

function getProcessTree(){
    $.ajax({
        type: "POST",
        dataType: "json",
        url: "../get_process_tree/",
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
                $('#p_tree').jstree({
                    'core': {
                        "themes": {
                            "responsive": false
                        },
                        "check_callback": true,
                        'data': data
                    },
                    "types": {
                        "NODE": {
                            "icon": "fa fa-folder icon-state-warning icon-lg"
                        },
                        "PROCESS": {
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
                                    if (obj.type == "PROCESS") {
                                        alert("无法在接口下新建节点。");
                                    } else {
                                        $("#form_div").show();
                                        $("#title").text("新建");
                                        $("#id").val("0");
                                        $("#pid").val(obj.id);
                                        $("#my_type").val("NODE");
                                        $("#node_name").val("");
                                        $("#node_pname").val(obj.text);
                                        $("#remark").val("");
                
                                        $("#processdiv").hide();
                                        $("#nodediv").show();
                                        $("#node_save").show();
                                    }
                                }
                            },
                            "新建场景": {
                                "label": "新建场景",
                                "action": function (data) {
                                    var inst = jQuery.jstree.reference(data.reference),
                                        obj = inst.get_node(data.reference);
                                    if (obj.type == "PROCESS" && obj.data.processtype != "1") {
                                            alert("无法在子场景下新建场景。");
                                    } else {
                                        $("#processtype").empty()
                                        if (obj.type == "PROCESS"){
                                            $('#processtype').append('<option selected value="2">回切流程</option>');
                                            $('#processtype').append('<option value="3">排错流程</option>');
                                        }else{
                                            $('#processtype').append('<option value="1" selected>主流程</option>');
                                        }
                
                                        $("#form_div").show();
                                        $("#processdiv").show();
                                        $("#nodediv").hide();
                                        $("#interface_save").show();
                                        $("#title").text("新建");
                                        $("#my_type").val("PROCESS");
                                        $("#id").val("0");
                                        $("#pid").val(obj.id);
                                        $("#pname").val(obj.text);
                                        $("#name").val("");
                                        $("#remark").val("");
                                        $("#sign").val("");
                                        $("#rto").val("");
                                        $("#rpo").val("");
                                        $("#sort").val("");
                                        $("#process_color").val("");
                                        $("#type").val("");
                                        $('#param_se').empty();
                                        $("#adg_div").hide();
                                        $("#cv_clients_div").hide();
                                        
                                        $('#process_main_database').val(""); // 主数据库
                                        $('#process_back').val(""); // 回切流程
                                        $('#cv_client').val(""); // 关联客户端
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
                                                url: "../process_del/",
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
                    .bind('select_node.jstree', function (event, data) {
                        var node = data.node;
                        $('#id').val(node.id);
                        $('#pid').val(node.parent);
                        if (node.parent == "#"){
                            $("#form_div").hide();
                            $("#node_save").hide();
                            $("#interface_save").hide();
                        } else {
                            $("#form_div").show();
                            $("#node_save").show();
                            $("#interface_save").show();
                            getProcessDetail(node.id, node.type);
                        }
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
                                    url: "../process_move/",
                                    data: {
                                        id: data.node.id,
                                        parent: data.parent,
                                        old_parent: data.old_parent,
                                        position: data.position,
                                        old_position: data.old_position,
                                    },
                                    success: function (data) {
                                        if (data == "重名") {
                                            alert("目标节点下存在重名。");
                                            location.reload()
                                        } else {
                                            if (data == "主场景") {
                                                alert("主场景不能移动至场景下。");
                                                location.reload()
                                            } else {
                                                if (data == "子场景") {
                                                    alert("子场景不能移动至节点下。");
                                                    location.reload()
                                                }else {
                                                    if (data != "0") {
                                                        var selectid = $("#id").val();
                                                        if (selectid == moveid) {
                                                            var res = data.split('^')
                                                            $("#pid").val(res[1])
                                                            $("#pname").val(res[0])
                                                            $("#node_pname").val(res[0])
                                                        }
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
                    });
            }
        }
    });
}

getProcessTree();

function getProcessBack(agent_type){
    /**
     * 获取对应Agent类型的回切流程 当前父节点下
     */
    var id = $('#id').val();
    $('#process_back').empty();
    $('#process_back').append('<option value="">无</option>');
    try {
        var p_backs = eval($('#p_backs').val());
        for (var i=0; i < p_backs.length; i++){
            if (p_backs[i].type == agent_type && p_backs[i].pnode_id == id){
                $('#process_back').append('<option value="' + p_backs[i].id + '">' + p_backs[i].name + '</option>');
            }
        }
    } catch(e){

    }
}
getProcessBack($('type').val());  // 新增时需要

$('#node_save, #interface_save').click(function (data){
    var save_type = $(this).prop("id");
    $.ajax({
        type: "POST",
        dataType: "JSON",
        url: "../process_save/",
        data: $('#p_form').serialize(),
        success: function (data){
            var status = data.status,
                info = data.info,
                select_id = data.data;
            if (status == 1){
                if ($("#id").val() == "0") {
                    if (save_type == "node_save"){
                        $('#p_tree').jstree('create_node', $("#pid").val(), {
                            "text": $("#node_name").val(),
                            "id": select_id,
                            "type": "NODE",
                        }, "last", false, false);
                    } else {
                        $('#p_tree').jstree('create_node', $("#pid").val(), {
                            "text": $("#name").val(),
                            "id": select_id,
                            "type": "PROCESS",
                        }, "last", false, false);
                    }

                    $("#id").val(select_id);
                    $('#p_tree').jstree('deselect_all');
                    $('#p_tree').jstree('select_node', $("#id").val(), true);
                } else {
                    var curnode = $('#p_tree').jstree('get_node', $("#id").val());
                    var name = "";
                    if (save_type == "node_save"){
                        name = $("#node_name").val();
                    } else {
                        name = $('#name').val();
                    }
                    var newtext = curnode.text.replace(curnode.text, name);
                    curnode.text = newtext;
                    $('#p_tree').jstree('set_text', $("#id").val(), newtext);
                    $('#title').text(newtext);
                }
            }   
            alert(info);
        }
    });
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
                    var txt_param = params_t_list[0].trim();
                    var v_param = params_t_list[2].trim();

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
                    insertParams();
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
    var existed = false;
    if (param_operate == "new") {
        // 判断是否重复
        $("#param_se option").each(function () {
            if (variable_name == $(this).val()) {
                existed = true;
                return false;
            }
        })
        if (!existed) {
            $('#param_se').append('<option value="' + variable_name + '">' + param_name + ':'  + variable_name + ':' + param_value + '</option>');
            $("#static01").modal("hide");
            insertParams();
        } else {
            alert("该变量名(" + variable_name + ")已存在，请重写填写。")
        }
    }
    if (param_operate == "edit") {
        // 非当前选中节点，相同的表示重复
        var paramOption = $("#param_se option");
        for (var i = 0; i < paramOption.length; i++) {
            if (variable_name == $(paramOption[i]).val() && $("#param_se").find('option:selected').get(0).index != i) {
                existed = true;
                break;
            }
        }
        if (!existed) {
            $("#param_se").find('option:selected').val(variable_name).text(param_name+ ':'  + variable_name + ':' + param_value);
            $("#static01").modal("hide");
            insertParams();
        } else {
            alert("该变量名(" + variable_name + ")已存在，请重写填写。")
        }
    }

    // put all params into config 
    var params_list = [];
    $('#param_se option').each(function () {
        var txt_param_list = $(this).text().split(":");
        var val_param = $(this).prop("value");
        var param_dict = {
            "param_name": txt_param_list[0],
            "variable_name": val_param,
            "param_value": txt_param_list[2]
        };
        params_list.push(param_dict)
    });
    $('#config').val(JSON.stringify(params_list))
});

function insertParams() {
    // 修改数据 $('#param_se option')都写入$("#params")
    var params_list = [];

    // 构造参数Map>> Array (动态参数)
    $('#param_se option').each(function () {
        // 构造单个参数信息
        var txt_param_list = $(this).text().split(":");
        var val_param = $(this).prop("value");
        var param_dict = {
            "param_name": txt_param_list[0],
            "variable_name": val_param,
            "param_value": txt_param_list[2]
        };
        params_list.push(param_dict)
    });
    $("#insert_params").val(JSON.stringify(params_list));
}

$("#type").change(function () {
    getProcessBack($(this).val());
    if ($("#type").val()=="Oracle ADG" || $("#type").val()=="MYSQL"){
        $("#adg_div").show();
    }
    else{
        $("#adg_div").hide();
    }
    if ($(this).val() == "Commvault"){
        $("#cv_clients_div").show();
    } else{
        $("#cv_clients_div").hide();
    } 
});