    $(document).ready(function() {

        $('#sample_1').dataTable( {
            "bAutoWidth": true,
            "bProcessing": true,
            "ajax": "../../vmrecoverydata?clientName=" + $('#sourceClient').val(),
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


        $('#sourceVM').change(function(){
            $('#newname').val("new_" + $("#sourceVM").find("option:selected").text());
        })
        $('#newname').val("new_" + $("#sourceVM").find("option:selected").text());
        $("#proxyClient").empty();
        $.ajax({
            type: "POST",
            url: "../../getproxylist/",
            data:
                {
                  clientName: $("#destClient").val()
                },
            dataType: "json",
            success:function(data){
                for (var i=0;i<data.length;i++){
                    $("#proxyClient").append("<option value='" + data[i] + "'>" + data[i] + "</option>");

                }
            },
          });

       $('#destClient').change(function(){
        $("#proxyClient").empty();
            $.ajax({
            type: "POST",
            url: "../../getproxylist/",
            data:
                {
                  clientName: $("#destClient").val()
                },
            dataType: "json",
            success:function(data){
                for (var i=0;i<data.length;i++){
                    $("#proxyClient").append("<option value='" + data[i] + "'>" + data[i] + "</option>");

                }
            },
          });
        })

        $('#recovery').click(function(){

            if ($('#sourceVM').val()=="")
                alert("请选择虚机。");
            else{
                if($('#newname').val()=="")
                    alert("虚机新名称不能为空。");
                else
                {
                    if($('#destClient').val()=="")
                        alert("请选择目标虚拟中心。");
                    else
                    {
                        if($('#proxyClient').val()=="")
                            alert("请选择目标代理客户端。");
                        else
                        {
                            if($('#dslist').val()=="")
                                alert("请选择数据存储。");
                            else
                            {
                                if($('#newname').val()==$("#sourceVM").find("option:selected").text())
                                    alert("请修改虚机新名称。");
                                else
                                {
                                    var power = "FALSE"
                                    if ($('#power').is(':checked'))
                                        power = "TRUE"
                                    var iscover = "FALSE"
                                    if ($('#isoverwrite').is(':checked'))
                                        iscover = "TRUE"
                                    var myrestoreTime = ""
                                    if($("input[name='optionsRadios']:checked").val()=="2" && $('#datetimepicker').val()!="")
                                        myrestoreTime = $('#datetimepicker').val()
                                    $.ajax({
                                            type: "POST",
                                            url: "../../dovmrecovery/",
                                            data: {
                                                        appName:$('#appName').val(),
                                                        sourceClient:$('#sourceClient').val(),
                                                        sourceVMName:$("#sourceVM").find("option:selected").text(),
                                                        sourceVMGUID:$('#sourceVM').val(),
                                                        newname:$('#newname').val(),
                                                        destClient:$('#destClient').val(),
                                                        proxyClient:$('#proxyClient').val(),
                                                        esxlist:$('#esxlist').val(),
                                                        dslist:$('#dslist').find("option:selected").text(),
                                                        disk:$('#disk').val(),
                                                        type:$('#type').val(),
                                                        power:power,
                                                        iscover:iscover,
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
                        }
                    }
                }
            }
        })

        $("#dslist").val("");
        $("#dslist option").each(function(){
            if($(this).val().indexOf($("#esxlist").val()) >= 0 ){
                $(this).show();
                $(this).prop("selected",true);
           }
           else
            $(this).hide();
          });

        $('#esxlist').change(function(){
            $("#dslist").val("");
            $("#dslist option").each(function(){
                if($(this).val().indexOf($("#esxlist").val()) >= 0 ){
                    $(this).show();
                    $(this).prop("selected",true);
               }
               else
                $(this).hide();
              });

        })


    } );