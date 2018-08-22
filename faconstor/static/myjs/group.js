$('#se_1').contextmenu({
    target: '#context-menu2',
    onItem: function (context, e) {
        if ($(e.target).text() == "新增") {
            $("#editgroup").show()
            $("#user").hide()
            $("#id").val("0")
            $("#name").val("")
            $("#remark").val("")
            $("#title").text("新建")
        }

        if ($(e.target).text() == "删除") {
            if ($("#se_1").find('option:selected').length == 0)
                alert("请选择要删除的角色。");
            else {
                if (confirm("错误删除角色典可能引起流程瘫痪，确定要删除该角色吗？")) {
                    $.ajax({
                        type: "POST",
                        url: "../groupdel/",
                        data:
                            {
                                id: $("#se_1").find('option:selected').attr("id"),
                            },
                        success: function (data) {
                            if (data == "删除成功。") {
                                $("#se_1").find('option:selected').remove();
                                $("#user").hide()
                                $("#id").val("0")
                                $("#name").val("")
                                $("#remark").val("")
                                $("#title").text("")
                            }
                            alert(data);
                        },
                        error: function (e) {
                            alert("页面出现错误，请于管理员联系。");
                        }
                    });
                }
            }
        }

    }
});
$('#se_1').change(function () {
    $("#editgroup").show()
    $("#user").show()
    $("#id").val($("#se_1").find('option:selected').attr('id'))
    $("#name").val($("#se_1").find('option:selected').text())
    $("#remark").val($("#se_1").find('option:selected').attr('remark'))
    $("#title").text($("#se_1").find('option:selected').text())
});

$('#save').click(function () {
    $.ajax({
        type: "POST",
        dataType: 'json',
        url: "../groupsave/",
        data:
            {
                id: $("#id").val(),
                name: $("#name").val(),
                remark: $("#remark").val(),
            },
        success: function (data) {
            var myres = data["res"];
            var mydata = data["data"];
            if (myres == "新增成功。") {
                $("#id").val(data["data"])
                $("#se_1").append("<option selected id='" + mydata + "' remark='" + $("#remark").val() + "'>" + $("#name").val() + "</option>");
                $("#title").text($("#name").val())
            }
            if (myres == "修改成功。") {
                $("#" + $("#id").val()).text($("#name").val())
                $("#" + $("#id").val()).attr('remark', $("#remark").val())
                $("#user").show()

            }
            alert(myres);
        },
        error: function (e) {
            alert("页面出现错误，请于管理员联系。");
        }
    });
});

$('#user').click(function () {
    $("#my_multi_select1").empty();
    $.ajax({
        type: "POST",
        dataType: 'json',
        url: "../getusers/",
        data:
            {
                id: $("#id").val(),
            },
        success: function (data) {
            for (var i = 0; i < data.data.user_list.length; i++) {
                $("#my_multi_select1").append("<option value='" + data.data.user_list[i].userid + "'>" + data.data.user_list[i].username + "</option>");
            }
            for (var i = 0; i < data.data.selected_user_list.length; i++) {
                try {
                    $("#my_multi_select1 option[value='" + data.data.selected_user_list[i].userid + "']").prop("selected", true);
                } catch (err) {}
            }
            $('#my_multi_select1').multiSelect('refresh');
        },
        error: function (e) {
            alert("页面出现错误，请于管理员联系。");
        }
    });
});

$('#saveuser').click(function () {
    var selecteduser = "";
    $("#my_multi_select1").find("option:selected").each(function () {
            var txt = $(this).val();
            selecteduser = selecteduser + txt + "*!-!*"
        }
    );
    $.ajax({
        type: "POST",
        url: "../groupsaveuser/",
        data:
            {
                id: $("#id").val(),
                selecteduser: selecteduser,
            },
        success: function (data) {
            $('#static1').modal('hide');
            alert(data);
        },
        error: function (e) {

            alert("页面出现错误，请于管理员联系。");
        }
    });
});

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




