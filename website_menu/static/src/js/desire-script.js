// odoo.define('financing_services.desire', function(require) {
//     $(document).ready(function() {
//         $('form#desire-form').on('submit', function(e) {
//             e.preventDefault();
//             $('form#desire-form input[required="required"]').removeClass("is-invalid");
//             let required_input = $('form#desire-form input[required="required"]');
//             let status = true;
//             $.each(required_input, function(index) {
//                 if ($(required_input[index]).val().length <= 0) {
//                     status = false;
//                     $(required_input[index]).addClass('is-invalid');
//                 }
//             });
            
//             console.log("this is status: ",status)
//             if (status) {
//                 let data = new FormData(this);
//                 window.dataz = data;
//                 $.ajax({
//                     url: "/api/form1",
//                     data: data,
//                     method: 'put',
//                     cache: false,
//                     contentType: false,
//                     enctype: 'multipart/form-data',
//                     dataType: 'json',
//                     processData: false,
//                     beforeSend: function() {},
//                     success: function(response) {
//                         console.log(response);
//                     },
//                     error: function(error) {
//                         console.log(error);
//                     }
//                 });
//             }
//             return false;
//         })
//     });
// });