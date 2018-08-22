    $(document).ready(function() {
        $('#sample_1').dataTable( {
            "bAutoWidth": true,
            "bSort": false,
            "bProcessing": true,
            "ajax": "../phyproconfigdata/",
            "columns": [
                { "data": "appGroup" },
                { "data": "clientName" },
                { "data": "platform" },
                { "data": "status" },
                { "data": null },
            ],

            "columnDefs": [{
                    "targets": -1,
                    "data": null,
                    "defaultContent": "<button  id='edit' title='编辑' data-toggle='modal'  data-target='#static'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button>"
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
        $('#sample_1 tbody').on( 'click', 'button#edit', function () {
                var table = $('#sample_1').DataTable();
                var data = table.row( $(this).parents('tr') ).data();
                $("#clientGUID").val(data.clientGUID);
                $("#clientName").val(data.clientName);
                $("#appGroup").val(data.appGroup);
                $('#agentTypeid li').remove();
                $('#tab1_0').removeClass("active");
                $('#tab1_1').removeClass("active");
                $('#tab1_2').removeClass("active");
                $('#tab1_3').removeClass("active");
                $('#fs').val("0")
                $('#oracle').val("0")
                $('#mssql').val("0")
                $('#fs_dataSetGUID').val("0")
                $('#oracle_dataSetGUID').val("0")
                $('#mssql_dataSetGUID').val("0")
                $('#password').val("")
                $('#fs_schdule').val("")
                $('#fs_storage').val("")
                $('#oracle_dbschdule').val("")
                $('#oracle_logschdule').val("")
                $('#oracle_dbstorage').val("")
                $('#oracle_logstorage').val("")
                $("#oracle_name").val("")
                $("#oracle_username").val("")
                $("#oracle_oraclehome").val("")
                $("#oracle_conn1").val("")
                $("#oracle_conn2").val("")
                $("#oracle_conn3").val("")
                $("#oracle_mypassword").val("")
                $("#oracle_repassword").val("")
                $('#mssql_dbschdule').val("")
                $('#mssql_logschdule').val("")
                $('#mssql_dbstorage').val("")
                $('#mssql_logstorage').val("")
                $("#mssql_name").val("")
                $("#mssql_username").val("")
                $("#mssql_mypassword").val("")
                $("#mssql_repassword").val("")
                $('#mssql_isvvs').prop("checked",false);
                $('#mssql_iscover').prop("checked",false);

                $('#fs_se_1').empty()
                $('#fs_isBackupOS').prop("checked",false);
                $('#content1').val("")
                $('#agentTypeid').append("<li ><a id='tabcheck_1' href='#tab1_0' data-toggle='tab'> 基本信息</a></li>")
                if (data.agentType.length==0)
                {
                    ;
                }
                else
                {
                    for (var i=0;i<data.agentType.length;i++)
                    {
                        if(data.agentType[i]=="FILESYSTEM")
                        {
                             $('#fs').val("1")
                             $('#agentTypeid').append("<li ><a  href='#tab1_1' data-toggle='tab'> 应用环境保护配置</a></li>")
                        }

                        if(data.agentType[i]=="ORACLE")
                        {
                            $('#oracle').val("1")
                            $('#agentTypeid').append("<li ><a id='ractab' href='#tab1_2' data-toggle='tab'> ORACLE数据库保护配置</a></li>")
                        }
                        if(data.agentType[i]=="MSSQL")
                        {
                            $('#mssql').val("1")
                            $('#agentTypeid').append("<li ><a href='#tab1_3' data-toggle='tab'> MSSQL数据库保护配置</a></li>")
                        }
                    }


                     $('#tabcheck_1').click();

                }


                $.ajax({
                    type: "POST",
                    dataType: 'json',
                    url: "../getphydataget/",
                    data:
                            {
                                clientGUID: $("#clientGUID").val(),
                                fs:$('#fs').val(),
                                oracle:$('#oracle').val(),
                                mssql:$('#mssql').val(),
                            },
                    success:function(data){
                        if(data["fs"]){
                            $("#fs_dataSetGUID").val(data["fs"]["dataSetGUID"]);
                            $("#fs_schdule").val(data["fs"]["schdule"]);
                            $("#fs_storage").val(data["fs"]["storage"]);
                            if(data["fs"]["isBackupOS"]=="TRUE")
                                $('#fs_isBackupOS').prop("checked",true);
                            for (var i=0;i<data["fs"]["path"].length;i++){
                                 $("#fs_se_1").append("<option value='" + data["fs"]["path"][i] + "'>" + data["fs"]["path"][i] + "</option>");
                            }

                        }
                        if(data["oracle"]){
                            $("#oracle_dataSetGUID").val(data["oracle"]["dataSetGUID"]);
                            $("#oracle_dbschdule").val(data["oracle"]["dbschdule"]);
                            $("#oracle_logschdule").val(data["oracle"]["logschdule"]);
                            $("#oracle_dbstorage").val(data["oracle"]["dbstorage"]);
                            $("#oracle_logstorage").val(data["oracle"]["logstorage"]);
                            $("#oracle_name").val(data["oracle"]["name"]);
                            $("#oracle_username").val(data["oracle"]["username"]);
                            $("#oracle_oraclehome").val(data["oracle"]["oraclehome"]);
                            $("#oracle_conn1").val(data["oracle"]["conn1"]);
                            $("#oracle_conn2").val(data["oracle"]["conn2"]);
                            $("#oracle_conn3").val(data["oracle"]["conn3"]);


                        }
                        if(data["mssql"]){
                            $("#mssql_dataSetGUID").val(data["mssql"]["dataSetGUID"]);
                            $("#mssql_dbschdule").val(data["mssql"]["dbschdule"]);
                            $("#mssql_logschdule").val(data["mssql"]["logschdule"]);
                            $("#mssql_dbstorage").val(data["mssql"]["dbstorage"]);
                            $("#mssql_logstorage").val(data["mssql"]["logstorage"]);
                            $("#mssql_backupContent").val(data["mssql"]["backupContent"]);

                            if(data["mssql"]["isvvs"]=="TRUE")
                                $('#mssql_isvvs').prop("checked",true);
                            if(data["mssql"]["iscover"]=="TRUE")
                                $('#mssql_iscover').prop("checked",true);
                             $("#mssql_name").val(data["mssql"]["name"]);
                            $("#mssql_username").val(data["mssql"]["username"]);

                        }
                    },
                    error : function(e){
                        alert("数据读取错误。");
                    }
                });
        });

        $('#new').click(function(){

            if ($("#content1").val()=="")
                alert("内容为空。");
            else{
                var newtext = $("#content1").val().toUpperCase()
                if (newtext.length>0&&newtext[newtext.length-1]=="\\")
                    newtext = newtext.substring(0,newtext.length-1)
                var issave= true
                $("#fs_se_1 option").each(function (){
                    var txt = $(this).val().toUpperCase();
                    if (txt.indexOf(newtext)==0||newtext.indexOf(txt)==0)
                    {
                        var text = txt.replace(newtext,"").replace(" ","")
                        if (text.length>0)
                        {
                            if( text[0]=='\\')
                                issave= false
                        }
                        else
                            issave= false
                        var text = newtext.replace(txt,"").replace(" ","")
                        if (text.length>0)
                        {
                            if( text[0]=='\\')
                                issave= false
                        }
                        else
                            issave= false
                    }
                })
                if(issave)
                    $("#fs_se_1").append("<option value='" + $("#content1").val() + "'>" + $("#content1").val() + "</option>");
                else
                    alert("与已存在路径内容重叠。");
            }
        })
        $('#edit').click(function(){
            if ($("#content1").val()=="")
                alert("内容为空。");
            else{
                if ($("#fs_se_1").find('option:selected').length==0)
                    alert("请选择要修改的记录。");
                else
                {
                    if ($("#fs_se_1").find('option:selected').length>1)
                         alert("修改时请不要选择多条记录。");
                    else
                    {
                        var newtext = $("#content1").val().toUpperCase()
                        if (newtext.length>0&&newtext[newtext.length-1]=="\\")
                            newtext = newtext.substring(0,newtext.length-1)
                        var issave= true
                        $("#fs_se_1 option").each(function (){
                            var txt = $(this).val().toUpperCase();
                            if(txt!= $("#fs_se_1").find('option:selected').val().toUpperCase()){
                                if (txt.indexOf(newtext)==0||newtext.indexOf(txt)==0)
                                {
                                    var text = txt.replace(newtext,"").replace(" ","")
                                    if (text.length>0)
                                    {
                                        if( text[0]=='\\')
                                            issave= false
                                    }
                                    else
                                        issave= false
                                    var text = newtext.replace(txt,"").replace(" ","")
                                    if (text.length>0)
                                    {
                                        if( text[0]=='\\')
                                            issave= false
                                    }
                                    else
                                        issave= false
                                }
                            }
                        })
                        if(issave)
                        {
                            $("#fs_se_1").find('option:selected').val($("#content1").val());
                            $("#fs_se_1").find('option:selected').text($("#content1").val());
                            }
                        else
                            alert("与已存在路径内容重叠。");

                     }
                }
            }
        })
        $('#del').click(function(){
            if ($("#fs_se_1").find('option:selected').length==0)
                    alert("请选择要删除的记录。");
                else
                {
                        $("#fs_se_1").find('option:selected').remove();
                }
        })

        $('#fs_se_1').change(function(){
            $("#content1").val($("#fs_se_1").find('option:selected').val())
        })


        $('#save0').click(function(){
            var table = $('#sample_1').DataTable();
            $.ajax({
                type: "POST",
                dataType: 'json',
                url: "../phyproconfigsaveapp/",
                data: {

                            clientGUID: $("#clientGUID").val(),
                            appGroup:$('#appGroup').val(),
                        },
                success:function(data){
                        alert(data["text"]);
                        table.ajax.reload();
                },
                error : function(e){
                    alert("保存失败，请于客服联系。");
                }
            });
        })
        $('#save1').click(function(){
            var table = $('#sample_1').DataTable();
            if ($('#password1').val()=="")
                alert("保存前请输入密码。");
            else
            {
                var checkvalue = "FALSE"
                if ($('#fs_isBackupOS').is(':checked'))
                    checkvalue = "TRUE"
                var isupdate = "FALSE"
                if ($('#fs_update').is(':checked'))
                    isupdate = "TRUE"
                var fs_backupContent = ""
                 $("#fs_se_1 option").each(function (){
                    var txt = $(this).val();
                    fs_backupContent =fs_backupContent + txt +"*!-!*"
                    }
                 );
                $.ajax({
                    type: "POST",
                    dataType: 'json',
                    url: "../phyproconfigsavefile/",
                    data: {
                                password:$('#password1').val(),
                                fs:$('#fs').val(),
                                clientGUID: $("#clientGUID").val(),
                                appGroup:$('#appGroup').val(),
                                fs_dataSetGUID:$('#fs_dataSetGUID').val(),
                                fs_schdule:$('#fs_schdule').val(),
                                fs_storage:$('#fs_storage').val(),
                                fs_isBackupOS:checkvalue,
                                fs_isupdate:isupdate,
                                fs_backupContent:fs_backupContent,
                            },
                    success:function(data){
                            alert(data["text"]);
                            $("#fs_dataSetGUID").val(data["fs_GUID"]);
                            table.ajax.reload();
                    },
                    error : function(e){
                        alert("保存失败，请于客服联系。");
                    }
                });
            }
        })
        $('#save2').click(function(){
            var table = $('#sample_1').DataTable();
            if ($('#oracle_mypassword').val()!=$('#oracle_repassword').val())
                alert("两次Oracle密码输入不一致。");
            else{
                if ($('#password2').val()=="")
                    alert("保存前请输入密码。");
                else
                {
                    var isupdate = "FALSE"
                    if ($('#oracle_update').is(':checked'))
                        isupdate = "TRUE"
                    $.ajax({
                        type: "POST",
                        dataType: 'json',
                        url: "../phyproconfigsaveoracle/",
                        data: {
                                    password:$('#password2').val(),
                                    oracle:$('#oracle').val(),
                                    clientGUID: $("#clientGUID").val(),
                                    appGroup:$('#appGroup').val(),

                                    oracle_dataSetGUID:$('#oracle_dataSetGUID').val(),
                                    oracle_dbschdule:$('#oracle_dbschdule').val(),
                                    oracle_logschdule:$('#oracle_logschdule').val(),
                                    oracle_dbstorage:$('#oracle_dbstorage').val(),
                                    oracle_logstorage:$('#oracle_logstorage').val(),
                                    oracle_name:$('#oracle_name').val(),
                                    oracle_username:$('#oracle_username').val(),
                                    oracle_mypassword:$('#oracle_mypassword').val(),
                                    oracle_oraclehome:$('#oracle_oraclehome').val(),
                                    oracle_conn1:$('#oracle_conn1').val(),
                                    oracle_conn2:$('#oracle_conn2').val(),
                                    oracle_conn3:$('#oracle_conn3').val(),
                                    oracle_isupdate:isupdate,

                                },
                        success:function(data){
                                $("#oracle_dataSetGUID").val(data["oracle_GUID"]);
                                alert(data["text"]);
                                table.ajax.reload();
                        },
                        error : function(e){
                            alert("保存失败，请于客服联系。");
                        }
                    });
                }

            }
        })
        $('#save3').click(function(){
            var table = $('#sample_1').DataTable();
            if ($('#mssql_mypassword').val()!=$('#mssql_repassword').val())
                alert("两次MSSQL密码输入不一致。");
            else{
                if ($('#password3').val()=="")
                    alert("保存前请输入密码。");
                else
                {

                    var isvvs = "FALSE"
                    if ($('#mssql_isvvs').is(':checked'))
                        isvvs = "TRUE"

                    var iscover = "FALSE"
                    if ($('#mssql_iscover').is(':checked'))
                        iscover = "TRUE"
                    var isupdate = "FALSE"
                    if ($('#mssql_update').is(':checked'))
                        isupdate = "TRUE"
                    $.ajax({
                        type: "POST",
                        dataType: 'json',
                        url: "../phyproconfigsavemssql/",
                        data: {
                                    password:$('#password3').val(),
                                    mssql:$('#mssql').val(),
                                    clientGUID: $("#clientGUID").val(),
                                    appGroup:$('#appGroup').val(),
                                    mssql_dataSetGUID:$('#mssql_dataSetGUID').val(),
                                    mssql_dbschdule:$('#mssql_dbschdule').val(),
                                    mssql_logschdule:$('#mssql_logschdule').val(),
                                    mssql_dbstorage:$('#mssql_dbstorage').val(),
                                    mssql_logstorage:$('#mssql_logstorage').val(),
                                    mssql_backupContent:$('#mssql_backupContent').val(),
                                    mssql_name:$('#mssql_name').val(),
                                    mssql_username:$('#mssql_username').val(),
                                    mssql_mypassword:$('#mssql_mypassword').val(),
                                    mssql_isvvs:isvvs,
                                    mssql_iscover:iscover,
                                    mssql_isupdate:isupdate,
                                },
                        success:function(data){
                                $("#mssql_dataSetGUID").val(data["mssql_GUID"]);
                                alert(data["text"]);
                                table.ajax.reload();
                        },
                        error : function(e){
                            alert("保存失败，请于客服联系。");
                        }
                    });
                }
            }
        })

    } );
