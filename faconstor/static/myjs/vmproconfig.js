    $(document).ready(function() {
        $('#sample_1').dataTable({
            "bAutoWidth": true,
            "bSort": false,
            "bProcessing": true,
            "ajax": "../vmproconfigdata/",
            "columns": [
                { "data": "appGroup" },
                { "data": "clientName" },
                { "data": "platform" },
                { "data": "status" },

            ],

            "columnDefs": [{
                "targets": 1,
                "mRender": function(data, type, full) {
                    return "<a id='editclent'  data-toggle='modal'  data-target='#static'>" + data + "</a>"
                }
            }, {
                "targets": 0,
                "mRender": function(data, type, full) {
                    return "<a id='editapp'  data-toggle='modal'  data-target='#static1'>" + data + "</a>"
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
        // 行按钮
        $('#sample_1 tbody').on('click', 'a#editclent', function() {
            var table = $('#sample_1').DataTable();
            $("#myclientGUID").empty();

            var data = table.row($(this).parents('tr')).data();
            $("#clientGUID").val(data.clientGUID);
            $("#clientName").val(data.clientName);
            $("#username").val(data.username);
            $("#hostname").val(data.hostname);
            $('#password').val("")
            $('#del').show()
            $("#pyhhost").select2("val", "");
            for (var i = 0; i < data.proxylist.length; i++) {
                $("#pyhhost").find("option[value='" + data.proxylist[i].clientGUID + "']").remove();
                $("#pyhhost").append("<option selected value='" + data.proxylist[i].clientGUID + "'>" + data.proxylist[i].clientName + "</option>");
            }
            $(".select2, .select2-multiple").select2({
                width: null
            });
        });

        $('#sample_1 tbody').on('click', 'a#editapp', function() {
            var table = $('#sample_1').DataTable();
            var data = table.row($(this).parents('tr')).data();
            for (var i = 0; i < table.context[0].aoData.length; i++) {
                drclientGUID = table.context[0].aoData[i]._aData.clientGUID
                clientName = table.context[0].aoData[i]._aData.clientName
                drclientGUIDlist = $("#myclientGUID").find("option[value='" + drclientGUID + "']")
                if (drclientGUIDlist.length <= 0)
                    $("#myclientGUID").append("<option value='" + drclientGUID + "'>" + clientName + "</option>");
            }
            $("#dataSetGUID").val(data.dataSetGUID);
            $("#appGroup").val(data.appGroup);
            $("#myclientGUID").val(data.clientGUID);
            $("#my_multi_select1").empty();
            var selectedvm = data.backupContent;
            $.ajax({
                type: "POST",
                url: "../getvmlist/",
                data: {
                    clientGUID: $("#myclientGUID").val()
                },
                dataType: "json",
                success: function(data) {
                    for (var i = 0; i < data.length; i++) {
                        $("#my_multi_select1").append("<option value='" + data[i]["vmid"] + "'>" + data[i]["vmname"] + "</option>");

                    }
                    for (var i = 0; i < selectedvm.length; i++) {
                        try {
                            $("#my_multi_select1 option[value='" + selectedvm[i] + "']").prop("selected", true);
                        } catch (err) {}
                    }

                    $('#my_multi_select1').multiSelect('refresh');
                },
            });

            $('#password').val("")

            $("#schdule").val(data.schdule);
            $("#storage").val(data.storage);
            $('#del2').show()

        });

        $('#newclent').click(function() {
            $('#password').val("")
            $("#clientGUID").val("0");
            $("#clientName").val("");
            $("#username").val("");
            $("#hostname").val("");
            $("#mypassword").val("");
            $("#pyhhost").select2("val", "");
            $('#del').hide()
        })

        $('#newapp').click(function() {
            $("#myclientGUID").empty();
            var table = $('#sample_1').DataTable();
            for (var i = 0; i < table.context[0].aoData.length; i++) {
                drclientGUID = table.context[0].aoData[i]._aData.clientGUID
                clientName = table.context[0].aoData[i]._aData.clientName
                drclientGUIDlist = $("#myclientGUID").find("option[value='" + drclientGUID + "']")
                if (drclientGUIDlist.length <= 0)
                    $("#myclientGUID").append("<option value='" + drclientGUID + "'>" + clientName + "</option>");
            }
            $('#password').val("")
            $("#dataSetGUID").val("0");
            $("#appGroup").val("");
            $("#backupContent").val("");
            $("#myclientGUID").val("");
            $("#schdule").val("");
            $("#storage").val("");
            $("#my_multi_select1").empty();
            $('#my_multi_select1').multiSelect('refresh');
            $('#del2').hide()
        })
        $('#myclientGUID').change(function() {
            $.ajax({
                type: "POST",
                url: "../getvmlist/",
                data: {
                    clientGUID: $("#myclientGUID").val()
                },
                dataType: "json",
                success: function(data) {
                    for (var i = 0; i < data.length; i++) {
                        $("#my_multi_select1").append("<option value='" + data[i]["vmid"] + "'>" + data[i]["vmname"] + "</option>");

                    }
                    $('#my_multi_select1').multiSelect('refresh');
                },
            });
        })



        $('#save1').click(function() {
            var table = $('#sample_1').DataTable();
            if ($('#mypassword').val() != $('#repassword').val())
                alert("两次密码输入不一致。");
            else {
                if ($('#password').val() == "")
                    alert("保存前请输入密码。");
                else {
                    var pyhhostlist = ""
                    $("#pyhhost").find("option:selected").each(function() {
                        var txt = $(this).val();
                        pyhhostlist = pyhhostlist + txt + "*!-!*"
                    });
                    $.ajax({
                        type: "POST",
                        url: "../vmproconfigsave/",
                        data: {

                            password: $('#password').val(),
                            mypassword: $('#mypassword').val(),
                            clientName: $('#clientName').val(),
                            clientGUID: $('#clientGUID').val(),
                            username: $("#username").val(),
                            hostname: $("#hostname").val(),
                            pyhhostlist: pyhhostlist,

                        },
                        success: function(data) {
                            alert(data);
                            if (data == "保存成功。") {
                                $('#static').modal('hide');
                                table.ajax.reload();
                            }
                        },
                        error: function(e) {
                            alert("保存失败，请于客服联系。");
                        }
                    });
                }
            }
        })
        $('#save2').click(function() {

            var table = $('#sample_1').DataTable();
            if ($('#password2').val() == "")
                alert("保存前请输入密码。");
            else {
                var backupContent = ""
                $("#my_multi_select1").find("option:selected").each(function() {
                    var txt = $(this).val();
                    backupContent = backupContent + txt + "*!-!*"
                });

                $.ajax({
                    type: "POST",
                    url: "../vmappsave/",
                    data: {

                        password: $('#password2').val(),
                        dataSetGUID: $('#dataSetGUID').val(),
                        appGroup: $('#appGroup').val(),
                        backupContent: backupContent,
                        schdule: $("#schdule").val(),
                        storage: $("#storage").val(),
                        myclientGUID: $("#myclientGUID").val(),

                    },
                    success: function(data) {
                        alert(data);
                        if (data == "保存成功。") {
                            $('#static1').modal('hide');
                            table.ajax.reload();
                        }
                    },
                    error: function(e) {
                        alert("保存失败，请于客服联系。");
                    }
                });
            }
        })
        $('#del').click(function() {
            var table = $('#sample_1').DataTable();
            if ($('#password').val() == "")
                alert("删除前请输入密码。");
            else {
                $.ajax({
                    type: "POST",
                    url: "../vmproconfigdel/",
                    data: {

                        password: $('#password').val(),
                        clientGUID: $('#clientGUID').val(),
                    },
                    success: function(data) {
                        alert(data);
                        if (data == "删除成功。") {
                            $('#static').modal('hide');
                            table.ajax.reload();
                        }
                    },
                    error: function(e) {
                        alert("删除失败，请于客服联系。");
                    }
                });
            }
        })
        $('#del2').click(function() {
            var table = $('#sample_1').DataTable();
            if ($('#password2').val() == "")
                alert("删除前请输入密码。");
            else {
                $.ajax({
                    type: "POST",
                    url: "../vmappdel/",
                    data: {

                        password: $('#password2').val(),
                        dataSetGUID: $('#dataSetGUID').val(),


                    },
                    success: function(data) {
                        alert(data);
                        if (data == "删除成功。") {
                            $('#static1').modal('hide');
                            table.ajax.reload();
                        }
                    },
                    error: function(e) {
                        alert("删除失败，请于客服联系。");
                    }
                });
            }
        })

        $('#my_multi_select1').multiSelect({
            selectableHeader: "<input type='text' class='search-input' autocomplete='off' placeholder='未选择'>",
            selectionHeader: "<input type='text' class='search-input' autocomplete='off' placeholder='已选择'>",
            afterInit: function(ms) {
                var that = this,
                    $selectableSearch = that.$selectableUl.prev(),
                    $selectionSearch = that.$selectionUl.prev(),
                    selectableSearchString = '#' + that.$container.attr('id') + ' .ms-elem-selectable:not(.ms-selected)',
                    selectionSearchString = '#' + that.$container.attr('id') + ' .ms-elem-selection.ms-selected';

                that.qs1 = $selectableSearch.quicksearch(selectableSearchString)
                    .on('keydown', function(e) {
                        if (e.which === 40) {
                            that.$selectableUl.focus();
                            return false;
                        }
                    });

                that.qs2 = $selectionSearch.quicksearch(selectionSearchString)
                    .on('keydown', function(e) {
                        if (e.which == 40) {
                            that.$selectionUl.focus();
                            return false;
                        }
                    });
            },
            afterSelect: function() {
                this.qs1.cache();
                this.qs2.cache();
            },
            afterDeselect: function() {
                this.qs1.cache();
                this.qs2.cache();
            }
        });

    });