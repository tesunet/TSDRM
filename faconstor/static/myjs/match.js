    $(document).ready(function() {
        $('#sample_1').dataTable( {
            "bAutoWidth": true,
            "bSort": false,
            "bProcessing": true,
            "ajax": "../matchdata/",
            "columns": [
                { "data": "clientName" },
                { "data": "platform" },
                { "data": "agentType" },
                { "data": "installTime" },
            ],
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

        $('#match').click(function(){
            $.ajax({
                type: "POST",
                dataType: 'json',
                url: "../matching/",
                success:function(data)
                {
                        if(data["value"]=="1")
                        {
                            $('#div1').hide()
                            $('#div2').show()
                            $("#my_multi_select1").empty();
                            for (var i=0;i<data["list"].length;i++){
                                if (data["list"][i]["selected"])
                                    $("#my_multi_select1").append("<option selected value='" + data["list"][i]["clientId"] + "'>" + data["list"][i]["clientName"] + "</option>");
                                else
                                    $("#my_multi_select1").append("<option value='" + data["list"][i]["clientId"] + "'>" + data["list"][i]["clientName"] + "</option>");
                            }
                            $('#my_multi_select1').multiSelect('refresh');
                        }
                        else
                        {
                            alert("获取客户端列表失败，请于客服联系。");
                            $('#static').modal('hide');
                        }
                },
                error : function(e){
                    alert("获取客户端列表失败，请于客服联系。");
                }
            });
        })

        $('#save1').click(function(){
            if (confirm("此操作将解除未勾选客户端的控制，确定要继续吗？")) {
                var table = $('#sample_1').DataTable();
                if ($('#password').val()=="")
                    alert("保存前请输入密码。");
                else
                {
                    var clientlist = ""
                     $("#my_multi_select1").find("option:selected").each(function (){
                        var txt = $(this).val();
                        clientlist =clientlist + txt +"*!-!*"
                        }
                     );

                    $.ajax({
                        type: "POST",
                        url: "../matchsave/",
                        data: {

                                    password:$('#password').val(),
                                    clientlist:clientlist,

                                },
                        success:function(data){
                                alert(data);
                                if(data=="保存成功。")
                                {
                                    $('#static1').modal('hide');
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

         $('#my_multi_select1').multiSelect({
      selectableHeader: "<input type='text' class='search-input' autocomplete='off' placeholder='未选择'>",
      selectionHeader: "<input type='text' class='search-input' autocomplete='off' placeholder='已选择'>",
      afterInit: function(ms){
        var that = this,
            $selectableSearch = that.$selectableUl.prev(),
            $selectionSearch = that.$selectionUl.prev(),
            selectableSearchString = '#'+that.$container.attr('id')+' .ms-elem-selectable:not(.ms-selected)',
            selectionSearchString = '#'+that.$container.attr('id')+' .ms-elem-selection.ms-selected';

        that.qs1 = $selectableSearch.quicksearch(selectableSearchString)
        .on('keydown', function(e){
          if (e.which === 40){
            that.$selectableUl.focus();
            return false;
          }
        });

        that.qs2 = $selectionSearch.quicksearch(selectionSearchString)
        .on('keydown', function(e){
          if (e.which == 40){
            that.$selectionUl.focus();
            return false;
          }
        });
      },
      afterSelect: function(){
        this.qs1.cache();
        this.qs2.cache();
      },
      afterDeselect: function(){
        this.qs1.cache();
        this.qs2.cache();
      }
    });
    } );
