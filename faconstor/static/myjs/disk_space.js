$(document).ready(function () {
    $("#loading").show();

    function getDiskSpace(utils_manage_id) {
        $.ajax({
            type: 'POST',
            dataType: 'json',
            url: '../get_disk_space/',
            data: {
                'utils_manage_id': utils_manage_id
            },
            success: function (data) {
                if (data.status == 1) {
                    var disk_table = "";
                    var disk_space = data.data;

                    var pre_display_name = "";
                    var pre_library_name = "";

                    for (var i = 0; i < disk_space.length; i++) {
                        var display_name_hidden = "";
                        var library_name_hidden = "";

                        if (pre_display_name == disk_space[i]["DisplayName"]) {
                            display_name_hidden = "display:none";
                        }
                        if (pre_display_name == disk_space[i]["DisplayName"] && pre_library_name == disk_space[i]["LibraryName"]) {
                            library_name_hidden = "display:none";
                        }

                        $("tbody").append(
                            '<tr>' +
                            '<td rowspan="' + disk_space[i].display_name_rowspan + '" style="vertical-align:middle; ' + display_name_hidden + '">' + (i + 1) + '</td>' +
                            '<td rowspan="' + disk_space[i].display_name_rowspan + '" style="vertical-align:middle; ' + display_name_hidden + '">' + disk_space[i]["DisplayName"] + '</td>' +
                            '<td rowspan="' + disk_space[i].library_name_rowspan + '" style="vertical-align:middle; ' + library_name_hidden + '">' + disk_space[i]["LibraryName"] + '</td>' +
                            '<td style="vertical-align:middle">' + disk_space[i]["MountPathName"] + '</td>' +
                            '<td style="vertical-align:middle">' + disk_space[i]["CapacityAvailable"] + '</td>' +
                            '<td style="vertical-align:middle">' + disk_space[i]["SpaceReserved"] + '</td>' +
                            '<td style="vertical-align:middle">' + disk_space[i]["TotalSpaceMB"] + '</td>' +
                            '<td style="vertical-align:middle">' + disk_space[i]["LastBackupTime"] + '</td>' +
                            '<td style="vertical-align:middle">' + disk_space[i]["Offline"] + '</td>' +
                            '<td style="vertical-align:middle"><button id="edit" title="图表" data-toggle="modal" data-target="#static" class="btn btn-xs btn-primary" type="button"><i class="fa fa-bar-chart"></i></button></td>' +
                            '</tr>'
                        );

                        pre_display_name = disk_space[i]["DisplayName"]
                        pre_library_name = disk_space[i]["LibraryName"]
                    }
                    $("#loading").hide();
                } else {
                    alert(data.info);
                }
            }
        });
    }

    getDiskSpace($('#utils_manage').val());

    $('#utils_manage').change(function () {
        $("tbody").empty();
        $("#loading").show();
        getDiskSpace($(this).val());
    });
});