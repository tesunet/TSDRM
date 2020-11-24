$(document).ready(function () {
    function customProcessDataTable() {
        $('#sample_1').dataTable({
            "bAutoWidth": true,
            "bSort": false,
            "bProcessing": true,
            "ajax": "../walkthroughdata/",
            "fnServerParams": function (aoData) {
                aoData.push({
                    name: "process_id",
                    value: $("#process_id").val()
                })
            },
            "columns": [
                { "data": "walkthrough_id" },
                { "data": "walkthrough_name" },
                { "data": "createuser" },
                { "data": "createtime" },
                { "data": "state" },
                { "data": "purpose" },
                { "data": "starttime" },
                { "data": "endtime" },
                { "data": "processes" },
                { "data": null },
            ],
            "columnDefs": [{
                "targets": 1,
                "render": function (data, type, full) {
                    return "<td><a href='walkthrough_url' target='_blank'>data</a></td>".replace("data", full.walkthrough_name).replace("walkthrough_url", "/walkthroughindex/" + full.walkthrough_id + "?s=true")
                }
            }, {
                "visible": false,
                "targets": -2  // 倒数第一列
            }, {
                "targets": -1,  // 指定最后一列添加按钮；
                "data": null,
                "width": "120px",  // 指定列宽；
                "render": function (data, type, full) {
                    var cat_button = ""
                    if (full.state == "已完成" || full.state == "终止") {
                        cat_button = "<button class='btn btn-xs btn-primary' type='button' data-toggle='modal' data-target='#static02' title='查看' id='cat'><i class='fa fa-eye' style='color: white'></i></a></button>"
                    } else {
                        cat_button = "<button class='btn btn-xs btn-primary' type='button' data-toggle='modal' data-target='#static02' title='查看' id='cat' disabled><i class='fa fa-eye' style='color: white'></i></a></button>"
                        if (full.state == "执行中"){
                            cat_button = "<button class='btn btn-xs btn-primary' type='button' data-toggle='modal' data-target='#static02' title='查看' id='cat' disabled><i class='fa fa-eye' style='color: white'></i></a></button><button title='终止'  id='stop_walkthrough' class='btn btn-xs btn-danger' type='button'><i class='fa fa-power-off'></i></button>"
                        }
                    }
                    return "<td><button  id='edit' title='编辑' data-toggle='modal'  data-target='#static01'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button>" + cat_button + "<button title='删除'  id='delrow' class='btn btn-xs btn-primary' type='button'><i class='fa fa-trash-o'></i></button></td>"
                    // return "<td><button  id='edit' title='编辑' data-toggle='modal'  data-target='#static01'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button><button class='btn btn-xs btn-primary' type='button'><a href='/custom_pdf_report/?processrunid&processid'><i class='fa fa-arrow-circle-down' style='color: white'></i></a></button><button title='删除'  id='delrow' class='btn btn-xs btn-primary' type='button'><i class='fa fa-trash-o'></i></button></td>".replace("processrunid", "processrunid=" + full.processrun_id).replace("processid", "processid=" + full.process_id)
                }
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

        $('#sample_1 tbody').on('click', 'button#delrow', function () {
            if (confirm("确定要删除该条数据？")) {
                var table = $('#sample_1').DataTable();
                var data = table.row($(this).parents('tr')).data();
                $.ajax({
                    type: "POST",
                    url: "../../walkthroughdel/",
                    data:
                    {
                        id: data.walkthrough_id
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
        $('#sample_1 tbody').on('click', 'button#cat', function () {
            var table = $('#sample_1').DataTable();
            var data = table.row($(this).parents('tr')).data();
            var walkthrough_id = data.walkthrough_id;
            $.ajax({
                type: "POST",
                url: "../../get_walkthrough_info/",
                data:
                {
                    walkthrough_id: walkthrough_id
                },
                success: function (data) {
                    $("table#process_data tbody").empty();
                    $("table#group_data tbody").empty();

                    $("#current_process").text(data.all_process_name);
                    $("#summary").text("为了提高防范灾难风险的能力，保证业务连续性要求，在公司总经理室高度重视下，太平资产成立灾备演练项目组，于time进行核心系统灾备演练，并取得圆满成功。演练具体情况报告如下。".replace("time", data.walkthrough_starttime));
                    $("#note").text(data.purpose);

                    var elements = "";
                    for (var k = 0; k < data.process_info_list.length; k++) {
                        var step_info_list = data.process_info_list[k].step_info_list;

                        elements += '<tr><td rowspan="' + (data.process_info_list[k].process_length + 1) + '"><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + data.process_info_list[k].process_name + '</font></font></td>';
                        for (var i = 0; i < step_info_list.length; i++) {
                            // wrapper_step
                            var stepWrapper = step_info_list[i];
                            var innerStep = stepWrapper.inner_step_list;
                            if (innerStep != "" && innerStep != null) {
                                var innerStepLength = innerStep.length;
                                var rowSpanString = ' rowspan="' + innerStepLength + '"';
                            } else {
                                rowSpanString = "";
                            }

                            if (stepWrapper.operator) {
                                var stepWrapperOperator = stepWrapper.operator
                            } else {
                                var stepWrapperOperator = ""
                            }
                            elements += '<td' + rowSpanString + '><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">*' + stepWrapper.step_name + '</font></font></td>';
                            // inner_step
                            if (innerStep != "" && innerStep != null) {
                                for (var j = 0; j < innerStep.length; j++) {
                                    if (innerStep[j].operator) {
                                        var stepInnerOperator = innerStep[j].operator
                                    } else {
                                        var stepInnerOperator = ""
                                    }


                                    elements += '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">**' + innerStep[j].step_name + '</font></font></td>' +
                                        '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + stepInnerOperator + '</font></font></td>' +
                                        '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + innerStep[j].start_time + '</font></font></td>' +
                                        '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + innerStep[j].end_time + '</font></font></td>' +
                                        '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + innerStep[j].rto + '</font></font></td></tr>'
                                }
                            } else {
                                var cur_starttime = "", cur_endtime = "", cur_rto = "";
                                if (stepWrapper.start_time) {
                                    cur_starttime = stepWrapper.start_time;
                                } else {
                                    cur_starttime = ""
                                }
                                if (stepWrapper.end_time) {
                                    cur_endtime = stepWrapper.end_time;
                                } else {
                                    cur_endtime = "";
                                }
                                if (stepWrapper.rto) {
                                    cur_rto = stepWrapper.rto;
                                } else {
                                    cur_rto = "";
                                }
                                elements += '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;"></font></font></td>' +
                                    '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + stepWrapperOperator + '</font></font></td>' +
                                    '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + cur_starttime + '</font></font></td>' +
                                    '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + cur_endtime + '</font></font></td>' +
                                    '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + cur_rto + '</font></font></td></tr>'
                            }
                        }
                        var process_start_time = "", process_end_time = "", process_rto = "";
                        try {
                            process_start_time = data.process_info_list[k].start_time;
                            process_end_time = data.process_info_list[k].end_time;
                            process_rto = data.process_info_list[k].rto;

                        }
                        catch (err) {
                            //..
                        }


                        elements += '<tr><td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;"><font color="#ff0000">*</font>总环节</font></font></td>';
                        elements += '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;"></font></font></td>' +
                            '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;"></font></font></td>' +
                            '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + process_start_time + '</font></font></td>' +
                            '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + process_end_time + '</font></font></td>' +
                            '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + process_rto + '</font></font></td></tr>';
                    }
                    // 添加流程总RTO


                    $("table#process_data tbody").append(elements);

                    var groupElements = "";
                    for (var i = 0; i < data.total_list.length; i++) {
                        var currentGroup = data.total_list[i];
                        var userList = currentGroup.current_users_and_departments;
                        if (userList != "" && userList != null) {
                            var userListLength = userList.length;
                            var rowSpanString01 = ' rowspan="' + userListLength + '"';
                        } else {
                            rowSpanString01 = "";
                        }
                        groupElements += '<tr><td' + rowSpanString01 + '><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + currentGroup.group + '</font></font></td>';
                        if (userList != "" && userList != null) {
                            for (var j = 0; j < userList.length; j++) {
                                groupElements += '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + userList[j].fullname + '</font></font></td>' +
                                    '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">' + userList[j].depart_name + '</font></font></td></tr>'
                            }
                        } else {
                            groupElements += '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;"></font></font></td>' +
                                '<td><font style="vertical-align: inherit;"><font style="vertical-align: inherit;"></font></font></td></tr>'
                        }
                    }
                    $("table#group_data tbody").append(groupElements);

                    // 下载链接
                    $("a#download").attr("href", "/walkthrough_pdf/?walkthrough_id=" + walkthrough_id)
                },
            });
        });
        $('#sample_1 tbody').on('click', 'button#stop_walkthrough', function () {
            if (confirm("是否终止本次演练?")){
                var table = $('#sample_1').DataTable();
                var data = table.row($(this).parents('tr')).data();
                var walkthrough_id = data.walkthrough_id;
                $.ajax({
                    type: "POST",
                    url: "../../stop_walkthrough/",
                    data:
                    {
                        walkthrough_id: walkthrough_id
                    },
                    success: function (data) {
                        var status = data.status,
                            info = data.info;
                        if (status=="1"){
                            table.ajax.reload();
                        }
                        alert(info)
                    },
                });
            }
        });
    }

    customProcessDataTable();

    $("#plan").click(function () {
        $("#static01").modal({ backdrop: "static" });
        $("#generate").hide();
        $("#run_invited").hide();
        $("#reject_invited").hide();
        $("#id").val("0");
        $("#name").val("");
        $("#start_date").val("");
        $("#end_date").val("");
        $("#purpose").val("");
        $("#my_multi_select1 option").each(function () {
            $(this).prop("selected", false);
        });
        $('#my_multi_select1').multiSelect('refresh');
    });

    // 保存邀请函
    $("#save").click(function () {
        var id = $("#id").val();
        var table = $('#sample_1').DataTable();
        var processes = ""

        var selectArray = []
        $("#ms-my_multi_select1").find(".ms-elem-selection.ms-selected").each(function () {
            selectArray.push($(this).children('span').text())
        });
        for (selectText of selectArray) {
            $("select#my_multi_select1").find("option").each(function () {
                if ($(this).text() == selectText) {
                    processes = processes + $(this).val() + "*!-!*"
                }
            });
        }

        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../walkthroughsave/",
            data:
            {
                id: id,
                name: $("#name").val(),
                start_time: $("#start_date").val(),
                end_time: $("#end_date").val(),
                purpose: $("#purpose").val(),
                processes: processes,
            },
            success: function (data) {
                if (data["res"] == "演练计划保存成功，待开启流程。") {
                    $("#generate").show();
                    $("#run_invited").show();
                    $("#reject_invited").show();
                    $("#id").val(data["data"]);
                    table.ajax.reload();
                    alert(data["res"]);
                }
                else
                    alert(data["res"]);
            }
        });
    });

    $('#sample_1 tbody').on('click', 'button#edit', function () {
        var table = $('#sample_1').DataTable();
        var data = table.row($(this).parents('tr')).data();
        $("#generate").show();
        $("#run_invited").show();
        $("#reject_invited").show();
        $("#id").val(data.walkthrough_id);
        $("#name").val(data.walkthrough_name);
        $("#start_date").val(data.starttime);
        $("#end_date").val(data.endtime);
        $("#purpose").val(data.purpose);
        $("#my_multi_select1 option").each(function () {
            $(this).prop("selected", false);
        });
        var processes = data.processes
        var myprocess = processes.split('^')
        for (i = 0; i < myprocess.length; i++) {
            $("#my_multi_select1 option[value='" + myprocess[i] + "']").prop("selected", true);
        }
        $('#my_multi_select1').multiSelect('refresh');

        // 右侧选中的排序
        var sortedProcesses = data.process_name_list;
        var j=0;
        for (sortedProcess of sortedProcesses) {
            $(".ms-selection").find(".ms-elem-selection.ms-selected").each(function () {
                // var curNode = "";
                if (sortedProcess.trim()==$(this).children("span").text().trim()){
                    $(this).insertBefore($(this).parent().find("li:eq(" + j + ")"));
                }
            });
            j++;
        }
    });

    // 取消计划流程
    $("#reject_invited").click(function () {
        var id = $("#id").val();
        if (confirm("是否取消当前流程计划？")) {
            $.ajax({
                type: "POST",
                dataType: 'json',
                url: "../reject_walkthrough/",
                data:
                {
                    id: id,
                },
                success: function (data) {
                    alert(data["res"]);
                    if (data['res'] === "取消演练计划成功！") {
                        // 关闭模态框刷新表格
                        window.location.reload();
                    }
                }
            });
        }
    });

    $("#confirm").click(function () {
        var process_id = $("#process_id").val();

        // 非邀请流程启动
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../falconstorrun/",
            data:
            {
                processid: process_id,
                run_person: $("#run_person").val(),
                run_time: $("#run_time").val(),
                run_reason: $("#run_reason").val(),
            },
            success: function (data) {
                if (data["res"] == "新增成功。") {
                    window.location.href = data["data"];
                }
                else
                    alert(data["res"]);
            },
            error: function (e) {
                alert("流程启动失败，请于管理员联系。");
            }
        });
    });

    $("#confirm_invited").click(function () {
        var process_id = $("#process_id").val();
        var plan_process_run_id = $("#plan_process_run_id").val();
        // 需邀请流程启动
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../falconstor_run_invited/",
            data:
            {
                processid: process_id,
                plan_process_run_id: plan_process_run_id,
                run_person: $("#runperson").val(),
                run_time: $("#runtime").val(),
                run_reason: $("#runreason").val(),
            },
            success: function (data) {
                if (data["res"] == "新增成功。") {
                    window.location.href = data["data"];
                }
                else
                    alert(data["res"]);
            },
            error: function (e) {
                alert("流程启动失败，请于管理员联系。");
            }
        });
    });


    $("#run_invited").click(function () {
        $("#static02").modal({ backdrop: "static" });
        // 写入当前时间
        var myDate = new Date();
        $("#runtime").val(myDate.toLocaleString());
    });


    $("#generate").click(function () {
        var walkthrough_id = $("#id").val();
        var start_date = $("#start_date").val();
        var end_date = $("#end_date").val();
        var purpose = $("#purpose").val();
        if (start_date == "" || start_date == null) {
            alert("演练开始时间！");
        } else if (end_date == "" || end_date == null) {
            alert("演练结束时间！");
        } else {
            window.open('/invite/?walkthrough_id=' + walkthrough_id + '&start_date=' + start_date + '&end_date=' + end_date + '&purpose=' + purpose);
        }
    });

    $('#start_date').datetimepicker({
        autoclose: true,
        format: 'yyyy-mm-dd hh:ii',
    });
    $('#end_date').datetimepicker({
        autoclose: true,
        format: 'yyyy-mm-dd hh:ii',
    });

    // 保存邀请函
    $("#save_invitation").click(function () {
        var process_id = $("#process_id").val();
        var plan_process_run_id = $("#plan_process_run_id").val();
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../save_invitation/",
            data:
            {
                process_id: process_id,
                plan_process_run_id: plan_process_run_id,
                start_time: $("#start_date").val(),
                end_time: $("#end_date").val(),
                purpose: $("#purpose").val(),
            },
            success: function (data) {
                if (data["res"] == "流程计划成功，待开启流程。") {
                    $("#save_div").hide();
                    $("#download_div").show();
                    $("#plan_process_run_id").val(data["data"]);
                    $("#static01").modal("hide");
                    // $("#sample_1").DataTable().destroy();
                    // customProcessDataTable();
                    window.location.href = "/"
                }
                else
                    alert(data["res"]);
            }
        });
    });




    // 修改计划流程
    $("#modify_invited").click(function () {
        $("#static03").modal({ backdrop: "static" });
        $('#start_date_modify').datetimepicker({
            autoclose: true,
            format: 'yyyy-mm-dd hh:ii',
        });
        $('#end_date_modify').datetimepicker({
            autoclose: true,
            format: 'yyyy-mm-dd hh:ii',
        });
    });

    // 保存修改计划流程
    $("#save_modify_invitation").click(function () {
        var plan_process_run_id = $("#plan_process_run_id").val();
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: "../save_modify_invitation/",
            data:
            {
                plan_process_run_id: plan_process_run_id,
                start_date_modify: $("#start_date_modify").val(),
                end_date_modify: $("#end_date_modify").val(),
                purpose_modify: $("#purpose_modify").val(),
            },
            success: function (data) {
                if (data["res"] == "修改流程计划成功，待开启流程。") {
                    $("#save_div").hide();
                    $("#download_div").show();
                    $("#plan_process_run_id").val(data["data"]);
                    $("#static03").modal("hide");
                    $("#static01").modal("hide");
                }
                else
                    alert(data["res"]);
            }
        });
        $("#sample_1").DataTable().destroy();
        customProcessDataTable();
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
        },
        keepOrder: true
    });

});
