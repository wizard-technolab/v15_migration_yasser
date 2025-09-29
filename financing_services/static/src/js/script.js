// form2 validation
// var isValid = true
// const phone_numbers = document.getElementsByClassName('phone_input');
// console.log("phone numbers: ",phone_numbers)
// for (var i = 0; i < phone_numbers.length; i++) {
//     console.log(phone_numbers.item(i));
//     if (isNumerics(phone_numbers.item(i).value) && phone_numbers.item(i).value.length == 10){
//         console.log("success, big one")
//     }
//     else{
//         SetError(phone_numbers.item(i), 'Invalid phone number')
//         isValid = false;
//     }
//  };
// const national_ids = document.getElementsByClassName('id_number_v');
// console.log("National Id's: ",national_ids)
// for (var i = 0; i < national_ids.length; i++) {
//     console.log(national_ids.item(i));
//     if (isNumerics(national_ids.item(i).value) && national_ids.item(i).value.length == 10){
//         console.log("success, big one")
//     }
//     else{
//         SetError(national_ids.item(i), 'Invalid Id Number')
//         isValid = false;
//     }
// }
// const amounts = document.getElementsByClassName('amount_v');
// console.log("Amounts: ",amounts)
// for (var i = 0; i < amounts.length; i++) {
//     console.log(amounts.item(i));
//     if (isNumeric(amounts.item(i).value)){
//         console.log("success, big one")
//         amounts.item(i).value = parseFloat(amounts.item(i).value);
//     }
//     else{
//         SetError(amounts.item(i), 'Invalid Amount')
//         isValid = false;
//     }
// }


// if (isValid != true){
//     return false
// }
// end of the comment


