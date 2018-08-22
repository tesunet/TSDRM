var property={
	width:document.body.clientWidth-380,
	height:450,
	toolBtns:["start round","end round","task","node","fork","join","complex"],
	haveHead:true,
	headBtns:["save","reload","new","undo","redo"],//如果haveHead=true，则定义HEAD区的按钮
	haveTool:true,
	haveGroup:true,
	useOperStack:true
};
var remark={
	cursor:"选择指针",
	direct:"结点连线",
	start:"任务开始",
	"end":"任务结束",
	"task":"人工任务",
	node:"自动任务",
	fork:"并行起点",
	"join":"并行终点",
	"complex":"子流程",
	group:"区域",
	save:"保存",
	undo:"撤销",
	redo:"重做",
	reload:"验证",
	"new":"发布",
};
var demo;
var recoverydata;

jQuery(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});

$(function(){
	demo=$.createGooFlow($("#demo"),property);
	demo.setNodeRemarks(remark);
    $.ajax({
            type: "GET",
            dataType: 'json',
            url: "../../getprocess/",
            data:
                {
                  id:$("#pid").val(),
                },
            success:function(data){
                    demo.loadData(data.data);
            },
            error : function(e){
                 alert("页面出现错误，请于管理员联系。");
                }
      });
   $.ajax({
        type: "POST",
        url: "../../manualrecoverydata/",
        dataType: "json",
        success:function(data){
            recoverydata=data.data;
            $("#recoveryclient").empty();
            for (var i=0;i<recoverydata.length;i++){
                 $("#recoveryclient").append("<option value='" + recoverydata[i]["id"] + "'>" + recoverydata[i]["clientName"] + "</option>");
            }
        },
      });


	demo.onItemFocus=function(id,type){
	     $("#id").val(id)
	      $("#type").val(type)
	    if(type=='node')
	    {
	        $("#divline").hide()
            $("#divnode").show()
            $("#code").val(demo.$nodeData[id].code)
            $("#name").val(demo.$nodeData[id].name)
            $("#nodetype").val(demo.$nodeData[id].nodetype)
            if(demo.$nodeData[id].skip)
            {
                if (demo.$nodeData[id].skip=="1")
                {
                   $('input:radio[name=radio1]')[0].checked = true;
                }
                else
                {
                    $('input:radio[name=radio1]')[1].checked = true;
                }
            }
            else
            {
                $('input:radio[name=radio1]')[1].checked = true;
            }
            if(demo.$nodeData[id].group)
            {
                try{
                    $("#group").val(demo.$nodeData[id].group)

                }
                catch(e)
                {
                }
                try{
                    $("#process").val(demo.$nodeData[id].group)

                }
                catch(e)
                {
                }
                $(".select2, .select2-multiple").select2({
                    width: null
                });

            }
            if(demo.$nodeData[id].time)
            {
                $("#time").val(demo.$nodeData[id].time)
            }
            else
            {
                $("#time").val("")
            }
            var myscripts=demo.$nodeData[id].stepscript
            $("#se_1").empty();
            for (var key in myscripts) {
                 $("#se_1").append("<option id='" + key.toString() + "'>" +myscripts[key].code +"</option>");
            }



            if(demo.$nodeData[id].type=='start round' || demo.$nodeData[id].type=='end round' || demo.$nodeData[id].type=='fork' ||demo.$nodeData[id].type=='join')
            {
                $("#divskip").hide();
                $("#divgroup").hide();
                $("#divprocess").hide();
                $("#divtime").hide();
                 $("#divsvript").hide();
                 $("#divtype").hide();
                 $("#divcommvault").hide();

            }
            else if(demo.$nodeData[id].type=='task' || demo.$nodeData[id].type=='node')
            {
                $("#divskip").show();
                $("#divgroup").show();
                $("#divprocess").hide();
                $("#divtime").show();
                $("#divsvript").show();
                $("#divtype").show();
                $("#divcommvault").hide();
                if(demo.$nodeData[id].type=='task')
                 {
                     if ($("#nodetype").val()=="commvault")
                    {
                        $("#divsvript").hide();
                        $("#divcommvault").show();
                        try{
                            $("#recoveryclient").val(demo.$nodeData[id].recoveryclient)

                        }
                        catch(e)
                        {
                        }
                        for (var i=0;i<recoverydata.length;i++)
                        {
                            if ($("#recoveryclient").val()==recoverydata[i]["id"])
                            {
                                $("#recoverytype").empty();
                                if(recoverydata[i]["type"]=="VMWARE")
                                    $("#recoverytype").append("<option value='VMWARE'>VMWARE</option>");
                                else
                                {
                                    for (var j=0;j<recoverydata[i]["agentType"].length;j++){
                                        if(recoverydata[i]["agentType"][j]!="Virtual Server" & recoverydata[i]["agentType"][j]!="VMWARE")
                                            $("#recoverytype").append("<option value='" + recoverydata[i]["agentType"][j] + "'>" + recoverydata[i]["agentType"][j] + "</option>");
                                     }
                                 }
                                try{
                                    $("#recoverytype").val(demo.$nodeData[id].recoverytype)

                                }
                                catch(e)
                                {
                                }
                                break;
                            }

                        }

                     }
                 }

                 if(demo.$nodeData[id].type=='node')
                 {
                    $("#divtype").hide();
                    $("#nodetype").val()=="普通任务"
                 }
            }
            else if(demo.$nodeData[id].type=='complex')
            {
                $("#divskip").hide();
                $("#divgroup").hide();
                $("#divprocess").show();
                $("#divtime").show();
                $("#divsvript").hide();
                $("#divtype").hide();
                $("#divcommvault").hide();
            }

        }
        else if(type=='line')
        {
            $("#divline").show()
            $("#divnode").hide()
            $("#linename").val(demo.$lineData[id].name)
            if(demo.$lineData[id].formula)
                $("#lineformula").val(demo.$lineData[id].formula)
            else
                $("#lineformula").val("")
        }

	    return true;}

	demo.onItemBlur=function(id,type){
        if(type=='node')
	    {
            demo.$nodeData[id].code = $("#code").val()
            demo.$nodeData[id].name = $("#name").val()
            demo.$nodeData[id].skip = $("input:radio[name='radio1']:checked").val() ;
            if(demo.$nodeData[id].type=='complex')
                demo.$nodeData[id].group = $("#process").val();
            else
                demo.$nodeData[id].group = $("#group").val();
            demo.$nodeData[id].time = $("#time").val()
            demo.$nodeData[id].nodetype = $("#nodetype").val()
            if(demo.$nodeData[id].nodetype=='commvault')
            {
                demo.$nodeData[id].recoveryclient =$("#recoveryclient").val()
                demo.$nodeData[id].recoverytype = $("#recoverytype").val()
            }
            else
            {
                demo.$nodeData[id].recoveryclient =""
                demo.$nodeData[id].recoverytype = ""
             }


            $("#"+id +" table tr:first td:nth-child(2)").text("h");

            if(demo.$nodeData[id].type=='start round' || demo.$nodeData[id].type=='end round')
            {
                $("#"+id +" div:nth-child(3)").text($("#name").val());
            }
            else
            {
                $("#"+id +" table tr:first td:nth-child(2)").text($("#name").val());
            }

        }
        else if(type=='line')
        {
            demo.$lineData[id].name = $("#linename").val();
            demo.$lineData[id].formula = $("#lineformula").val();
            $("#"+id + " text").text( $("#linename").val());
        }
	    return true;
    }

    demo.onBtnSaveClick= function(){
    if(confirm("保存操作会将流程重置为未发布状态，确定要保存该流程吗？")){
            var id = $("#id").val()
            var type = $("#type").val()
            if(type=='node')
            {
                demo.$nodeData[id].code = $("#code").val()
                demo.$nodeData[id].name = $("#name").val()
                demo.$nodeData[id].skip = $("input:radio[name='radio1']:checked").val() ;
                if(demo.$nodeData[id].type=='complex')
                    demo.$nodeData[id].group = $("#process").val();
                else
                    demo.$nodeData[id].group = $("#group").val();
                demo.$nodeData[id].time = $("#time").val()
                demo.$nodeData[id].nodetype = $("#nodetype").val()
                if(demo.$nodeData[id].nodetype=='commvault')
                {
                    demo.$nodeData[id].recoveryclient =$("#recoveryclient").val()
                    demo.$nodeData[id].recoverytype = $("#recoverytype").val()
                }
                else
                {
                    demo.$nodeData[id].recoveryclient =""
                    demo.$nodeData[id].recoverytype = ""
                 }

                $("#"+id +" table tr:first td:nth-child(2)").text("h");

                if(demo.$nodeData[id].type=='start round' || demo.$nodeData[id].type=='end round')
                {
                    $("#"+id +" div:nth-child(3)").text($("#name").val());
                }
                else
                {
                    $("#"+id +" table tr:first td:nth-child(2)").text($("#name").val());
                }

            }
            else if(type=='line')
            {
                demo.$lineData[id].name = $("#linename").val();
                demo.$lineData[id].formula = $("#lineformula").val();
                $("#"+id + " text").text( $("#linename").val());
            }
            $.ajax({
            type: "POST",
            url: "../../processdrawsave/",
            data:JSON.stringify(demo.exportData()),
            success:function(data){
                    alert(data);
            },
            error : function(e){
                 alert("页面出现错误，请于管理员联系。");
                }
      });
      }
    }

    demo.onFreshClick= function(){
    if(confirm("验证前请先保存修改，是否已保存？")){
        $.ajax({
            type: "POST",
            url: "../../processdrawtest/",
            data:{
                  id:$("#pid").val(),
                },
            success:function(data){
                    alert(data);
            },
            error : function(e){
                 alert("页面出现错误，请于管理员联系。");
                }
      });
    }}
    demo.onBtnNewClick= function(){
    if(confirm("发布前请先保存并验证，是否执行发布操作？")){
        $.ajax({
            type: "POST",
            url: "../../processdrawrelease/",
            data:{
                  id:$("#pid").val(),
                },
            success:function(data){
                    alert(data);
            },
            error : function(e){
                 alert("页面出现错误，请于管理员联系。");
                }
      });
    }}

     demo.onItemDel= function(){
      $("#type").val("")
      $("#divline").hide()
    $("#divnode").hide()
    return true;
    }

    $('#se_1').contextmenu({
        target: '#context-menu2',
        onItem: function (context, e) {
            if($(e.target).text()=="新增")
            {
                $("#scriptid").val("0");
                $("#scriptcode").val("");
                $("#scriptip").val("");
                $("#scriptport").val("");
                $("#scriptusername").val("");
                $("#scriptpassword").val("");
                $("#scriptfilename").val("");
                $("#scriptparamtype").val("无");
                $("#scriptparam").val("");
                $("#scriptscriptpath").val("");
                $("#scriptrunpath").val("");
                $("#scriptcommand").val("");
                $("#scriptmaxtime").val("");
                $("#scripttime").val("");
                document.getElementById("edit").click();
            }
            if($(e.target).text()=="修改")
             {
              if ($("#se_1").find('option:selected').length==0)
                alert("请选择要修改的脚本。");
                else
                {
                    if ($("#se_1").find('option:selected').length>1)
                         alert("修改时请不要选择多条记录。");
                    else
                    {
                        var myscript = demo.$nodeData[$("#id").val()].stepscript[ $("#se_1").find('option:selected').attr('id')]
                        $("#scriptid").val( $("#se_1").find('option:selected').attr('id'));
                        $("#scriptcode").val( myscript.code);
                        $("#scriptip").val( myscript.ip);
                        $("#scriptport").val( myscript.port);
                        $("#scripttype").val(myscript.type);
                        $("#scriptruntype").val(myscript.runtype);
                        $("#scriptusername").val( myscript.username);
                        $("#scriptpassword").val( myscript.password);
                        $("#scriptfilename").val( myscript.filename);
                        $("#scriptparamtype").val( myscript.paramtype);
                        $("#scriptparam").val( myscript.param);
                        $("#scriptscriptpath").val(myscript.scriptpath);
                        $("#scriptrunpath").val( myscript.runpath);
                        $("#scriptcommand").val("cd " + $("#scriptscriptpath").val() + ";" + $("#scriptrunpath").val() + "/" + $("#scriptfilename").val() + " " + $("#scriptparam").val());
                        $("#scriptmaxtime").val(myscript.maxtime);
                        $("#scripttime").val( myscript.time);

                        document.getElementById("edit").click();}
                }

             }

             if($(e.target).text()=="删除"){
               if ($("#se_1").find('option:selected').length==0)
                    alert("请选择要删除的脚本。");
                else
                {
                if(confirm("确定要删除该脚本吗？")){
                    $.ajax({
                            type: "POST",
                            url: "../../scriptdel/",
                            data:
                                {
                                  id:$("#se_1").find('option:selected').attr("id").replace("script_",""),
                                },
                            success:function(data){
                            if(data==1)
                            {
                                $("#se_1").find('option:selected').remove();
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
                }
            }

        }
      });

    $('#save').click(function(){
              $.ajax({
                    type: "POST",
                    dataType: 'json',
                    url: "../../processscriptsave/",
                    data:
                        {
                            processid:$("#pid").val(),
                            pid:$("#id").val().replace("demo_node_",""),
                            id:$("#scriptid").val().replace("script_",""),
                            code:$("#scriptcode").val(),
                            ip:$("#scriptip").val(),
                            port:$("#scriptport").val(),
                            type:$("#scripttype").val(),
                            runtype:$("#scriptruntype").val(),
                            username:$("#scriptusername").val(),
                            password:$("#scriptpassword").val(),
                            filename:$("#scriptfilename").val(),
                            paramtype:$("#scriptparamtype").val(),
                            param:$("#scriptparam").val(),
                            scriptpath:$("#scriptscriptpath").val(),
                            runpath:$("#scriptrunpath").val(),
                            maxtime:$("#scriptmaxtime").val(),
                            time:$("#scripttime").val(),
                        },
                    success:function(data){
                            var myres = data["res"];
                            var mydata = data["data"];
                            if(myres=="新增成功。")
                            {
                                $("#scriptid").val(data["data"]);
                                $("#se_1").append("<option id='" + "script_" + mydata + "'>" + $("#scriptcode").val() +"</option>");
                                var newscript = {code : $("#scriptcode").val(),ip : $("#scriptip").val(),port : $("#scriptport").val(),type : $("#scripttype").val(),runtype : $("#scriptruntype").val()
                                ,username : $("#scriptusername").val(),password : $("#scriptpassword").val(),filename : $("#scriptfilename").val(),paramtype : $("#scriptparamtype").val()
                                ,param : $("#scriptparam").val(),scriptpath : $("#scriptscriptpath").val(),runpath : $("#scriptrunpath").val()
                                ,maxtime : $("#scriptmaxtime").val(),time : $("#scripttime").val()}
                                demo.$nodeData[$("#id").val()].stepscript["script_" + $("#scriptid").val()] = newscript
                                $('#static01').modal('hide');                            }
                            if(myres=="修改成功。")
                            {
                                $("#"+$("#scriptid").val()).text($("#scriptcode").val())
                                demo.$nodeData[$("#id").val()].stepscript[$("#scriptid").val()].code = $("#scriptcode").val()
                                demo.$nodeData[$("#id").val()].stepscript[$("#scriptid").val()].ip = $("#scriptip").val()
                                demo.$nodeData[$("#id").val()].stepscript[$("#scriptid").val()].port = $("#scriptport").val()
                                demo.$nodeData[$("#id").val()].stepscript[$("#scriptid").val()].type = $("#scripttype").val()
                                demo.$nodeData[$("#id").val()].stepscript[$("#scriptid").val()].runtype = $("#scriptruntype").val()
                                demo.$nodeData[$("#id").val()].stepscript[$("#scriptid").val()].username = $("#scriptusername").val()
                                demo.$nodeData[$("#id").val()].stepscript[$("#scriptid").val()].password = $("#scriptpassword").val()
                                demo.$nodeData[$("#id").val()].stepscript[$("#scriptid").val()].filename = $("#scriptfilename").val()
                                demo.$nodeData[$("#id").val()].stepscript[$("#scriptid").val()].paramtype = $("#scriptparamtype").val()
                                demo.$nodeData[$("#id").val()].stepscript[$("#scriptid").val()].param = $("#scriptparam").val()
                                demo.$nodeData[$("#id").val()].stepscript[$("#scriptid").val()].scriptpath = $("#scriptscriptpath").val()
                                demo.$nodeData[$("#id").val()].stepscript[$("#scriptid").val()].runpath = $("#scriptrunpath").val()
                                demo.$nodeData[$("#id").val()].stepscript[$("#scriptid").val()].maxtime = $("#scriptmaxtime").val()
                                demo.$nodeData[$("#id").val()].stepscript[$("#scriptid").val()].time = $("#scripttime").val()
                                $('#static01').modal('hide');
                            }
                            alert(myres);
                    },
                    error : function(e){
                         alert("页面出现错误，请于管理员联系。");
                        }
              });
        })

    $('#scriptfilename').change(function(){
        $("#scriptcommand").val("cd " + $("#scriptscriptpath").val() + ";" + $("#scriptrunpath").val() + "/" + $("#scriptfilename").val() + " " + $("#scriptparam").val());
    })
    $('#scriptscriptpath').change(function(){
        $("#scriptcommand").val("cd " + $("#scriptscriptpath").val() + ";" + $("#scriptrunpath").val() + "/" + $("#scriptfilename").val() + " " + $("#scriptparam").val());
    })
    $('#scriptrunpath').change(function(){
        $("#scriptcommand").val("cd " + $("#scriptscriptpath").val() + ";" + $("#scriptrunpath").val() + "/" + $("#scriptfilename").val() + " " + $("#scriptparam").val());
    })
    $('#scriptparam').change(function(){
        $("#scriptcommand").val("cd " + $("#scriptscriptpath").val() + ";" + $("#scriptrunpath").val() + "/" + $("#scriptfilename").val() + " " + $("#scriptparam").val());
    })
    $("#divtype").change(function(){
        $("#divsvript").show();
        $("#divcommvault").hide();
        if ($("#nodetype").val()=="commvault")
        {
            $("#divsvript").hide();
            $("#divcommvault").show();
            for (var i=0;i<recoverydata.length;i++)
            {
                if ($("#recoveryclient").val()==recoverydata[i]["id"])
                {
                    $("#recoverytype").empty();
                    if(recoverydata[i]["type"]=="VMWARE")
                        $("#recoverytype").append("<option value='VMWARE'>VMWARE</option>");
                    else
                    {
                        for (var j=0;j<recoverydata[i]["agentType"].length;j++){
                            if(recoverydata[i]["agentType"][j]!="Virtual Server" & recoverydata[i]["agentType"][j]!="VMWARE")
                                $("#recoverytype").append("<option value='" + recoverydata[i]["agentType"][j] + "'>" + recoverydata[i]["agentType"][j] + "</option>");
                         }
                     }
                 }
            }
         }
    })
    $("#recoveryclient").change(function(){
        for (var i=0;i<recoverydata.length;i++)
        {
            if ($("#recoveryclient").val()==recoverydata[i]["id"])
            {
                $("#recoverytype").empty();
                if(recoverydata[i]["type"]=="VMWARE")
                    $("#recoverytype").append("<option value='VMWARE'>VMWARE</option>");
                else
                {
                    for (var j=0;j<recoverydata[i]["agentType"].length;j++){
                        if(recoverydata[i]["agentType"][j]!="Virtual Server" & recoverydata[i]["agentType"][j]!="VMWARE")
                            $("#recoverytype").append("<option value='" + recoverydata[i]["agentType"][j] + "'>" + recoverydata[i]["agentType"][j] + "</option>");
                     }
                 }
                 break;
             }
        }
    })

    $('#sample_1').dataTable( {
            "bAutoWidth": true,
            "bSort": false,
            "bProcessing": true,
            "ajax": "../../scriptdata/",
            "columns": [
                { "data": "id" },
                { "data": "code" },
                { "data": "ip" },
                { "data": "port" },
                { "data": "type" },
                { "data": "runtype" },
                { "data": "filename" },
                { "data": "time" },
                { "data": "username" },
                { "data": "password" },
                { "data": "paramtype" },
                { "data": "param" },
                { "data": "scriptpath" },
                { "data": "runpath" },
                { "data": "maxtime" },
                { "data": null }
            ],

            "columnDefs": [{
                    "targets": -1,
                    "data": null,
                    "defaultContent": "<button  id='select' title='选择'  class='btn btn-xs btn-primary' type='button'><i class='fa fa-check'></i></button>"
            },{
              "targets": [-2],
                "visible": false
            } ,{
                  "targets": [-3],
                    "visible": false
            } ,{
                  "targets": [-4],
                    "visible": false
            } ,{
                  "targets": [-5],
                    "visible": false
            } ,{
                  "targets": [-6],
                    "visible": false
            } ,{
                  "targets": [-7],
                    "visible": false
            } ,{
                  "targets": [-8],
                    "visible": false
            } ,{
                  "targets": [-9],
                    "visible": false
            },{
                  "targets": [0],
                    "visible": false
            }],
            "oLanguage": {
            "sLengthMenu": "每页显示 _MENU_ 条记录",
            "sZeroRecords": "抱歉， 没有找到",
            "sInfo": "从 _START_ 到 _END_ /共 _TOTAL_ 条数据",
            "sInfoEmpty": "没有数据",
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
                $("#scriptcode").val( data.code);
                $("#scriptip").val( data.ip);
                $("#scriptport").val( data.port);
                $("#scripttype").val(data.type);
                $("#scriptruntype").val(data.runtype);
                $("#scriptusername").val( data.username);
                $("#scriptpassword").val( data.password);
                $("#scriptfilename").val( data.filename);
                $("#scriptparamtype").val( data.paramtype);
                $("#scriptparam").val( data.param);
                $("#scriptscriptpath").val(data.scriptpath);
                $("#scriptrunpath").val( data.runpath);
                $("#scriptcommand").val("cd " + $("#scriptscriptpath").val() + ";" + $("#scriptrunpath").val() + "/" + $("#scriptfilename").val() + " " + $("#scriptparam").val());
                $("#scriptmaxtime").val(data.maxtime);
                $("#scripttime").val( data.time);
                $('#static1').modal('hide');
        });


});


