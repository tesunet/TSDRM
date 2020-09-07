function displayScriptTree() {
    $('#script_tree').data('jstree', false).empty();
    $('#script_tree').jstree({
        'plugins': ["checkbox", "types"],
        'core': {
            "themes": {
                "responsive": false,
            },
            'data': treeData,
            'multiple': false,  // 单选
        },

        "types": {
            "NODE": {
                "icon": "fa fa-folder icon-state-warning icon-lg"
            },
            "INTERFACE": {
                "icon": "fa fa-file-code-o icon-state-warning icon-lg"
            }
        },
        "checkbox": {
            "keep_selected_style": false,  //是否默认选中
            "three_state": false,  //父子级别级联选择
        },
    });
}

function displayParams(if_instance) {
    /*
        参数： if_instance: 区分脚本实例1、脚本0
        响应： 
            根据 脚本内容中 参数符号 从 主机参数、流程参数、脚本参数 匹配出 参数名称、变量、值、类别
    */
    $.ajax({
        type: "POST",
        dataType: "json",
        url: "../display_params/",
        data: {
            process_id: $('#process').val(),
            script_id: $('#scriptid').val(),
            script_instance_id: $('#script_instance_id').val(),
            if_instance: if_instance,
        },
        success: function (data) {
            // $('#process_param_div').children().eq(0).empty();
            $('#script_param_div').children().eq(0).empty();
            // $('#host_param_div').children().eq(0).empty();
            // var process_div_hidden = true;
            var script_div_hidden = true;
            for (var i = 0; i < data.data.length; i++) {
                var params = data.data[i];
                // if (params["type"] == "PROCESS") {
                //     $('#process_param_div').children().eq(0).append('<div class="form-group">\n' +
                //         '    <label class="col-md-2 control-label" style="padding-left: 0;">' + params.param_name + '</label>\n' +
                //         '    <div class="col-md-10">\n' +
                //         '        <input id="' + params.variable_name + '" type="text" name="' + params.variable_name + '" class="form-control" readonly\n' +
                //         '               value="' + params.param_value + '"\n' +
                //         '               >\n' +
                //         '        <div class="form-control-focus"></div>\n' +
                //         '\n' +
                //         '    </div>\n' +
                //         '</div>');
                //     process_div_hidden = false;
                // }
                if (params["type"] == "SCRIPT") {
                    $('#script_param_div').children().eq(0).append('<div class="form-group">\n' +
                        '    <label class="col-md-2 control-label" style="padding-left: 0;">' + params.param_name + '</label>\n' +
                        '    <div class="col-md-10">\n' +
                        '        <input id="' + params.variable_name + '" type="text" name="' + params.variable_name + '" class="form-control"\n' +
                        '               value="' + params.param_value + '"\n' +
                        '               >\n' +
                        '        <div class="form-control-focus"></div>\n' +
                        '\n' +
                        '    </div>\n' +
                        '</div>');
                    script_div_hidden = false;
                }
                // if (params["type"] == "HOST") {
                //     $('#host_param_div').children().eq(0).append('<div class="form-group">\n' +
                //         '    <label class="col-md-2 control-label" style="padding-left: 0;">' + params.param_name + '</label>\n' +
                //         '    <div class="col-md-10">\n' +
                //         '        <input id="' + params.variable_name + '" type="text" name="' + params.variable_name + '" class="form-control" readonly\n' +
                //         '               value="' + params.param_value + '"\n' +
                //         '               >\n' +
                //         '        <div class="form-control-focus"></div>\n' +
                //         '\n' +
                //         '    </div>\n' +
                //         '</div>');
                //     host_div_hidden = false;
                // }
            }
            // if (process_div_hidden) {
            //     $('#process_div').hide();
            // } else {
            //     $('#process_div').show();
            // }
            if (script_div_hidden) {
                $('#script_div').hide();
            } else {
                $('#script_div').show();
            }
        }
    })
}

// 根据工具加载源客户端
$("#utils").empty()
for (var i=0; i<cv_client_data.length; i++){
    if (i==0){
        $("#utils").append('<option value="' + cv_client_data[i].utils_id + '" selected>' + cv_client_data[i].utils_name + '</option>');
        loadOrigins(cv_client_data[i].utils_id);
    } else {
        $("#utils").append('<option value="' + cv_client_data[i].utils_id + '">' + cv_client_data[i].utils_name + '</option>');
    }
}