odoo.define('financing_services.script', function(require) {
    $(document).ready(function() {
        var rpc = require('web.rpc');
        var shownname = document.querySelector(".shown_name");

        $('form#finance-app-otp').on('submit', function(e) {
            e.preventDefault();
            let data = new FormData(this);
            window.dataz = data;
            $.ajax({
                url: "https://otp.absher.sa/AbsherOTPService",
                data: data,
                method: 'post',
                cache: false,
                contentType: false,
                enctype: 'multipart/form-data',
                dataType: 'xml',
                processData: false,
                beforeSend: function() {
                 console.log("loading that now");
                        $('#modalLoader').modal('show');
                },
                success: function(response) {
                    if(response['status'] == true){
                        console.log("success: ",response);
//                        shownname.innerHTML = ' ';
//                        formnumber++;
//                        updateform();
//                        var url = '/printonsuccess/' + response['record_id'] + '/crm.lead' + '/' + 2
//                        window.location.href = url;
//                        window.location.replace(url);
                    }
                    else{
                        console.log("error: ",response['message']);
                        alert(response['message'])
                        return false;
                    }
                },
                error: function(error) {
                    console.log(error)
                }
            });
            return false;
        });

        $('form#finance-app-form').on('submit', function(e) {
            e.preventDefault();
            let data = new FormData(this);
            window.dataz = data;
            $.ajax({
                url: "api/form2",
                data: data,
                method: 'put',
                cache: false,
                contentType: false,
                enctype: 'multipart/form-data',
                dataType: 'json',
                processData: false,
                beforeSend: function() {
                 console.log("loading that now");
                        $('#modalLoader').modal('show');
                },
                success: function(response) {                    
                    if(response['status'] == true){
                        console.log("success: ",response);
                        shownname.innerHTML = ' ';
                        formnumber++;
                        updateform();
                        var url = '/printonsuccess/' + response['record_id'] + '/crm.lead' + '/' + 2
                        window.location.href = url;
                        window.location.replace(url);
                    }
                    else{
                        console.log("error: ",response['message']);
                        alert(response['message'])
                        return false;
                    }
                },
                error: function(error) {
                    console.log(error)
                }
            });
            return false;
        });

        $('form#health-form').on('submit', function(e) {
            e.preventDefault();
            let data = new FormData(this);
            window.dataz = data;
            $.ajax({
                url: "api/form3",
                data: data,
                method: 'put',
                cache: false,
                contentType: false,
                enctype: 'multipart/form-data',
                dataType: 'json',
                processData: false,
                beforeSend: function() {},
                success: function(response) {
                    console.log(response);
                    shownname.innerHTML = ' ';
                    formnumber++;
                    updateform();
                    var url = '/printonsuccess/' + response['record_id'] + '/health.declaration' + '/' + 3
                    window.location.href = url;
                    window.location.replace(url);
                },
                error: function(error) {
                    console.log(error);
                }
            });
            return false;
        });

        $('form#hospital-quotation-form').on('submit', function(e) {
            e.preventDefault();
            let data = new FormData(this);
            window.dataz = data;
            var isValid = true
            var validate_inputs = document.querySelectorAll(".main.active input");
            validate_inputs.forEach(function(vaildate_input) {
                vaildate_input.classList.remove('is-invalid');
            });
            const phone_numbers = document.getElementsByClassName('phone_input');
            console.log("phone numbers: ",phone_numbers)
            for (var i = 0; i < phone_numbers.length; i++) {
                console.log(phone_numbers.item(i));
                if (isNumerics(phone_numbers.item(i).value) && phone_numbers.item(i).value.length == 10){
                    console.log("success, big one")
                }
                else{
                    SetError(phone_numbers.item(i), 'Invalid phone number')
                    isValid = false;
                }
             };
            const national_ids = document.getElementsByClassName('id_number_v');
            console.log("National Id's: ",national_ids)
            for (var i = 0; i < national_ids.length; i++) {
                console.log(national_ids.item(i));
                if (isNumerics(national_ids.item(i).value) && national_ids.item(i).value.length == 10){
                    console.log("success, big one")
                }
                else{
                    SetError(national_ids.item(i), 'Invalid Id Number')
                    isValid = false;
                }
            }
            const amounts = document.getElementsByClassName('amount_v');
            console.log("Amounts: ",amounts)
            for (var i = 0; i < amounts.length; i++) {
                console.log(amounts.item(i));
                if (isNumeric(amounts.item(i).value)){
                    console.log("success, big one")
                    amounts.item(i).value = parseFloat(amounts.item(i).value);
                }
                else{
                    SetError(amounts.item(i), 'Invalid Amount')
                    isValid = false;
                }
            }
            const names = document.getElementsByClassName('name_v');
            console.log("names: ",names)
            for (var i = 0; i < names.length; i++) {
                console.log(names.item(i));
                if (isName(names.item(i).value)){
                    console.log("success, big one")
                    names.item(i).classList.remove("is-invalid");
                }
                else{
                    SetError(names.item(i), 'Invalid name')
                    isValid = false;
                }
            }
            var validate_inputs_required = document.querySelectorAll(".main.active .required");
            validate_inputs_required.forEach(function(vaildate_input) {
                if (vaildate_input.value.length == 0) {
                    isValid = false;
                    vaildate_input.classList.add('is-invalid');
                }
            });
            var validate_email_values = document.querySelectorAll(".main.active .email_v");
            validate_email_values.forEach(function(validate_email_values){
                validate_email_values.classList.remove('warning');
                if (/^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/.test(validate_email_values.value)){
                    console.log("success, big one")
                    validate_email_values.classList.remove("is-invalid");
                }
                else{
                    SetError(validate_email_values, ' Invalid Email')
                    validate_email_values.classList.add('is-invalid');
                    isValid = false;
                }
            });
            if (isValid != true){
                return false
            }else{
                $.ajax({
                    url: "api/form4",
                    data: data,
                    method: 'put',
                    cache: false,
                    contentType: false,
                    enctype: 'multipart/form-data',
                    dataType: 'json',
                    processData: false,
                    beforeSend: function() {
                        console.log("loading that now");
                        $('#modalLoader').modal('show');
                    },
                    success: function(response) {
                        
                        console.log(response);
                        shownname.innerHTML = ' ';
                        formnumber++;
                        updateform();
                        var url = '/printonsuccess/' + response['record_id'] + '/hospital.quotation' + '/' + 4
                        window.location.href = url;
                        window.location.replace(url);

                    },
                    error: function(error) {
                        console.log(error);
                    },
                    complete:function(data){
                        console.log("here we complete")
                        $('#modalLoader').modal('hide');
                    }
                });
            }
            return false;
        });

        $('form#desire-form').on('submit', function(e) {
            e.preventDefault();
            let data = new FormData(this);
            var isValid = true
            var validate_inputs = document.querySelectorAll(".main.active input");
            validate_inputs.forEach(function(vaildate_input) {
                vaildate_input.classList.remove('is-invalid');
            });
            const phone_numbers = document.getElementsByClassName('phone_input');
            console.log("phone numbers: ",phone_numbers)
            for (var i = 0; i < phone_numbers.length; i++) {
                console.log(phone_numbers.item(i));
                if (isNumerics(phone_numbers.item(i).value) && phone_numbers.item(i).value.length == 10){
                    console.log("success, big one")
                }
                else{
                    SetError(phone_numbers.item(i), 'Invalid phone number')
                    isValid = false;
                }
             };
            const national_ids = document.getElementsByClassName('id_number_v');
            console.log("National Id's: ",national_ids)
            for (var i = 0; i < national_ids.length; i++) {
                console.log(national_ids.item(i));
                if (isNumerics(national_ids.item(i).value) && national_ids.item(i).value.length == 10){
                    console.log("success, big one")
                }
                else{
                    SetError(national_ids.item(i), 'Invalid Id Number')
                    isValid = false;
                }
            }
            const amounts = document.getElementsByClassName('amount_v');
            console.log("Amounts: ",amounts)
            for (var i = 0; i < amounts.length; i++) {
                console.log(amounts.item(i));
                if (isNumeric(amounts.item(i).value)){
                    console.log("success, big one")
                    amounts.item(i).value = parseFloat(amounts.item(i).value);
                }
                else{
                    SetError(amounts.item(i), 'Invalid Amount')
                    isValid = false;
                }
            }
            const names = document.getElementsByClassName('name_v');
            console.log("names: ",names)
            for (var i = 0; i < names.length; i++) {
                console.log(names.item(i));
                if (isName(names.item(i).value)){
                    console.log("success, big one")
                    names.item(i).classList.remove("is-invalid");
                }
                else{
                    SetError(names.item(i), 'Invalid name')
                    isValid = false;
                }
            }
            var validate_inputs_required = document.querySelectorAll(".main.active .required");
            validate_inputs_required.forEach(function(vaildate_input) {
                if (vaildate_input.value.length == 0) {
                    isValid = false;
                    vaildate_input.classList.add('is-invalid');
                }
            });
            

            if (isValid != true){
                return false
            }else{
                window.dataz = data;
                var url = window.location
                $.ajax({
                    url: "api/form1",
                    data: data,
                    method: 'put',
                    cache: false,
                    contentType: false,
                    enctype: 'multipart/form-data',
                    dataType: 'json',
                    processData: false,
                    beforeSend: function() {},
                    success: function(response) {
                        console.log(response);
                        shownname.innerHTML = ' ';
                        formnumber++;
                        updateform();
                        var url = '/printonsuccess/' + response['record_id'] + '/expression.of.desire' + '/' + 1
                        window.location.href = url;
                        window.location.replace(url);
                    },
                    error: function(error) {
                        console.log(error);
                    }
                });
            }
            var username = document.querySelector("#user_name");
            var shownname = document.querySelector(".shown_name");
            var submit_click = document.querySelectorAll(".submit_button");
            submit_click.forEach(function(submit_click_form) {
                submit_click_form.addEventListener('click', function() {
                    // shownname.innerHTML = username.value;
                    shownname.innerHTML = ' ';
                    formnumber++;
                    updateform();
                });
            });
            
            return false;
        });
        
    });

    function isName(vals){
        if(vals.length != 0){
            if ( !/\d+/.test(vals)){
                return true;
            }
            else{
                return false;
            }
        }else{return true}
    }

    function isNumeric(value) {
        // return /^-?\d+$/.test(value);
        if(value.length !=0 ){
            return !isNaN(parseFloat(value));
        }else{return true}
        // return !isNaN(parseFloat(value)) && isFinite(value);
    }
    function isNumerics(value) {
        if(value.length !=0 ){
            return /^-?\d+$/.test(value);
        }else{return true}
        // return !isNaN(parseFloat(value)) && isFinite(value);
    }
    function SetError(number,message){
        console.log(number.value + 'is' + message)
        number.classList.add('is-invalid')
    }

    var next_click = document.querySelectorAll(".next_button");
    var main_form = document.querySelectorAll(".main");
    var step_list = document.querySelectorAll(".progress-bar li");
    var num = document.querySelector(".step-number");
    let formnumber = 0;

    next_click.forEach(function(next_click_form) {
        next_click_form.addEventListener('click', function() {
            if (!validateform()) {
                return false
            }
            formnumber++;
            updateform();
            progress_forward();
            // contentchange();
        });
    });

    var back_click = document.querySelectorAll(".back_button");
    back_click.forEach(function(back_click_form) {
        back_click_form.addEventListener('click', function() {
            formnumber--;
            updateform();
            progress_backward();
            // contentchange();
        });
    });

    var hospital_names = document.querySelectorAll(".hospital_name");
    hospital_names.forEach(function(hospital_name){
        hospital_name.disabled = true;
        var rrs = document.querySelectorAll(".rr");
        rrs.forEach(function(rr){
            rr.classList.remove("required");
            rr.classList.remove("is-invalid");
        })
    });

    var have_guarantor = document.querySelectorAll(".have_guarantor");
    have_guarantor.forEach(function(have_guarantor){
        have_guarantor.addEventListener('click', function() {
            var hospital_names = document.querySelectorAll(".hospital_name");
            if (have_guarantor.checked == false){
                hospital_names.forEach(function(hospital_name){
                    hospital_name.disabled = true;
                    var rrs = document.querySelectorAll(".rr");
                    rrs.forEach(function(rr){
                        rr.classList.remove("required");
                        rr.classList.remove("is-invalid");
                    })
                });
            }else{
                console.log("Guarantor Checked: ",have_guarantor.checked)
                hospital_names.forEach(function(hospital_name){
                    hospital_name.disabled = false;
                    hospital_name.value = '';
                    var rrs = document.querySelectorAll(".rr");
                    rrs.forEach(function(rr){
                        rr.classList.add("required");
                    })
                });
            }
            console.log("have_guarantor",have_guarantor.checked);
        });

    });


    // make joining date / date of establishment not required in case you select retired
    var job_type_selections = document.querySelectorAll(" .job_type_selection");
    job_type_selections.forEach(function(job_type_selection){
        job_type_selection.addEventListener('click', function() {
            var set_join_dates = document.querySelectorAll(".set_join_date");
            if (job_type_selection.value == 'retired'){
                set_join_dates.forEach(function(set_join_date){
                    set_join_date.classList.remove("required");
                    set_join_date.classList.remove("is-invalid");
                });
            }else{
                set_join_dates.forEach(function(set_join_date){
                    set_join_date.classList.add("required");
                });
            }
        });

    });

    // make joining date / date of establishment not required in case you select retired in guarantor
    var g_job_type_selections = document.querySelectorAll(" .g_job_type_selection");
    g_job_type_selections.forEach(function(g_job_type_selection){
        g_job_type_selection.addEventListener('click', function() {
            var g_set_join_dates = document.querySelectorAll(".g_set_join_date");
            if (g_job_type_selection.value == 'retired'){
                g_set_join_dates.forEach(function(g_set_join_date){
                    g_set_join_date.classList.remove("required");
                    g_set_join_date.classList.remove("is-invalid");
                });
            }else{
                g_set_join_dates.forEach(function(g_set_join_date){
                    g_set_join_date.classList.add("required");
                });
            }
        });

    });


    // make hospital name available and required when click on know_us from hospital
    var custom_radio_controler = document.querySelectorAll(".know_us_value");
    custom_radio_controler.forEach(function(controller){
        controller.addEventListener('click', function() {
            if (controller.value == 'clients'){
                var hospital_name = document.querySelectorAll(".hospital_name_know_us")
                hospital_name.forEach(function(my_hospital){
                    my_hospital.style.visibility = "visible";
                    my_hospital.classList.add("required")
                    my_hospital.classList.remove("not-visible")
                })
            }else{
                var hospital_name = document.querySelectorAll(".hospital_name_know_us")
                hospital_name.forEach(function(my_hospital){
                    my_hospital.style.visibility = "hidden";
                    my_hospital.classList.remove("required")
                    my_hospital.classList.remove("is-invalid");
                    my_hospital.classList.add("not-visible");

                    
                })   
            }
        });

    });
    



    var home_type = document.querySelectorAll(".rented_home1");
    console.log(" Home Type: ", home_type.value)
    home_type.forEach(function(home_type){
        home_type.addEventListener('click',function(){
            console.log(" Home Type: ", home_type.value);
            var annual_rent = document.querySelectorAll(".main.active .annual_rent1");
            annual_rent.forEach(function(annual_rent1){
                if(home_type.value == 'rent'){
                    annual_rent1.classList.add("required");
                    console.log("annual rent: ",annual_rent1)
                }else{
                    annual_rent1.classList.remove("required");
                    console.log("else annual rent: ",annual_rent1)
                }
            });
            
        });
    });

    var have_medical_service = document.querySelectorAll(".have_medical");
    have_medical_service.forEach(function(have_medical_service){
        have_medical_service.addEventListener('click', function() {
            var medical_details = document.querySelectorAll(".medical_details");
            if (have_medical_service.checked == true){
                medical_details.forEach(function(medical_detail){
                    medical_detail.classList.add("required");
                });
            }else{
                medical_details.forEach(function(medical_detail){
                    medical_detail.classList.remove("required");
                });
            }
            console.log("have_medical_service",have_medical_service.checked);
        });

    });

    function updateform() {
        main_form.forEach(function(mainform_number) {
            mainform_number.classList.remove('active');
        })
        main_form[formnumber].classList.add('active');
    }

    function progress_forward() {

        num.innerHTML = formnumber + 1;
        step_list[formnumber].classList.add('active');
    }

    function progress_backward() {
        var form_num = formnumber + 1;
        step_list[form_num].classList.remove('active');
        num.innerHTML = form_num;
    }

    var step_num_content = document.querySelectorAll(".step-number-content");

    function contentchange() {
        step_num_content.forEach(function(content) {
            content.classList.remove('active');
            content.classList.add('d-none');
        });
        step_num_content[formnumber].classList.add('active');
    }


    function validateform() {
        validate = true;
        var validate_inputs = document.querySelectorAll(".main.active input");
        validate_inputs.forEach(function(vaildate_input) {
            vaildate_input.classList.remove('is-invalid');
        });
        var validate_inputs_required = document.querySelectorAll(".main.active .required");
        validate_inputs_required.forEach(function(vaildate_input) {
            if (vaildate_input.value.length == 0) {
                validate = false;
                vaildate_input.classList.add('is-invalid');
            }
        });
        var validate_inputs = document.querySelectorAll(".main.active input");
        validate_inputs.forEach(function(vaildate_input) {
            vaildate_input.classList.remove('warning');
            if (vaildate_input.hasAttribute('required')) {
                if (vaildate_input.value.length == 0) {
                    validate = false;
                    vaildate_input.classList.add('is-invalid');
                }
            }
        });
        var validate_select = document.querySelectorAll(".main.active select");
        validate_select.forEach(function(vaildate_select) {
            vaildate_select.classList.remove('warning');
            if (vaildate_select.hasAttribute('required')) {
                if (vaildate_select.value.length == 0) {
                    validate = false;
                    vaildate_select.classList.add('is-invalid');
                }
            }
        });
        var validate_amount = document.querySelectorAll(".main.active .amount_v");
        validate_amount.forEach(function(validate_amount){
            validate_amount.classList.remove('warning');
            if(validate_amount.value.length != 0){
                console.log('amount',validate_amount.value)
                if (isNumeric(validate_amount.value)){
                    console.log("success, big one")
                    validate_amount.value = parseFloat(validate_amount.value);
                }
                else{
                    SetError(validate_amount, 'Invalid Amount')
                    console.log(validate_amount)
                    validate_amount.classList.add('is-invalid');
                    validate = false;
                }
            }else{}
        });
        // number of dependant validations
        var validate_dependant = document.querySelectorAll(".main.active .dependant_v");
        validate_dependant.forEach(function(validate_dependant){
            validate_dependant.classList.remove('warning');
            if(validate_dependant.value.length != 0){
                console.log('amount',validate_dependant.value)
                if (isNumeric(validate_dependant.value)){
                    if (validate_dependant.value > 0){
                        console.log("success, big one")
                        validate_dependant.value = parseFloat(validate_dependant.value);
                    }else{
                        SetError(validate_dependant, 'Invalid Amount')
                        console.log(validate_dependant)
                        validate_dependant.classList.add('is-invalid');
                        validate = false;
                    }
                }
                else{
                    SetError(validate_dependant, 'Invalid Amount')
                    console.log(validate_dependant)
                    validate_dependant.classList.add('is-invalid');
                    validate = false;
                }
            }else{}
        });
        // phone validation
        var validate_phone_input = document.querySelectorAll(".main.active .phone_input");
        validate_phone_input.forEach(function(validate_phone_input){
            validate_phone_input.classList.remove('warning');
            if(validate_phone_input.value.length != 0){
                // if (isNumerics(validate_phone_input.value)){
                if (isNumerics(validate_phone_input.value) && validate_phone_input.value.length == 10){
                    console.log("success, big one")
                }
                else{
                    SetError(validate_phone_input, 'Invalid phone number')
                    validate_phone_input.classList.add('is-invalid');
                    validate = false;
                }
            }else{}
        });
        // id_number_v validation
        var validate_id_number_v = document.querySelectorAll(".main.active .id_number_v");
        validate_id_number_v.forEach(function(validate_id_number_v){
            console.log("i guess it's just undefinde: ",validate_id_number_v.classList)
            validate_id_number_v.classList.remove('warning');
            if(validate_id_number_v.value.length != 0){
                // if (isNumerics(validate_id_number_v.value)){
                if (isNumerics(validate_id_number_v.value) && validate_id_number_v.value.length == 10){
                    console.log("success, big one")
                }
                else{
                    SetError(validate_id_number_v, 'Invalid ID number')
                    validate_id_number_v.classList.add('is-invalid');
                    validate = false;
                }
            }else{}
        });
        // name validiation
        var validate_name_values = document.querySelectorAll(".main.active .name_v");
        validate_name_values.forEach(function(validate_name_values){
            validate_name_values.classList.remove('warning');
            if(validate_name_values.value.length != 0){
                if (isName(validate_name_values.value)){
                    console.log("success, big one")
                    validate_name_values.classList.remove("is-invalid");
                }
                else{
                    SetError(validate_name_values, ' Invalid name')
                    validate_name_values.classList.add('is-invalid');
                    validate = false;
                }
            }else{}
        });
        
        // email validation
        var validate_email_values = document.querySelectorAll(".main.active .email_v");
        validate_email_values.forEach(function(validate_email_values){
            validate_email_values.classList.remove('warning');
            if(validate_email_values.value.length != 0){
                console.log("email",validate_email_values.value)
                if (/^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/.test(validate_email_values.value)){
                    console.log("success, big one")
                    validate_email_values.classList.remove("is-invalid");
                }
                else{
                    SetError(validate_email_values, ' Invalid Email')
                    validate_email_values.classList.add('is-invalid');
                    validate = false;
                }
            }else{}
        });
        var validate_file_values = document.querySelectorAll('.main.active .file_v');
        validate_file_values.forEach(function(validate_file_value){
            if(validate_file_value.value.length != 0){
                console.log("File: ",validate_file_value.value);
                var extension_array = validate_file_value.value.split(".");
                var extension = extension_array[extension_array.length - 1]
                var arr = ['pdf','PDF','jpg','JPG','jpeg','JPEG','gif','GIF','png','PNG','webp','WEBP']
                if (arr.includes(extension)){
                    validate_file_value.classList.remove("is-invalid");
                }else{
                    SetError(validate_file_value, ' Invalid File')
                    validate_file_value.classList.add('is-invalid');
                    validate = false;
                }
            }else{}
        });
        
        return validate;

    }
});