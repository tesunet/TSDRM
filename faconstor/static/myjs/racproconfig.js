    $(document).ready(function() {
        $('#sample_1').dataTable( {
            "bAutoWidth": true,
            "bSort": false,
            "bProcessing": true,
            "ajax": "../racproconfigdata/",
            "columns": [
                { "data": "clientName" },
                { "data": "platform" },
                { "data": "databaseName" },
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
                $("#databaseName").val(data.databaseName);
                 $("#dataSetGUID").val(data.dataSetGUID);
                $("#pyhhost").select2("val", "");
                for (var i=0;i<data.proxylist.length;i++){
                    $("#pyhhost").find("option[value='" + data.proxylist[i].clientGUID + "']").remove();
                    $("#pyhhost").append("<option selected value='" + data.proxylist[i].clientGUID + "'>" + data.proxylist[i].clientName + "</option>");
                }
                $(".select2, .select2-multiple").select2({
                    width: null
                });
                $('#raclist li').remove();
                $('#tab1_1').removeClass("active");
                $('#tab1_2').removeClass("active");
                $('#tab1_3').removeClass("active");
                $('#tab1_4').removeClass("active");
                $('#tab1_5').removeClass("active");

                $('#password').val("")
                $('#del').show()

                $('#oracle_dbschdule').val("")
                $('#oracle_logschdule').val("")
                $('#oracle_dbstorage').val("")
                $('#oracle_logstorage').val("")

                $('#oracle_pyhGUID_1').val("0")
                $('#oracle_pyhGUID_2').val("0")
                $('#oracle_pyhGUID_3').val("0")
                $('#oracle_pyhGUID_4').val("0")
                $('#oracle_pyhGUID_5').val("0")


                $("#oracle_name_1").val("")
                $("#oracle_username_1").val("")
                $("#oracle_mypassword_1").val("")
                $("#oracle_repassword_1").val("")
                $("#oracle_oraclehome_1").val("")
                $("#oracle_conn1_1").val("")
                $("#oracle_conn2_1").val("")
                $("#oracle_conn3_1").val("")

                $("#oracle_name_2").val("")
                $("#oracle_username_2").val("")
                $("#oracle_mypassword_2").val("")
                $("#oracle_repassword_2").val("")
                $("#oracle_oraclehome_2").val("")
                $("#oracle_conn1_2").val("")
                $("#oracle_conn2_2").val("")
                $("#oracle_conn3_2").val("")

                $("#oracle_name_3").val("")
                $("#oracle_username_3").val("")
                $("#oracle_mypassword_3").val("")
                $("#oracle_repassword_3").val("")
                $("#oracle_oraclehome_3").val("")
                $("#oracle_conn1_3").val("")
                $("#oracle_conn2_3").val("")
                $("#oracle_conn3_3").val("")

                $("#oracle_name_4").val("")
                $("#oracle_username_4").val("")
                $("#oracle_mypassword_4").val("")
                $("#oracle_repassword_4").val("")
                $("#oracle_oraclehome_4").val("")
                $("#oracle_conn1_4").val("")
                $("#oracle_conn2_4").val("")
                $("#oracle_conn3_4").val("")

                $("#oracle_name_5").val("")
                $("#oracle_username_5").val("")
                $("#oracle_mypassword_5").val("")
                $("#oracle_repassword_5").val("")
                $("#oracle_oraclehome_5").val("")
                $("#oracle_conn1_5").val("")
                $("#oracle_conn2_5").val("")
                $("#oracle_conn3_5").val("")

                $("#oracle_dbschdule").val(data.oracle_dbschdule);
                $("#oracle_logschdule").val(data.oracle_logschdule);
                $("#oracle_dbstorage").val(data.oracle_dbstorage);
                $("#oracle_logstorage").val(data.oracle_logstorage);


                if (data.raclist.length==0)
                {
                    $('#raclist').hide()
                    $('#myTabContent1').hide()
                }
                else
                {
                    $('#raclist').show()
                    $('#myTabContent1').show()
                    for (var i=0;i<data.raclist.length;i++)
                    {
                        $('#raclist').append("<li id='" + data.raclist[i].pyhGUID +  "' ><a  id='tabcheck_" + (i+1).toString() + "' href='#tab1_" + (i+1).toString() + "' data-toggle='tab'>" + data.raclist[i].pyhclientName +  "</a></li>")
                        $('#oracle_pyhGUID_' + (i+1).toString()).val(data.raclist[i].pyhGUID)

                        $("#oracle_name_" + (i+1).toString()).val(data.raclist[i].name);
                        $("#oracle_username_" + (i+1).toString()).val(data.raclist[i].username);
                        $("#oracle_oraclehome_" + (i+1).toString()).val(data.raclist[i].oraclehome);
                        $("#oracle_conn1_" + (i+1).toString()).val(data.raclist[i].conn1);
                        $("#oracle_conn2_" + (i+1).toString()).val(data.raclist[i].conn2);
                        $("#oracle_conn3_" + (i+1).toString()).val(data.raclist[i].conn3);

                    }
                    $('#tabcheck_1').click();


                }

        });

        $('#new').click(function(){
            $("#clientGUID").val("0");
                $("#clientName").val("");
                $("#databaseName").val("");
                 $("#dataSetGUID").val("0");
                $("#pyhhost").select2("val", "");

                $('#raclist li').remove();
                $('#tab1_1').removeClass("active");
                $('#tab1_2').removeClass("active");
                $('#tab1_3').removeClass("active");
                $('#tab1_4').removeClass("active");
                $('#tab1_5').removeClass("active");

                $('#password').val("")

                $('#oracle_dbschdule').val("")
                $('#oracle_logschdule').val("")
                $('#oracle_dbstorage').val("")
                $('#oracle_logstorage').val("")

                $("#oracle_name_1").val("")
                $("#oracle_username_1").val("")
                $("#oracle_mypassword_1").val("")
                $("#oracle_repassword_1").val("")
                $("#oracle_oraclehome_1").val("")
                $("#oracle_conn1_1").val("")
                $("#oracle_conn2_1").val("")
                $("#oracle_conn3_1").val("")

                $("#oracle_name_2").val("")
                $("#oracle_username_2").val("")
                $("#oracle_mypassword_2").val("")
                $("#oracle_repassword_2").val("")
                $("#oracle_oraclehome_2").val("")
                $("#oracle_conn1_2").val("")
                $("#oracle_conn2_2").val("")
                $("#oracle_conn3_2").val("")

                $("#oracle_name_3").val("")
                $("#oracle_username_3").val("")
                $("#oracle_mypassword_3").val("")
                $("#oracle_repassword_3").val("")
                $("#oracle_oraclehome_3").val("")
                $("#oracle_conn1_3").val("")
                $("#oracle_conn2_3").val("")
                $("#oracle_conn3_3").val("")

                $("#oracle_name_4").val("")
                $("#oracle_username_4").val("")
                $("#oracle_mypassword_4").val("")
                $("#oracle_repassword_4").val("")
                $("#oracle_oraclehome_4").val("")
                $("#oracle_conn1_4").val("")
                $("#oracle_conn2_4").val("")
                $("#oracle_conn3_4").val("")

                $("#oracle_name_5").val("")
                $("#oracle_username_5").val("")
                $("#oracle_mypassword_5").val("")
                $("#oracle_repassword_5").val("")
                $("#oracle_oraclehome_5").val("")
                $("#oracle_conn1_5").val("")
                $("#oracle_conn2_5").val("")
                $("#oracle_conn3_5").val("")

               $('#oracle_pyhGUID_1').val("0")
                $('#oracle_pyhGUID_2').val("0")
                $('#oracle_pyhGUID_3').val("0")
                $('#oracle_pyhGUID_4').val("0")
                $('#oracle_pyhGUID_5').val("0")

                $('#raclist').hide()
                $('#myTabContent1').hide()
                $('#del').hide()
        })

        $('#save1').click(function(){
            var table = $('#sample_1').DataTable();
            if ($('#oracle_mypassword_1').val()!=$('#oracle_repassword_1').val() || $('#oracle_mypassword_2').val()!=$('#oracle_repassword_2').val()|| $('#oracle_mypassword_3').val()!=$('#oracle_repassword_3').val()|| $('#oracle_mypassword_4').val()!=$('#oracle_repassword_4').val()|| $('#oracle_mypassword_5').val()!=$('#oracle_repassword_5').val())
                alert("两次密码输入不一致。");
            else{
                if ($('#password').val()=="")
                    alert("保存前请输入密码。");
                else
                {
                    var pyhhostlist = ""
                     $("#pyhhost").find("option:selected").each(function (){
                        var txt = $(this).val();
                        pyhhostlist =pyhhostlist + txt +"*!-!*"
                        }
                     );
                    $.ajax({
                        type: "POST",
                        url: "../racproconfigsave/",
                        data: {
                                password:$('#password').val(),
                                clientGUID:$("#clientGUID").val(),
                                clientName:$("#clientName").val(),
                                databaseName:$("#databaseName").val(),
                                dataSetGUID:$("#dataSetGUID").val(),
                                pyhhostlist:pyhhostlist,
                                oracle_dbschdule:$("#oracle_dbschdule").val(),
                                oracle_logschdule:$("#oracle_logschdule").val(),
                                oracle_dbstorage:$("#oracle_dbstorage").val(),
                                oracle_logstorage:$("#oracle_logstorage").val(),

                                oracle_name_1:$("#oracle_name_1").val(),
                                oracle_username_1:$("#oracle_username_1").val(),
                                oracle_mypassword_1:$("#oracle_mypassword_1").val(),
                                oracle_oraclehome_1:$("#oracle_oraclehome_1").val(),
                                oracle_conn1_1:$("#oracle_conn1_1").val(),
                                oracle_conn2_1:$("#oracle_conn2_1").val(),
                                oracle_conn3_1:$("#oracle_conn3_1").val(),
                                oracle_pyhGUID_1:$('#oracle_pyhGUID_1').val(),

                                oracle_name_2:$("#oracle_name_2").val(),
                                oracle_username_2:$("#oracle_username_2").val(),
                                oracle_mypassword_2:$("#oracle_mypassword_2").val(),
                                oracle_oraclehome_2:$("#oracle_oraclehome_2").val(),
                                oracle_conn1_2:$("#oracle_conn1_2").val(),
                                oracle_conn2_2:$("#oracle_conn2_2").val(),
                                oracle_conn3_2:$("#oracle_conn3_2").val(),
                                oracle_pyhGUID_2:$('#oracle_pyhGUID_2').val(),

                                oracle_name_3:$("#oracle_name_3").val(),
                                oracle_username_3:$("#oracle_username_3").val(),
                                oracle_mypassword_3:$("#oracle_mypassword_3").val(),
                                oracle_oraclehome_3:$("#oracle_oraclehome_3").val(),
                                oracle_conn1_3:$("#oracle_conn1_3").val(),
                                oracle_conn2_3:$("#oracle_conn2_3").val(),
                                oracle_conn3_3:$("#oracle_conn3_3").val(),
                                oracle_pyhGUID_3:$('#oracle_pyhGUID_3').val(),

                                oracle_name_4:$("#oracle_name_4").val(),
                                oracle_username_4:$("#oracle_username_4").val(),
                                oracle_mypassword_4:$("#oracle_mypassword_4").val(),
                                oracle_oraclehome_4:$("#oracle_oraclehome_4").val(),
                                oracle_conn1_4:$("#oracle_conn1_4").val(),
                                oracle_conn2_4:$("#oracle_conn2_4").val(),
                                oracle_conn3_4:$("#oracle_conn3_4").val(),
                                oracle_pyhGUID_4:$('#oracle_pyhGUID_4').val(),

                                oracle_name_5:$("#oracle_name_5").val(),
                                oracle_username_5:$("#oracle_username_5").val(),
                                oracle_mypassword_5:$("#oracle_mypassword_5").val(),
                                oracle_oraclehome_5:$("#oracle_oraclehome_5").val(),
                                oracle_conn1_5:$("#oracle_conn1_5").val(),
                                oracle_conn2_5:$("#oracle_conn2_5").val(),
                                oracle_conn3_5:$("#oracle_conn3_5").val(),
                                oracle_pyhGUID_5:$('#oracle_pyhGUID_5').val(),

                                },
                        success:function(data){
                                alert(data);
                                if(data=="保存成功。")
                                {
                                    $('#static').modal('hide');
                                    table.ajax.reload();
                                }
                        },
                        error : function(e){
                            alert("保存失败，请于客服联系。");
                        }
                    });
                }
            }
        })

        $('#del').click(function(){
            var table = $('#sample_1').DataTable();
            if ($('#password').val()=="")
                alert("删除前请输入密码。");
            else
            {
                $.ajax({
                    type: "POST",
                    url: "../racproconfigdel/",
                    data: {

                                password:$('#password').val(),
                                clientGUID:$('#clientGUID').val(),
                                dataSetGUID:$('#dataSetGUID').val(),
                            },
                    success:function(data){
                            alert(data);
                            if(data=="删除成功。")
                            {
                                $('#static').modal('hide');
                                table.ajax.reload();
                            }
                    },
                    error : function(e){
                        alert("删除失败，请于客服联系。");
                    }
                });
            }
        })

        $('#pyhhost').change(function(){
            $('#raclist').show()
            $('#myTabContent1').show()
            $('#raclist li').remove();
            $('#oracle_pyhGUID_1').val("0")
            $('#oracle_pyhGUID_2').val("0")
            $('#oracle_pyhGUID_3').val("0")
            $('#oracle_pyhGUID_4').val("0")
            $('#oracle_pyhGUID_5').val("0")
            var pyhlength = $("#pyhhost").find("option:selected")
            if(pyhlength.length==0){
                $('#raclist').hide()
                $('#myTabContent1').hide()
            }
            else{
                 for (var i=0;i<pyhlength.length;i++)
                {

                    $('#raclist').append("<li id='" + pyhlength[i].value +  "' ><a id='tabcheck_" + (i+1).toString() + "' href='#tab1_" + (i+1).toString() + "' data-toggle='tab'>" + pyhlength[i].text +  "</a></li>")
                    $('#oracle_pyhGUID_' + (i+1).toString()).val(pyhlength[i].value)
                }
                $('#tabcheck_1').click();

           }



        })

    } );

