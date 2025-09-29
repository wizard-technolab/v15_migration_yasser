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


//odoo.define('website_menu.script', function(require) {
//    $(document).ready(function() {
//        console.log('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq')
//
//        var calculate = document.querySelectorAll(".calculate");
//        var loan_amount = document.getElementById("#loan_amount")
//
//        console.log(loan_amount)
//
////        var calculate = document.querySelectorAll(".main.active.num_value");
//        calculate.forEach(function(calculate_form) {
//            calculate_form.addEventListener('click', function() {
//                console.log('uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu')
////                loan_amount.text='True';
//                });
//    });
//    });
//    });


//    function isName(vals){
//        if(vals.length != 0){
//            if ( !/\d+/.test(vals)){
//                return true;
//            }
//            else{
//                return false;
//            }
//        }else{return true}
//    }
//
//    function isNumeric(value) {
//        // return /^-?\d+$/.test(value);
//        if(value.length !=0 ){
//            return !isNaN(parseFloat(value));
//        }else{return true}
//        // return !isNaN(parseFloat(value)) && isFinite(value);
//    }
//    function isNumerics(value) {
//        if(value.length !=0 ){
//            return /^-?\d+$/.test(value);
//        }else{return true}
//        // return !isNaN(parseFloat(value)) && isFinite(value);
//    }
//    function SetError(number,message){
//        console.log(number.value + 'is' + message)
//        number.classList.add('is-invalid')
//    }

