    $(document).ready(function() {
        $('#sample_1').dataTable( {
            "bAutoWidth": true,
            "bSort": false,
            "bProcessing": true,
            "ajax": "../../filerecoverydata?clientName=" + $('#sourceClient').val(),
            "columns": [
                { "data": "jobId" },
                { "data": "jobType" },
                { "data": "Level" },
                { "data": "StartTime" },
                { "data": "LastTime" },
                { "data": null },
            ],

            "columnDefs": [{
                    "targets": -1,
                    "data": null,
                    "defaultContent": "<button  id='select' title='选择'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-check'></i></button>"
            } ],

            "oLanguage": {
            "sLengthMenu": "&nbsp;&nbsp;每页显示 _MENU_ 条记录",
            "sZeroRecords": "抱歉， 没有找到",
            "sInfo": "从 _START_ 到 _END_ /共 _TOTAL_ 条数据",
            "sInfoEmpty":'',
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
            } );
        $('#sample_1 tbody').on( 'click', 'button#select', function () {
            var table = $('#sample_1').DataTable();
            var data = table.row( $(this).parents('tr') ).data();
            $("#datetimepicker").val( data.LastTime);
            $("input[name='optionsRadios'][value='1']").prop("checked",false);
            $("input[name='optionsRadios'][value='2']").prop("checked",true);
        });
        $('#datetimepicker').datetimepicker({
            format:'yyyy-mm-dd hh:ii:ss',
            });
        $('#recovery').click(function(){

            if ($("input[name='optionsRadios']:checked").val()=="2" && $('#datetimepicker').val()=="")
                alert("请输入时间。");
            else{
                if($('#destClient').val()=="")
                    alert("请选择目标客户端。");
                else
                {
                    if ($("input[name='path']:checked").val()=="2" && $('#mypath').val()=="")
                        alert("请输入指定路径。");
                    else{
                        var myrestoreTime = ""
                        if($("input[name='optionsRadios']:checked").val()=="2" && $('#datetimepicker').val()!="")
                            myrestoreTime = $('#datetimepicker').val()
                        var iscover = $("input[name='overwrite']:checked").val();

                        var mypath = "same"
                        if($("input[name='path']:checked").val()=="2")
                            mypath = $('#mypath').val()
                        var treeObj = $.fn.zTree.getZTreeObj("treeDemo");
                        var nodes = treeObj.getCheckedNodes(true);
                        var selectedfile = ""
                         $("#fs_se_1 option").each(function (){
                            var txt = $(this).val();
                            selectedfile =selectedfile + txt +"*!-!*"
                            }
                         );
                        $.ajax({
                                type: "POST",
                                url: "../../dofilerecovery/",
                                data: {
                                            instanceName:$('#instanceName').val(),
                                            sourceClient:$('#sourceClient').val(),
                                            destClient:$('#destClient').val(),
                                            restoreTime:myrestoreTime,
                                            iscover:iscover,
                                            mypath:mypath,
                                            selectedfile: selectedfile,
                                        },
                                success:function(data){
                                        alert(data);
                                },
                                error : function(e){
                                    alert("恢复启动失败，请于客服联系。");
                                }
                            });
                    }
                }
            }
        })

         $('#selectpath').click(function(){
            $('#fs_se_1').empty();
            var treeObj = $.fn.zTree.getZTreeObj("treeDemo");
            var nodes = treeObj.getCheckedNodes(true);
            for (var k = 0, length = nodes.length; k < length; k++) {
                var halfCheck = nodes[k].getCheckStatus();
                if (!halfCheck.half){
                    $("#fs_se_1").append("<option value='\\" + nodes[k].id + "\\'>\\" + nodes[k].id + "\\</option>");
                }
            }
            if (nodes.length==0)
                $("#fs_se_1").append("<option value='\\'>\\</option>");
         })

    });
    var setting = {
        async: {
            enable: true,
            url:'../../getfiletree/',
            autoParam:["id"],
            otherParam:{"clientName":$('#sourceClient').val()},
            dataFilter: filter
        },
        check: {
            enable: true,
            chkStyle: "checkbox",               //多选
            chkboxType: { "Y": "s", "N": "ps" }  //不级联父节点选择
        },
        view:{
            showLine:false
        },

    };
    function filter(treeId, parentNode, childNodes) {
        if (!childNodes) return null;
        for (var i=0, l=childNodes.length; i<l; i++) {
            childNodes[i].name = childNodes[i].name.replace(/\.n/g, '.');
        }
        return childNodes;
    }

    $(document).ready(function(){
        $.fn.zTree.init($("#treeDemo"), setting);
    });
