   var Activate = function () {


	var handleActivate = function () {


         $('.activate-form').validate({
	            errorElement: 'span', //default input error message container
	            errorClass: 'help-block', // default input error message class
	            focusInvalid: false, // do not focus the last invalid input
	            ignore: "",
	            rules: {
	                poolname: {
	                    required: true,
	                },
	                name: {
	                    required: true,
	                },
	            },

	            messages: { // custom messages for radio buttons and checkboxes
	            },

	            invalidHandler: function (event, validator) { //display error alert on form submit

	            },

	            highlight: function (element) { // hightlight error inputs
	                $(element)
	                    .closest('.form-group').addClass('has-error'); // set error class to the control group
	            },

	            success: function (label) {
	                label.closest('.form-group').removeClass('has-error');
	                label.remove();
	            },



	            submitHandler: function (form) {
	                form.submit();
	            }
	        });



	}

    return {
        //main function to initiate the module
        init: function () {

            handleActivate();
        }
    };

}();

    $(document).ready(function() {
        Activate.init();
        $('#sample_2').dataTable( {
            "bAutoWidth": true,
            "bSort": false,
            "bProcessing": true,
            "ajax": "../computerresourcepooldata/",
            "columns": [
                { "data": "id" },
                { "data": "name" },
                { "data": "type" },
                { "data": "description" },
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
        $('#sample_2 tbody').on( 'click', 'button#select', function () {
            var table = $('#sample_2').DataTable();
            var data = table.row( $(this).parents('tr') ).data();
            $("#poolid").val( data.id);
            $("#poolname").val( data.name);
            $('#static1').modal('hide');
        });
        $('#sample_1').dataTable( {
            "bAutoWidth": true,
            "bSort": false,
            "bProcessing": true,
            "ajax": "../computerresourcedata/",
            "columns": [
                { "data": "id" },
                { "data": "name" },
                { "data": "description" },
                { "data": "state" },
                { "data": null },
            ],

            "columnDefs": [{
                    "targets": -1,
                    "data": null,
                    "defaultContent": "<button  id='edit' title='编辑' data-toggle='modal'  data-target='#static'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-edit'></i></button><button title='删除'  id='delrow' class='btn btn-xs btn-primary' type='button'><i class='fa fa-trash-o'></i></button>"
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
        $('#sample_1 tbody').on( 'click', 'button#delrow', function () {
            if (confirm("确定要删除该条数据？")) {
                var table = $('#sample_1').DataTable();
                var data = table.row( $(this).parents('tr') ).data();
                $.ajax({
                        type: "POST",
                        url: "../computerresourcedel/",
                        data:
                            {
                              id: data.id
                            },
                        success:function(data){
                        if(data==1)
                        {
                            table.ajax.reload();
                            alert("删除成功！");
                        }
                        else
                        alert("删除失败，请于管理员联系。");
                        },
                        error : function(e){
                             alert("删除失败，请于管理员联系。");
                        }
                  });

        }
        });
        $('#sample_1 tbody').on( 'click', 'button#edit', function () {
                $("#disk2").hide()
                $("#disk3").hide()
                $("#disk4").hide()
                $("#disk5").hide()
                $("#disk6").hide()
                $("#disk2_size").attr("disabled","disabled")
                $("#disk3_size").attr("disabled","disabled")
                $("#disk4_size").attr("disabled","disabled")
                $("#disk5_size").attr("disabled","disabled")
                $("#disk6_size").attr("disabled","disabled")
                $("#disk2_name").attr("disabled","disabled")
                $("#disk3_name").attr("disabled","disabled")
                $("#disk4_name").attr("disabled","disabled")
                $("#disk5_name").attr("disabled","disabled")
                $("#disk6_name").attr("disabled","disabled")
                $("#disk2_type").attr("disabled","disabled")
                $("#disk3_type").attr("disabled","disabled")
                $("#disk4_type").attr("disabled","disabled")
                $("#disk5_type").attr("disabled","disabled")
                $("#disk6_type").attr("disabled","disabled")
                $("#disk1_size").val("");
                $("#disk2_size").val("");
                $("#disk3_size").val("");
                $("#disk4_size").val("");
                $("#disk5_size").val("");
                $("#disk6_size").val("");
                $("#disk1_name").val("");
                $("#disk2_name").val("");
                $("#disk3_name").val("");
                $("#disk4_name").val("");
                $("#disk5_name").val("");
                $("#disk6_name").val("");
                $("#add").show()

                var table = $('#sample_1').DataTable();
                var data = table.row( $(this).parents('tr') ).data();
                $("#id").val(data.id);
                $("#name").val(data.name);
                $("#poolid").val(data.poolid);
                $("#poolname").val(data.poolname);
                $("#cpu").val(data.cpu);
                $("#memory").val(data.memory);
                try
                {
                    $("#disk1_size").val(data.disks[0].size);
                }catch (e)
                { }
                try
                {
                    $("#disk2_size").val(data.disks[1].size);
                }catch (e)
                { }
                try
                {
                    $("#disk3_size").val(data.disks[2].size);
                }catch (e)
                { }
                try
                {
                    $("#disk4_size").val(data.disks[3].size);
                }catch (e)
                { }
                try
                {
                    $("#disk5_size").val(data.disks[4].size);
                }catch (e)
                { }
                try
                {
                    $("#disk6_size").val(data.disks[5].size);
                }catch (e)
                { }
                try
                {
                    $("#disk1_name").val(data.disks[0].name);
                }catch (e)
                { }
                try
                {
                    $("#disk2_name").val(data.disks[1].name);
                }catch (e)
                { }
                try
                {
                    $("#disk3_name").val(data.disks[2].name);
                }catch (e)
                { }
               try
                {
                    $("#disk4_name").val(data.disks[3].name);
                }catch (e)
                { }
                try
                {
                    $("#disk5_name").val(data.disks[4].name);
                }catch (e)
                { }
                try
                {
                    $("#disk6_name").val(data.disks[5].name);
                }catch (e)
                { }
                try
                {
                    $("#disk1_type").val(data.disks[0].type);
                }catch (e)
                { }
                try
                {
                    $("#disk2_type").val(data.disks[1].type);
                }catch (e)
                { }
                try
                {
                    $("#disk3_type").val(data.disks[2].type);
                }catch (e)
                { }
                try
                {
                    $("#disk4_type").val(data.disks[3].type);
                }catch (e)
                { }
                try
                {
                    $("#disk5_type").val(data.disks[4].type);
                }catch (e)
                { }
                try
                {
                    $("#disk6_type").val(data.disks[5].type);
                }catch (e)
                { }
                $("#ip").val(data.ip);
                $("#username").val(data.username);
                $("#password").val(data.password);
                $("#description").val(data.description);

                 if ($("#disk2_size").val() !== null && $("#disk2_size").val() !== undefined && $("#disk2_size").val() !== '')
                {
                    $("#disk2").show()
                    $("#disk2_size").removeAttr("disabled");
                    $("#disk2_name").removeAttr("disabled");
                    $("#disk2_type").removeAttr("disabled");
                }
                if ($("#disk3_size").val() !== null && $("#disk3_size").val() !== undefined && $("#disk3_size").val() !== '')
                {
                    $("#disk2").show()
                    $("#disk2_size").removeAttr("disabled");
                    $("#disk2_name").removeAttr("disabled");
                    $("#disk2_type").removeAttr("disabled");
                    $("#disk3").show()
                    $("#disk3_size").removeAttr("disabled");
                    $("#disk3_name").removeAttr("disabled");
                    $("#disk3_type").removeAttr("disabled");
                }
                if ($("#disk4_size").val() !== null && $("#disk4_size").val() !== undefined && $("#disk4_size").val() !== '')
                {
                    $("#disk4").show()
                    $("#disk4_size").removeAttr("disabled");
                    $("#disk4_name").removeAttr("disabled");
                    $("#disk4_type").removeAttr("disabled");
                    $("#disk2").show()
                    $("#disk2_size").removeAttr("disabled");
                    $("#disk2_name").removeAttr("disabled");
                    $("#disk2_type").removeAttr("disabled");
                    $("#disk3").show()
                    $("#disk3_size").removeAttr("disabled");
                    $("#disk3_name").removeAttr("disabled");
                    $("#disk3_type").removeAttr("disabled");
                }
                if ($("#disk5_size").val() !== null && $("#disk5_size").val() !== undefined && $("#disk5_size").val() !== '')
                {
                    $("#disk4").show()
                    $("#disk4_size").removeAttr("disabled");
                    $("#disk4_name").removeAttr("disabled");
                    $("#disk4_type").removeAttr("disabled");
                    $("#disk2").show()
                    $("#disk2_size").removeAttr("disabled");
                    $("#disk2_name").removeAttr("disabled");
                    $("#disk2_type").removeAttr("disabled");
                    $("#disk3").show()
                    $("#disk3_size").removeAttr("disabled");
                    $("#disk3_name").removeAttr("disabled");
                    $("#disk3_type").removeAttr("disabled");
                    $("#disk5").show()
                    $("#disk5_size").removeAttr("disabled");
                    $("#disk5_name").removeAttr("disabled");
                    $("#disk5_type").removeAttr("disabled");
                }
                if ($("#disk6_size").val() !== null && $("#disk6_size").val() !== undefined && $("#disk6_size").val() !== '')
                {
                    $("#disk4").show()
                    $("#disk4_size").removeAttr("disabled");
                    $("#disk4_name").removeAttr("disabled");
                    $("#disk4_type").removeAttr("disabled");
                    $("#disk2").show()
                    $("#disk2_size").removeAttr("disabled");
                    $("#disk2_name").removeAttr("disabled");
                    $("#disk2_type").removeAttr("disabled");
                    $("#disk3").show()
                    $("#disk3_size").removeAttr("disabled");
                    $("#disk3_name").removeAttr("disabled");
                    $("#disk3_type").removeAttr("disabled");
                    $("#disk5").show()
                    $("#disk5_size").removeAttr("disabled");
                    $("#disk5_name").removeAttr("disabled");
                    $("#disk5_type").removeAttr("disabled");
                    $("#disk6").show()
                    $("#disk6_size").removeAttr("disabled");
                    $("#disk6_name").removeAttr("disabled");
                    $("#disk6_type").removeAttr("disabled");
                    $("#add").hide()
                }
        });

         $("#new").click(function(){

            $("#disk2").hide()
            $("#disk3").hide()
            $("#disk4").hide()
            $("#disk5").hide()
            $("#disk6").hide()
            $("#disk2_size").attr("disabled","disabled")
            $("#disk3_size").attr("disabled","disabled")
            $("#disk4_size").attr("disabled","disabled")
            $("#disk5_size").attr("disabled","disabled")
            $("#disk6_size").attr("disabled","disabled")
            $("#disk2_name").attr("disabled","disabled")
            $("#disk3_name").attr("disabled","disabled")
            $("#disk4_name").attr("disabled","disabled")
            $("#disk5_name").attr("disabled","disabled")
            $("#disk6_name").attr("disabled","disabled")
            $("#disk2_type").attr("disabled","disabled")
            $("#disk3_type").attr("disabled","disabled")
            $("#disk4_type").attr("disabled","disabled")
            $("#disk5_type").attr("disabled","disabled")
            $("#disk6_type").attr("disabled","disabled")
            $("#add").show()
            $("#id").val("0");
            $("#name").val("");
            $("#poolid").val("");
            $("#poolname").val("");
            $("#cpu").val("");
            $("#memory").val("");
            $("#disk1_size").val("");
            $("#disk2_size").val("");
            $("#disk3_size").val("");
            $("#disk4_size").val("");
            $("#disk5_size").val("");
            $("#disk6_size").val("");
            $("#disk1_name").val("");
            $("#disk2_name").val("");
            $("#disk3_name").val("");
            $("#disk4_name").val("");
            $("#disk5_name").val("");
            $("#disk6_name").val("");
            $("#ip").val("");
            $("#username").val("");
            $("#password").val("");
            $("#description").val("");
          });


          $('#save').click(function(){
            var table = $('#sample_1').DataTable();
            if($("#formactivate").validate().form())

                $.ajax({
                    type: "POST",
                    url: "../computerresourcesave/",
                    data: $('#formactivate').serialize(),
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
             else
                alert("输入有误，请重新输入。");
         })

          $("#add").click(function(){

          if (!$("#disk5").is(":hidden"))
            {
                $("#disk6").show()
                $("#disk6_size").removeAttr("disabled");
                $("#disk6_name").removeAttr("disabled");
                $("#disk6_type").removeAttr("disabled");
                 $("#add").hide()
            }
            else if (!$("#disk4").is(":hidden"))
                {

                    $("#disk5").show()
                    $("#disk5_size").removeAttr("disabled");
                    $("#disk5_name").removeAttr("disabled");
                    $("#disk5_type").removeAttr("disabled");
                }
                else if (!$("#disk3").is(":hidden"))
            {
                $("#disk4").show()
                $("#disk4_size").removeAttr("disabled");
                $("#disk4_name").removeAttr("disabled");
                $("#disk4_type").removeAttr("disabled");
            }
            else if (!$("#disk2").is(":hidden"))
            {
                $("#disk3").show()
                $("#disk3_size").removeAttr("disabled");
                $("#disk3_name").removeAttr("disabled");
                $("#disk3_type").removeAttr("disabled");
            }
            else
            {
                $("#disk2").show()
                $("#disk2_size").removeAttr("disabled");
                $("#disk2_name").removeAttr("disabled");
                $("#disk2_type").removeAttr("disabled");
            }
         })



    } );