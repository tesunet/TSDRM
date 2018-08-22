    $(document).ready(function() {
        $('#sample_1').dataTable( {
            "bAutoWidth": true,
            "bSort": false,
            "bProcessing": true,
            "ajax": "../manualrecoverydata/",
            "columns": [
                { "data": "clientName" },
                { "data": "platform" },
                { "data": "type" },

            ],

            "columnDefs": [{
                    "targets": 0,
                    "mRender":function(data,type,full){
                        return "<a id='edit'  data-toggle='modal'  data-target='#static1'>" + data+"</a>"
                    }
            }],
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
        // 行按钮

        $('#sample_1 tbody').on( 'click', 'a#edit', function () {
                var table = $('#sample_1').DataTable();
                var data = table.row( $(this).parents('tr') ).data();
                if (data.type=="physical box"){
                    $("#vm").hide()
                    $("#filesystem").hide()
                    $("#oracle").hide()
                    $("#mssql").hide()
                    for (var i=0;i<data.agentType.length;i++)
                    {
                        if(data.agentType[i]=="FILESYSTEM")
                        {
                            $("#filesystem").show()
                            $("#filesystem").attr("href","/filerecovery/"+data.id);
                        }
                        if(data.agentType[i]=="ORACLE")
                        {
                            $("#oracle").show()
                            $("#oracle").attr("href","/oraclerecovery/"+data.id);
                        }
                        if(data.agentType[i]=="MSSQL")
                        {
                            $("#mssql").show()
                            $("#mssql").attr("href","/mssqlrecovery/"+data.id);
                        }
                    }

                }
                else
                {
                    if (data.type=="VMWARE"){
                        $("#vm").show()
                        $("#filesystem").hide()
                        $("#oracle").hide()
                        $("#mssql").hide()
                        $("#vm").attr("href","/vmrecovery/"+data.id);
                    }
                    else
                        alert("暂不支持。");
                }
        });

    } );