function loadOrigins(utils_id){
    $('#origin').empty();
    for (var i=0; i<cv_client_data.length; i++){
        if (cv_client_data[i]["utils_id"] == utils_id){
            var origins = cv_client_data[i]["cv_client_list"];
            for (var j=0; j< origins.length; j++){
                $("#origin").append('<option value="' + origins[j].id + '">' + origins[j].host_name + '(' + origins[j].client_name + ')</option>')
            }
            break;
        }
    }
}

$('#utils').change(function(){
    loadOrigins($(this).val());
})

// function loadHostsParams(){
//     $.ajax({
//         type: "POST",
//         dataType: "JSON",
//         url: "../load_hosts_params/",
//         data: {
//             host_id: $('#host_id').val(),
//             script_id: $('#scriptid').val(),
//         },
//         success: function(data){
//             $('#host_param_div').children().eq(0).empty();
//             var host_div_hidden = true;
//             for (var i = 0; i < data.data.length; i++) {
//                 var params = data.data[i];
//                 if (params["type"] == "HOST") {
//                     $('#host_param_div').children().eq(0).append('<div class="form-group">\n' +
//                         '    <label class="col-md-2 control-label" style="padding-left: 0;">' + params.param_name + '</label>\n' +
//                         '    <div class="col-md-10">\n' +
//                         '        <input id="' + params.variable_name + '" type="text" name="' + params.variable_name + '" class="form-control"\n' +
//                         '               value="' + params.param_value + '"\n' +
//                         '               >\n' +
//                         '        <div class="form-control-focus"></div>\n' +
//                         '\n' +
//                         '    </div>\n' +
//                         '</div>');
//                     host_div_hidden = false;
//                 }
//             }
//             if (host_div_hidden) {
//                 $('#host_div').hide();
//             } else {
//                 $('#host_div').show();
//             }
//         }
//     });
// }

// $('#host_id').change(function(){
//     loadHostsParams();
// })

$("#load_script").click(function () {
    var script_tree = $('#script_tree').jstree(true).get_selected(true);
    try {
        if (script_tree[0].type == "INTERFACE") {
            var data = script_tree[0].data;
            /*
            data:
                code: "5-5"
                interface_type: "Linux"
                name: "5-5"
                pname: "第一组"
                remark: ""
                script_text: ""
                success_text: "tesunetsucceed"
                type: "INTERFACE"
                variable_param_list: []
            id: "105"
            parent: "187"
            parents: (3) ["187", "183", "#"]
            */
            // 判断是否为commvault
            $('#script_instance_name_div').show();
            $('#script_instance_remark_div').show();
            $('#sort_div').show();
            $('#error_solved_div').show();
            if (data.interface_type == "Commvault") {
                $("#host_id_div").hide();
                $("#script_text_div").hide();
                $("#success_text_div").hide();
                $("#log_address_div").hide();
                $("#origin_div").show();
                $("#commv_interface_div").show();
                $('#utils_id_div').show();
            } else {
                $("#host_id_div").show();
                $("#script_text_div").show();
                $("#success_text_div").show();
                $("#log_address_div").show();
                $("#origin_div").hide();
                $("#commv_interface_div").hide();
                $('#utils_id_div').hide();
            }
            $("#scriptid").val(script_tree[0].id);
            $("#scriptcode").val(data.code);
            $("#script_name").val(data.name);
            $("#script_text").val(data.script_text);
            $("#success_text").val(data.success_text);

            // commvault
            $("#interface_type").val(data.interface_type);
            $("#commv_interface").val(data.commv_interface);

            displayParams(0);
            // loadHostsParams();
            $("#static03").modal('hide');
        } else {
            alert('请选择接口。')
        }
    } catch(e){
        console.log(e)
        alert('请选择接口。')
    }
});

// 展示树时取消checked
$("#static03").on("shown.bs.modal", function () {
    displayScriptTree();
})

function hideParamsDiv() {
    $('#process_div').hide();
    $('#script_div').hide();
    $('#host_div').hide();
}

function get_error_solved_process(process_id){
    /**
     * 排错流程
     */
    $('#error_solved').empty();
    $('#error_solved').append('<option value="">无</option>')
    $.ajax({
        type: "POST",
        dataType: "JSON",
        url: "../get_error_solved_process/",
        data: {
            process_id: process_id
        },
        success: function(data){
            var status = data.status;
            if (status == 1){
                var data = eval(data.data)
                for(var i=0; i< data.length; i++){
                    $('#error_solved').append('<option value="' + data[i].id + '">' + data[i].name + '</option>');
                }
            } else {
                alert(data.info)
            }
        }
    })
}

