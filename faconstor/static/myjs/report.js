    $(document).ready(function() {
        $('#sample_1').dataTable( {
            "bAutoWidth": true,
            "bSort": false,
            "bProcessing": true,
            "ajax": "../reportdata?client=" + $('#client').val() + "&type=" + $('#type').val() + "&startdate=" + $('#startdate').val() + "&enddate=" + $('#enddate').val(),
            "columns": [
                { "data": "jobid" },
                { "data": "clientname" },
                { "data": "backupset" },
                { "data": "idataagent" },
                { "data": "backuplevel" },
                { "data": "startdate" },
                { "data": "enddate" },
                { "data": "jobstatus" },
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
        $('#startdate').datetimepicker({
            autoclose:true,
            minView: "month",
            format:'yyyy-mm-dd',
            });
        $('#enddate').datetimepicker({
            autoclose:true,
            minView: "month",
            format:'yyyy-mm-dd',
            });
        $('#cx').click(function(){

            var table = $('#sample_1').DataTable();
            table.ajax.url("../reportdata?client=" + $('#client').val() + "&type=" + $('#type').val() + "&startdate=" + $('#startdate').val() + "&enddate=" + $('#enddate').val()).load();
        })


    });