//    var next_click = document.querySelectorAll(".next_button");
//    var main_form = document.querySelectorAll(".main");
//    var step_list = document.querySelectorAll(".progress-bar li");
//    var num = document.querySelector(".step-number");
//    let formnumber = 0;
//
//    next_click.forEach(function(next_click_form) {
//        next_click_form.addEventListener('click', function() {
//            if (!validateform()) {
//                return false
//            }
//            formnumber++;
//            updateform();
//            progress_forward();
//            // contentchange();
//        });
//    });
//
//    var back_click = document.querySelectorAll(".back_button");
//    back_click.forEach(function(back_click_form) {
//        back_click_form.addEventListener('click', function() {
//            formnumber--;
//            updateform();
//            progress_backward();
//            // contentchange();
//        });
//    });
//
//    var hospital_names = document.querySelectorAll(".hospital_name");
//    hospital_names.forEach(function(hospital_name){
//        hospital_name.disabled = true;
//        var rrs = document.querySelectorAll(".rr");
//        rrs.forEach(function(rr){
//            rr.classList.remove("required");
//            rr.classList.remove("is-invalid");
//        })
//    });
//
//    var have_guarantor = document.querySelectorAll(".have_guarantor");
//    have_guarantor.forEach(function(have_guarantor){
//        have_guarantor.addEventListener('click', function() {
//            var hospital_names = document.querySelectorAll(".hospital_name");
//            if (have_guarantor.checked == false){
//                hospital_names.forEach(function(hospital_name){
//                    hospital_name.disabled = true;
//                    var rrs = document.querySelectorAll(".rr");
//                    rrs.forEach(function(rr){
//                        rr.classList.remove("required");
//                        rr.classList.remove("is-invalid");
//                    })
//                });
//            }else{
//                console.log("Guarantor Checked: ",have_guarantor.checked)
//                hospital_names.forEach(function(hospital_name){
//                    hospital_name.disabled = false;
//                    hospital_name.value = '';
//                    var rrs = document.querySelectorAll(".rr");
//                    rrs.forEach(function(rr){
//                        rr.classList.add("required");
//                    })
//                });
//            }
//            console.log("have_guarantor",have_guarantor.checked);
//        });
//
//    });
//
//    var home_type = document.querySelectorAll(".rented_home1");
//    console.log(" Home Type: ", home_type.value)
//    home_type.forEach(function(home_type){
//        home_type.addEventListener('click',function(){
//            console.log(" Home Type: ", home_type.value);
//            var annual_rent = document.querySelectorAll(".main.active .annual_rent1");
//            annual_rent.forEach(function(annual_rent1){
//                if(home_type.value == 'rent'){
//                    annual_rent1.classList.add("required");
//                    console.log("annual rent: ",annual_rent1)
//                }else{
//                    annual_rent1.classList.remove("required");
//                    console.log("else annual rent: ",annual_rent1)
//                }
//            });
//
//        });
//    });
//
//    var have_medical_service = document.querySelectorAll(".have_medical");
//    have_medical_service.forEach(function(have_medical_service){
//        have_medical_service.addEventListener('click', function() {
//            var medical_details = document.querySelectorAll(".medical_details");
//            if (have_medical_service.checked == true){
//                medical_details.forEach(function(medical_detail){
//                    medical_detail.classList.add("required");
//                });
//            }else{
//                medical_details.forEach(function(medical_detail){
//                    medical_detail.classList.remove("required");
//                });
//            }
//            console.log("have_medical_service",have_medical_service.checked);
//        });
//
//    });
//
//    function updateform() {
//        main_form.forEach(function(mainform_number) {
//            mainform_number.classList.remove('active');
//        })
//        main_form[formnumber].classList.add('active');
//    }
//
//    function progress_forward() {
//
//        num.innerHTML = formnumber + 1;
//        step_list[formnumber].classList.add('active');
//    }
//
//    function progress_backward() {
//        var form_num = formnumber + 1;
//        step_list[form_num].classList.remove('active');
//        num.innerHTML = form_num;
//    }
//
//    var step_num_content = document.querySelectorAll(".step-number-content");
//
//    function contentchange() {
//        step_num_content.forEach(function(content) {
//            content.classList.remove('active');
//            content.classList.add('d-none');
//        });
//        step_num_content[formnumber].classList.add('active');
//    }
//
//
//    function validateform() {
//        validate = true;
//        var validate_inputs = document.querySelectorAll(".main.active input");
//        validate_inputs.forEach(function(vaildate_input) {
//            vaildate_input.classList.remove('is-invalid');
//        });
//        var validate_inputs_required = document.querySelectorAll(".main.active .required");
//        validate_inputs_required.forEach(function(vaildate_input) {
//            if (vaildate_input.value.length == 0) {
//                validate = false;
//                vaildate_input.classList.add('is-invalid');
//            }
//        });
//        var validate_inputs = document.querySelectorAll(".main.active input");
//        validate_inputs.forEach(function(vaildate_input) {
//            vaildate_input.classList.remove('warning');
//            if (vaildate_input.hasAttribute('required')) {
//                if (vaildate_input.value.length == 0) {
//                    validate = false;
//                    vaildate_input.classList.add('is-invalid');
//                }
//            }
//        });
//        var validate_select = document.querySelectorAll(".main.active select");
//        validate_select.forEach(function(vaildate_select) {
//            vaildate_select.classList.remove('warning');
//            if (vaildate_select.hasAttribute('required')) {
//                if (vaildate_select.value.length == 0) {
//                    validate = false;
//                    vaildate_select.classList.add('is-invalid');
//                }
//            }
//        });
//        var validate_amount = document.querySelectorAll(".main.active .amount_v");
//        validate_amount.forEach(function(validate_amount){
//            validate_amount.classList.remove('warning');
//            if(validate_amount.value.length != 0){
//                console.log('amount',validate_amount.value)
//                if (isNumeric(validate_amount.value)){
//                    console.log("success, big one")
//                    validate_amount.value = parseFloat(validate_amount.value);
//                }
//                else{
//                    SetError(validate_amount, 'Invalid Amount')
//                    console.log(validate_amount)
//                    validate_amount.classList.add('is-invalid');
//                    validate = false;
//                }
//            }else{}
//        });
//        // phone validation
//        var validate_phone_input = document.querySelectorAll(".main.active .phone_input");
//        validate_phone_input.forEach(function(validate_phone_input){
//            validate_phone_input.classList.remove('warning');
//            if(validate_phone_input.value.length != 0){
//                // if (isNumerics(validate_phone_input.value)){
//                if (isNumerics(validate_phone_input.value) && validate_phone_input.value.length == 10){
//                    console.log("success, big one")
//                }
//                else{
//                    SetError(validate_phone_input, 'Invalid phone number')
//                    validate_phone_input.classList.add('is-invalid');
//                    validate = false;
//                }
//            }else{}
//        });
//        // id_number_v validation
//        var validate_id_number_v = document.querySelectorAll(".main.active .id_number_v");
//        validate_id_number_v.forEach(function(validate_id_number_v){
//            console.log("i guess it's just undefinde: ",validate_id_number_v.classList)
//            validate_id_number_v.classList.remove('warning');
//            if(validate_id_number_v.value.length != 0){
//                // if (isNumerics(validate_id_number_v.value)){
//                if (isNumerics(validate_id_number_v.value) && validate_id_number_v.value.length == 10){
//                    console.log("success, big one")
//                }
//                else{
//                    SetError(validate_id_number_v, 'Invalid ID number')
//                    validate_id_number_v.classList.add('is-invalid');
//                    validate = false;
//                }
//            }else{}
//        });
//        // name validiation
//        var validate_name_values = document.querySelectorAll(".main.active .name_v");
//        validate_name_values.forEach(function(validate_name_values){
//            validate_name_values.classList.remove('warning');
//            if(validate_name_values.value.length != 0){
//                if (isName(validate_name_values.value)){
//                    console.log("success, big one")
//                    validate_name_values.classList.remove("is-invalid");
//                }
//                else{
//                    SetError(validate_name_values, ' Invalid name')
//                    validate_name_values.classList.add('is-invalid');
//                    validate = false;
//                }
//            }else{}
//        });
//
//        // email validation
//        var validate_email_values = document.querySelectorAll(".main.active .email_v");
//        validate_email_values.forEach(function(validate_email_values){
//            validate_email_values.classList.remove('warning');
//            if(validate_email_values.value.length != 0){
//                console.log("email",validate_email_values.value)
//                if (/^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/.test(validate_email_values.value)){
//                    console.log("success, big one")
//                    validate_email_values.classList.remove("is-invalid");
//                }
//                else{
//                    SetError(validate_email_values, ' Invalid Email')
//                    validate_email_values.classList.add('is-invalid');
//                    validate = false;
//                }
//            }else{}
//        });
//        var validate_file_values = document.querySelectorAll('.main.active .file_v');
//        validate_file_values.forEach(function(validate_file_value){
//            if(validate_file_value.value.length != 0){
//                console.log("File: ",validate_file_value.value);
//                var extension_array = validate_file_value.value.split(".");
//                var extension = extension_array[extension_array.length - 1]
//                var arr = ['pdf','PDF','jpg','JPG','jpeg','JPEG','gif','GIF','png','PNG','webp','WEBP']
//                if (arr.includes(extension)){
//                    validate_file_value.classList.remove("is-invalid");
//                }else{
//                    SetError(validate_file_value, ' Invalid File')
//                    validate_file_value.classList.add('is-invalid');
//                    validate = false;
//                }
//            }else{}
//        });
//
//        return validate;
//
//    }