var treedata = "";

function getStepDetail(){
    $.ajax({
        type: "POST",
        dataType: "JSON",
        url: "../get_step_detail/",
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
                $("#time").val(data.time);
                $("#approval option:selected").removeProp("selected");
                $("#skip option:selected").removeProp("selected");
                $("#rto_count_in option:selected").removeProp("selected");
                $("#remark").val(data.remark);
                $("#force_exec").val(data.force_exec);

                var groupInfoList = data.allgroups.split("&");
                for (var i = 0; i < groupInfoList.length - 1; i++) {
                    var singlegroupInfoList = groupInfoList[i].split("+");
                    if (singlegroupInfoList[0] == data.group) {
                        $("#group").append('<option value="' + singlegroupInfoList[0] + '" selected>' + singlegroupInfoList[1] + '</option>')
                    } else {
                        $("#group").append('<option value="' + singlegroupInfoList[0] + '">' + singlegroupInfoList[1] + '</option>')
                    }
                }
                $("#approval").find("option[value='" + data.approval + "']").prop("selected", true);
                $("#skip").find("option[value='" + data.skip + "']").prop("selected", true);
                $("#rto_count_in").find("option[value='" + data.rto_count_in + "']").prop("selected", true);
                var scriptInfoList = data.scripts.split("&");
                for (var i = 0; i < scriptInfoList.length - 1; i++) {
                    var singleScriptInfoList = scriptInfoList[i].split("+");
                    $("#se_1").append('<option value="' + singleScriptInfoList[0] + '">' + singleScriptInfoList[1] + '</option>')
                }
                var verifyItemsList = data.verifyitems.split("&");
                for (var i = 0; i < verifyItemsList.length - 1; i++) {
                    var singleVerifyItemsList = verifyItemsList[i].split("+");
                    $("#se_2").append('<option value="' + singleVerifyItemsList[0] + '">' + singleVerifyItemsList[1] + '</option>')
                }
            }
        }
    });
}

