    $(document).ready(function() {
        $('#sample_1').dataTable( {
            "bAutoWidth": true,
            "bProcessing": true,
            "ajax": "../../oraclerecoverydata?clientName=" + $('#sourceClient').val(),
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
            $("#datetimepicker").val(data.LastTime);
            $("input[name='optionsRadios'][value='1']").prop("checked",false);
            $("input[name='optionsRadios'][value='2']").prop("checked",true);
        });
        $('#datetimepicker').datetimepicker({
            format:'yyyy-mm-dd hh:ii:ss',
            pickerPosition:'top-right'
            });
        $('#recovery').click(function(){
            if ($("input[name='optionsRadios']:checked").val()=="2" && $('#datetimepicker').val()=="")
                alert("请输入时间。");
            else{
                if($('#destClient').val()=="")
                    alert("请选择目标客户端。");
                else
                {
                    var myrestoreTime = ""
                    if($("input[name='optionsRadios']:checked").val()=="2" && $('#datetimepicker').val()!="")
                        myrestoreTime = $('#datetimepicker').val()
                    $.ajax({
                            type: "POST",
                            url: "../../dooraclerecovery/",
                            data: {
                                        instanceName:$('#instanceName').val(),
                                        sourceClient:$('#sourceClient').val(),
                                        destClient:$('#destClient').val(),
                                        restoreTime:myrestoreTime,
                                    },
                            success:function(data){
                                    alert(data);
                            },
                            error : function(e){
                                alert("恢复失败，请于客服联系。");
                            }
                        });
                }
            }
        })
    } );