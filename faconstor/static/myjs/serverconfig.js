var Activate = function () {


    var handleActivate = function () {


        $('.activate-form').validate({
            errorElement: 'span', //default input error message container
            errorClass: 'help-block', // default input error message class
            focusInvalid: false, // do not focus the last invalid input
            ignore: "",
            rules: {
                email: {
                    required: true,
                    email: true
                },
                phone: {
                    required: true,
                    phone: true
                },

                username: {
                    required: true
                },
                fullname: {
                    required: true
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


    };

    return {
        //main function to initiate the module
        init: function () {

            handleActivate();
        }
    };

}();

jQuery(document).ready(function () {
    Activate.init();


});

$('#activatebtn').click(function () {
    if ($("#formactivate").validate().form())
        $.ajax({
            type: "POST",
            url: "../serverconfigsave/",
            data: $('#formactivate').serialize(),
            success: function (data) {
                alert(data);
            },
            error: function (e) {
                alert("保存失败，请于客服联系。");
            }
        });
    else
        alert("输入有误，请重新输入。");
});