// 定义构造树的函数
function customTree() {
    $.ajax({
        type: "POST",
        url: "../custom_step_tree/",
        data: {
            process: $("#process").val(),
            name: $("#name").val(),
            id: $("#id").val(),
        },
        dataType: "json",
        success: function (data) {
            JSON.stringify(data.treedata);
            treedata = data.treedata;
            $('#tree_2').jstree({
                'core': {
                    "themes": {
                        "responsive": false
                    },
                    "check_callback": true,
                    'data': treedata
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
                                $("#formdiv").show();
                                var inst = jQuery.jstree.reference(data.reference),
                                    obj = inst.get_node(data.reference);
                                $("#se_1").empty();
                                $("#se_2").empty();

                                $("#group").empty();
                                $("#title").text("新建");
                                $("#id").val("0");
                                $("#pid").val(obj.id);
                                $('#remark').val("");
                                $("#time").val("");
                                $("#skip option:selected").removeProp("selected");
                                $("#approval option:selected").removeProp("selected");
                                $("#group option:selected").removeProp("selected");
                                $("#rto_count_in option:selected").removeProp("selected");
                                $("#name").val("");
                                $("#force_exec").val(2);
                                var groupInfoList = obj.data.allgroups.split("&");
                                for (var i = 0; i < groupInfoList.length - 1; i++) {
                                    var singlegroupInfoList = groupInfoList[i].split("+");
                                    $("#group").append('<option value="' + singlegroupInfoList[0] + '">' + singlegroupInfoList[1] + '</option>')
                                }
                            }
                        },
                        "删除": {
                            "label": "删除",
                            "action": function (data) {
                                var inst = jQuery.jstree.reference(data.reference),
                                    obj = inst.get_node(data.reference);
                                if (obj.children.length > 0){
                                    alert("节点下还有其他节点或功能，无法删除。");
                                }else {
                                    if (confirm("确定要删除此节点？删除后不可恢复。")) {
                                        $.ajax({
                                            type: "POST",
                                            url: "../del_step/",
                                            data: {
                                                id: obj.id,
                                                process_id: $("#process option:selected").val(),
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
                                url: "../move_step/",
                                data: {
                                    id: data.node.id,
                                    parent: data.parent,
                                    old_parent: data.old_parent,
                                    position: data.position,
                                    old_position: data.old_position,
                                    process_id: $("#process option:selected").val(),
                                },
                                success: function (data) {
                                    var selectid = $("#id").val();
                                    if (selectid == moveid) {
                                        var res = data.split('^');
                                        $("#pid").val(res[1]);
                                        $("#pname").val(res[0]);
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
                    $("#se_1").empty();
                    $("#se_2").empty();
                    $("#group").empty();
                    $("#title").text(data.node.text);
                    $("#id").val(data.node.id);
                    $("#pid").val(data.node.parent);
                    $("#name").val(data.node.text);
                    if (data.node.parent != "#"){
                        getStepDetail();
                        $("#formdiv").show();
                    } else {
                        $("#formdiv").hide();
                    }
                })
            // context-menu
            $('#se_1').contextmenu({
                target: '#context-menu2',
                onItem: function (context, e) {
                    if ($(e.target).text() == "新增") {
                        hideParamsDiv();
                        $("#script_instance_id").val("0");
                        $("#scriptid").val("0");
                        $("#scriptcode").val("");
                        $("#script_name").val("");
                        $("#script_text").val("");
                        $("#success_text").val("");
                        $("#log_address").val("");
                        $("#host_id").val("");
                        $("#origin").val("");
                        $("#commv_interface").val("");
                        $("#interface_type").val("");
                        $("#sort").val('');
                        $("#error_solved").val('');
                        $('#script_instance_name').val('');
                        $('#script_instance_remark').val('');
                        $('#utils option:first').prop("selected", true);

                        // 隐藏
                        $("#host_id_div").hide();
                        $("#script_text_div").hide();
                        $("#success_text_div").hide();
                        $("#log_address_div").hide();
                        $("#sort_div").hide();
                        $("#origin_div").hide();
                        $("#commv_interface_div").hide();
                        $('#utils_id_div').hide();
                        $('#script_instance_name_div').hide();
                        $('#script_instance_remark_div').hide();
                        $('#sort_div').hide();
                        $('#error_solved_div').hide();

                        document.getElementById("edit").click();
                    }
                    if ($(e.target).text() == "修改") {
                        if ($("#se_1").find('option:selected').length == 0)
                            alert("请选择要修改的脚本。");
                        else {
                            if ($("#se_1").find('option:selected').length > 1)
                                alert("修改时请不要选择多条记录。");
                            else {
                                hideParamsDiv();
                                $.ajax({
                                    type: "POST",
                                    url: "../get_script_data/",
                                    data: {
                                        id: $("#id").val(),
                                        script_instance_id: $("#se_1").find('option:selected').val(),
                                    },
                                    dataType: "json",
                                    success: function (data) {
                                        if (data.status == 1) {
                                            // script
                                            $("#scriptid").val(data.data.script_id);
                                            $("#scriptcode").val(data.data.script_code);
                                            $("#script_name").val(data.data.script_name);
                                            $("#script_text").val(data.data.script_text);
                                            $("#success_text").val(data.data.succeedtext);
                                            $("#interface_type").val(data.data.interface_type);
                                            $("#commv_interface").val(data.data.commv_interface);

                                            // script_instance
                                            $('#script_instance_id').val(data.data.script_instance_id);
                                            $("#sort").val(data.data.script_instance_sort);
                                            $("#error_solved").val(data.data.script_instance_error_solved);
                                            $("#log_address").val(data.data.log_address);
                                            $('#script_instance_name').val(data.data.script_instance_name);
                                            $('#script_instance_remark').val(data.data.script_instance_remark);
                                            // >> Linux/Windows
                                            $("#host_id").val(data.data.host_id);
                                            // >> Commvault
                                            $('#utils').val(data.data.utils_id)
                                            $("#origin").val(data.data.primary_id);
                                            $("#commv_interface").val(data.data.commv_interface);
                                            $('#script_instance_name_div').show();
                                            $('#script_instance_remark_div').show();
                                            $('#sort_div').show();
                                            $('#error_solved_div').show();
                                            // 判断是否为commvault
                                            if (data.data.interface_type == "Commvault") {
                                                $("#host_id_div").hide();
                                                $("#script_text_div").hide();
                                                $("#success_text_div").hide();
                                                $("#log_address_div").hide();
                                                $("#origin_div").show();
                                                $("#commv_interface_div").show();
                                                $('#utils_id_div').show();

                                            } else {
                                                $("#host_id_div").show();
                                                $("#script_text_div").show();
                                                $("#success_text_div").show();
                                                $("#log_address_div").show();
                                                $("#origin_div").hide();
                                                $("#commv_interface_div").hide();
                                                $('#utils_id_div').hide();
                                            }

                                            displayParams(1);
                                            // loadHostsParams();
                                        } else {
                                            alert(data.info)
                                        }
                                    },
                                    error: function (e) {
                                        alert("数据读取失败，请于客服联系。");
                                    }
                                });

                                document.getElementById("edit").click();
                            }
                        }

                    }

                    if ($(e.target).text() == "删除") {
                        if ($("#se_1").find('option:selected').length == 0)
                            alert("请选择要删除的脚本。");
                        else {
                            if (confirm("确定要删除该脚本吗？")) {
                                $.ajax({
                                    type: "POST",
                                    url: "../../remove_script/",
                                    data: {
                                        script_instance_id: $("#se_1").find('option:selected').val(),
                                    },
                                    success: function (data) {
                                        if (data["status"] == 1) {
                                            $("#se_1").find('option:selected').remove();
                                            alert("删除成功！");
                                            $('#tree_2').jstree("destroy");

                                            customTree();
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

                }
            });

            // context-menu for verify
            $('#se_2').contextmenu({
                target: '#context-menu3',
                onItem: function (context, e) {
                    if ($(e.target).text() == "新增") {
                        $("#verify_id").val("0");
                        $("#verify_name").val("");
                        $("#verify_state").val("");

                        document.getElementById("edit").click();
                    }
                    if ($(e.target).text() == "修改") {
                        if ($("#se_2").find('option:selected').length == 0)
                            alert("请选择要修改的确认项。");
                        else {
                            if ($("#se_2").find('option:selected').length > 1)
                                alert("修改时请不要选择多条记录。");
                            else {
                                $.ajax({
                                    type: "POST",
                                    url: "../get_verify_items_data/",
                                    data: {
                                        id: $("#id").val(),
                                        verify_id: $("#se_2").find('option:selected').val(),
                                    },
                                    dataType: "json",
                                    success: function (data) {
                                        $("#verify_id").val(data["id"]);
                                        $("#verify_name").val(data["name"]);
                                    },
                                    error: function (e) {
                                        alert("数据读取失败，请于客服联系。");
                                    }
                                });
                                document.getElementById("edit").click();
                            }
                        }

                    }


                    if ($(e.target).text() == "删除") {
                        if ($("#se_2").find('option:selected').length == 0)
                            alert("请选择要删除的确认项。");
                        else {
                            if (confirm("确定要删除该确认项吗？")) {
                                $.ajax({
                                    type: "POST",
                                    url: "../../remove_verify_item/",
                                    data: {
                                        verify_id: $("#se_2").find('option:selected').val(),
                                    },
                                    success: function (data) {
                                        if (data["status"] == 1) {
                                            $("#se_2").find('option:selected').remove();
                                            alert("删除成功！");
                                            $('#tree_2').jstree("destroy");

                                            customTree();
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

                }
            });
        },
        error: function (e) {
            alert("流程读取失败，请于客服联系。");
        }
    });
}

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

customTree();


$('#sample_1 tbody').on('click', 'button#select', function () {
    var table = $('#sample_1').DataTable();
    var data = table.row($(this).parents('tr')).data();

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

    $("#scriptcode").val(data.code);
    $("#script_name").val(data.name);
    $("#script_text").val(data.script_text);
    $("#success_text").val(data.success_text);
    $("#log_address").val(data.log_address);
    $("#host_id").val(data.host_id);

    // commvault
    $("#interface_type").val(data.interface_type);
    $("#origin").val(data.origin);
    $("#commv_interface").val(data.commv_interface);

    $('#static03').modal('hide');
});

get_error_solved_process($("#process").val());
$("#process").change(function () {
    $("#formdiv").hide();
    $('#tree_2').jstree("destroy");
    customTree();

    // 排错流程
    get_error_solved_process($(this).val());
});


// 脚本
$('#scriptsave').click(function () {
    var config = [];
    // $('#process_div').find('input').each(function () {
    //     config.push({
    //         param_name: $(this).parent().prev().text(),
    //         variable_name: $(this).attr("id"),
    //         param_value: $(this).val(),
    //         type: "PROCESS"
    //     })
    // })
    $('#script_div').find('input').each(function () {
        config.push({
            param_name: $(this).parent().prev().text(),
            variable_name: $(this).attr("id"),
            param_value: $(this).val(),
            type: "SCRIPT"
        })
    })
    // $('#host_div').find('input').each(function () {
    //     config.push({
    //         param_name: $(this).parent().prev().text(),
    //         variable_name: $(this).attr("id"),
    //         param_value: $(this).val(),
    //         type: "HOST"
    //     })
    // })
    $.ajax({
        type: "POST",
        dataType: 'json',
        url: "../../processscriptsave/",
        data: {
            step_id: $("#id").val().replace("demo_node_", ""),
            script_id: $("#scriptid").val(),
            config: JSON.stringify(config),
            interface_type: $('#interface_type').val(),  // 接口类型
            error_solved: $('#error_solved').val(),  // 排错流程
            /**
             * 接口实例名称
             * 选择工具
             * 选择客户端
             * 选择主机
             * 填写类名
             * 日志地址
             * 接口实例说明
             */
            script_instance_id: $('#script_instance_id').val(),
            script_instance_name: $('#script_instance_name').val(),
            utils: $('#utils').val(),
            host_id: $('#host_id').val(),
            origin: $('#origin').val(),
            commv_interface: $('#commv_interface').val(),
            log_address: $('#log_address').val(),
            sort: $('#sort').val(),
            script_instance_remark: $('#script_instance_remark').val()
        },
        success: function (data) {
            alert(data["info"]);
            $('#script_instance_id').val(data.id); // 新增后修改
            var mydata = eval(data.data);
            if (data["status"] == 1) {
                /*
                    加载所有脚本，重新排序
                 */
                $("#se_1").empty();
                for (var i = 0; i < mydata.length; i++) {
                    $("#se_1").append("<option value='" + mydata[i].id + "'>" + mydata[i].name + "</option>");
                }

                $('#static01').modal('hide');
                // 重新构造树，停留当前修改脚本的步骤位置
                $('#tree_2').jstree("destroy");
                customTree();
            }
        },
        error: function (e) {
            alert("请保存当前步骤后，再添加关联脚本。");
        }
    });
})


// 确认项
$('#verify_items_save').click(function () {
    $.ajax({
        type: "POST",
        dataType: 'json',
        url: "../../verify_items_save/",
        data: {
            processid: $("#process option:selected").val(),
            id: $("#verify_id").val(),
            name: $("#verify_name").val(),
            step_id: $("#id").val(),
        },
        success: function (data) {
            var myres = data["res"];
            var mydata = data["data"];
            if (myres == "新增成功。") {
                $("#verify_id").val(data["data"]);
                $("#se_2").append("<option value='" + mydata + "'>" + $("#verify_name").val() + "</option>");
                $('#static02').modal('hide');
                $('#tree_2').jstree("destroy");
                customTree();
            }
            if (myres == "修改成功。") {
                var verify_id = $("#verify_id").val();
                $("#se_2").find('option[value="verify_id"]'.replace("verify_id", verify_id)).text($("#verify_name").val());
                $('#static02').modal('hide');
                $('#tree_2').jstree("destroy");
                customTree();
            }
            alert(myres);
        },
        error: function (e) {
            alert("请保存当前步骤后，再添加关联确认项。");
        }
    });
});


$('#save').click(function () {
    $.ajax({
        type: "POST",
        url: "../setpsave/",
        data: {
            id: $("#id").val(),
            pid: $("#pid").val(),
            name: $("#name").val(),
            time: $("#time").val(),
            skip: $("#skip").val(),
            approval: $("#approval").val(),
            group: $("#group").val(),
            rto_count_in: $("#rto_count_in").val(),
            new: $("#new").val(),
            process_id: $("#process option:selected").val(),
            remark: $("#remark").val(),
            force_exec: $("#force_exec").val()
        },
        success: function (data) {
            if (data["result"] != "保存成功。") {
                alert(data["result"])
            } else {
                alert("保存成功！");

                if ($("#id").val() == "0") {
                    $('#tree_2').jstree('create_node', $("#pid").val(), {
                        "text": $("#name").val(),
                        "id": data.data,
                    }, "last", false, false);

                    $("#id").val(data.data);
                    $('#tree_2').jstree('deselect_all');
                    $('#tree_2').jstree('select_node', $("#id").val(), true);
                }
                else {
                    var curnode = $('#tree_2').jstree('get_node', $("#id").val());
                    var name = $('#name').val();
                    var newtext = curnode.text.replace(curnode.text, name);
                    curnode.text = newtext
                    $('#tree_2').jstree('set_text', $("#id").val(), newtext);
                    $('#title').text(newtext);
                }
            }
        },
        error: function (e) {
            alert("保存失败，请于客服联系。");
        }
    });
});
