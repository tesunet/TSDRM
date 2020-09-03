function getframework(){
    $('#loading').show();
    $('#showdata').hide();
    $.ajax({
        type: 'POST',
        dataType: 'json',
        url: '../get_framework/',
        data: {
            "util":$('#util').val(),
        },
        success: function (data) {
                $('#loading').hide();
                $('#showdata').show();
                if (data.ret == 0) {
                    alert(data.data)
                } else {
                    $('#cs_host').text(data.data.commserve.host);
                    $('#cs_version').text(data.data.commserve.version);
                    $('#cs_sp').text(data.data.commserve.sp);
                    $('#cs_os').text(data.data.commserve.os);
                    $('#cs_net').text(data.data.commserve.net);
                    if(data.data.commserve.net=="中断"){
                        $("#cs_net").css("color","red");
                    }
                    $('#cs_apiport').text(data.data.commserve.apiport);
                    $('#cs_apiconnect').text(data.data.commserve.apiconnect);
                    if(data.data.commserve.apiconnect=="中断"){
                        $("#cs_apiconnect").css("color","red");
                    }
                    $('#cs_dbname').text(data.data.commserve.dbname);
                    $('#cs_dbconnect').text(data.data.commserve.dbconnect);
                    if(data.data.commserve.dbconnect=="中断"){
                        $("#cs_dbconnect").css("color","red");
                    }

                    $('#cs_memtotal').text("获取中");
                    $('#cs_memutilization').text("获取中");
                    $('#cs_swaptotal').text("获取中");
                    $('#cs_swaputilization').text("获取中");
                    $('#cs_cpuloadpercentage').text("获取中");
                    $('#cs_disktotal').text("获取中");
                    $('#cs_diskutilization').text("获取中");

                    for (var i = 0; i < data.data.ma.length; i++) {
                        var result="";
                        result +="<tr>";
                        result +="<td>" + data.data.ma[i]["DisplayName"] + "</td>";
                        result +="<td>" + data.data.ma[i]["SWVersion"] + "</td>";
                        result +="<td>" + data.data.ma[i]["ServicePack"] + "</td>";
                        result +="<td>" + data.data.ma[i]["OSName"] + "</td>";
                        if(data.data.ma[i]["net"]=="中断")
                            result +="<td style='color: red'>" + data.data.ma[i]["net"] + "</td>";
                        else
                            result +="<td>" + data.data.ma[i]["net"] + "</td>";
                        if(data.data.ma[i]["Offline"]=="离线")
                            result +="<td style='color: red'>" + data.data.ma[i]["Offline"] + "</td>";
                        else
                            result +="<td>" + data.data.ma[i]["Offline"] + "</td>";
                        result +="<td>" + data.data.ma[i]["TotalLibraries"] + "</td>";
                        result +="<td>" + data.data.ma[i]["OfflineLibraries"] + "</td>";
                        result +="<td>" + data.data.ma[i]["TotalSpaceMB"] + "TB</td>";
                        result +="<td>" + data.data.ma[i]["Percent"] + "%</td>";
                        result +="<td>" + data.data.ma[i]["TotalFreeSpaceMB"] + "TB</td>";
                        result +="<td>" + data.data.ma[i]["SpaceReserved"] + "TB</td>";
                        result +="<td>" + data.data.ma[i]["CapacityAvailable"] + "TB</td>";

                        result +="</tr>";
                        $("#matable tbody").append(result);
                    }
                    if(data.data.commserve.net=="正常") {
                        $.ajax({
                            type: 'POST',
                            dataType: 'json',
                            url: '../get_csinfo/',
                            data: {
                                "util": $('#util').val(),
                            },
                            success: function (data1) {
                                if (data.ret == 0) {
                                    alert(data1.data)
                                } else {

                                    $('#cs_memtotal').text(data1.data.commserve.memtotal);
                                    $('#cs_memutilization').text(data1.data.commserve.memutilization);
                                    $('#cs_swaptotal').text(data1.data.commserve.swaptotal);
                                    $('#cs_swaputilization').text(data1.data.commserve.swaputilization);
                                    $('#cs_cpuloadpercentage').text(data1.data.commserve.cpuloadpercentage);
                                    $('#cs_disktotal').text(data1.data.commserve.disktotal);
                                    $('#cs_diskutilization').text(data1.data.commserve.diskutilization);
                                }
                            }
                        });
                    }
                    else{
                         $('#cs_memtotal').text("无法获取");
                        $('#cs_memutilization').text("无法获取");
                        $('#cs_swaptotal').text("无法获取");
                        $('#cs_swaputilization').text("无法获取");
                        $('#cs_cpuloadpercentage').text("无法获取");
                        $('#cs_disktotal').text("无法获取");
                        $('#cs_diskutilization').text("无法获取");
                    }
                }
        }
    });
}

$(document).ready(function () {
    getframework();
    $("#util").change(function () {
        getframework();
    });
});








