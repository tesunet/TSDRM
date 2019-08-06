$(function () {
    var treeData = [];
    $.ajax({
        type: "POST",
        url: "../get_contact_tree/",
        data: {},
        success: function (data) {
            treeData = data.data;
            customContactTree();
            $('#contact_tb').dataTable({
                "bAutoWidth": true,
                "bSort": false,
                "bProcessing": true,
                "ajax": "../get_contact_info/?user_id=0",
                "columns": [
                    {"data": "user_name"},
                    {"data": "tel"},
                    {"data": "email"},
                    {"data": "depart"},
                ],
                "columnDefs": [],
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
        },
        error: function (e) {
            alert("修改密码失败，请于管理员联系。");
        }
    });


    function customContactTree() {
        $('#tree_contact').jstree({
            'core': {
                "themes": {
                    "responsive": false
                },
                "check_callback": true,
                'data': treeData,
            },
            "types": {
                "org": {
                    "icon": "fa fa-folder icon-state-warning icon-lg"
                },
                "user": {
                    "icon": "fa fa-user icon-state-warning icon-lg"
                }
            },
            "plugins": ["types", "role"]
        })
            .on('loaded.jstree', function (e, data) {
                var inst = data.instance;
                var obj = inst.get_node(e.target.firstChild.firstChild.lastChild);

                inst.select_node(obj);
            })
            .bind('select_node.jstree', function (event, data) {
                $("#contact_div").show();
                $("#title").text(data.node.text);

                var curNodeId = data.node.id;
                if (data.node.parent == "#") {
                    curNodeId = 0;
                }
                var table = $('#contact_tb').DataTable();
                table.ajax.url("../get_contact_info/?user_id=" + curNodeId).load();
            });
    }
});