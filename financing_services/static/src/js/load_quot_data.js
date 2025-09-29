odoo.define('financing_services.load_quot_data', function(require){
    
    // 
    var current_page = window.location.href

    if (current_page.includes('/form4')){

        const ajax = require('web.ajax');
        const core = require('web.core');
        const selection = document.getElementById('service_selection');
        const service_form_group = document.getElementById('service_form_group');
        const add_line_button = document.getElementById('add_line_button');

        

        
        var products = []
        function CallData(){
            console.log("Inside the function!")
            ajax.jsonRpc('/web/get_products/','call').then(function(vals){
                console.log("this is then,", vals)
                console.log("selection,", selection)
                products = vals['products']
                products.forEach(product => {
                    // create option
                    var option = document.createElement('option');
                    option.setAttribute('value',product['id']);
                    option.setAttribute('name' ,'product_id_' + product['id'])
                    var code = ''
                    if (product['default_code'] != false){
                        code = product['default_code']
                    }
                    var option_text = document.createTextNode(product['name'] + ' [' + code + ']')
                    option.appendChild(option_text)
                    // append option to selection
                    selection.appendChild(option);
                    selection.setAttribute('name' ,'product_id_' + product['id'])
                    console.log("here in this");
                });
                clinic = vals['clinic'];
                company_name = document.getElementById('company_name');
                company_name.appendChild(document.createTextNode(clinic['clinic_name']))
                company_name.value = clinic['clinic_name']
                clinic_name = document.getElementById('clinic_name');
                clinic_name.value = clinic['clinic_name']
                clinic_email = document.getElementById('clinic_email');
                clinic_email.value = clinic['clinic_email']
                applicant_name = document.getElementById('applicant_name');
                applicant_name.value = clinic['applicant_name']
                clinic_phone = document.getElementById('clinic_phone');
                clinic_phone.value = clinic['clinic_phone']
                contract_name = document.getElementById('contract_name');
                contract_name.value = clinic['contract_name']
                contract_date = document.getElementById('contract_date');
                contract_date.value = clinic['contract_date']
                clinic_user_id = document.getElementById('clinic_user_id');
                clinic_user_id.value = clinic['clinic_user_id']

                var consistent_amount = document.getElementById('consistent_amount');
                consistent_amount.setAttribute('name','product_amount_' + products[0]['id']);

                var consistent_quantity = document.getElementById('consistent_quantity');
                consistent_quantity.setAttribute('name','product_quantity_' + products[0]['id']);

                var consistent_price = document.getElementById('consistent_price');
                consistent_price.setAttribute('name','product_price_' + products[0]['id']);
                selection.setAttribute('name' ,'product_id_' + products[0]['id'])


            });
            
        }
        // load the products to the template
        CallData()

        // add line code
        var row_id = 1
        add_line_button.addEventListener('click', function() {
            row_id = row_id + 1
            console.log("line added in: ",service_form_group)
            // row
            var row = document.createElement('div');
            row.setAttribute('class','row');
            row.setAttribute('style','margin-top:5px;')
            row.setAttribute('id',row_id)
            // col-6
            var col6 = document.createElement('div');
            col6.setAttribute('class','col-5');
            var added_selection = document.createElement('select');
            added_selection.setAttribute('class','form-control service_selection custom-select')
            // add options to selection
            products.forEach(product => {
                // create option
                var option = document.createElement('option');
                option.setAttribute('value',product['id']);
                option.setAttribute('name' ,'product_id_' + product['id'])
                added_selection.setAttribute('name' ,'product_id_' + product['id'])
                var code = ''
                    if (product['default_code'] != false){
                        code = product['default_code']
                    }
                var option_text = document.createTextNode(product['name'] + ' [' + code + ']')
                option.appendChild(option_text)
                // append option to added_selection
                added_selection.appendChild(option)
            });
            added_selection.setAttribute('name' ,'product_id_' + products[0]['id'])
            col6.appendChild(added_selection);

            // col-2 quantity
            var col_quantity = document.createElement('div');
            col_quantity.setAttribute('class','col-2');
            var quantity = document.createElement('input')
            quantity.setAttribute('class','form-control amount_v required')
            quantity.setAttribute('placeholder',"Service Quantity")
            quantity.setAttribute('name','product_quantity_' + added_selection.value)
            col_quantity.appendChild(quantity)
            
            // col-2 price
            var col_price = document.createElement('div');
            col_price.setAttribute('class','col-2');
            var price = document.createElement('input')
            price.setAttribute('class','form-control amount_v required')
            price.setAttribute('placeholder',"Unit Price")
            price.setAttribute('name','product_price_' + added_selection.value)
            col_price.appendChild(price)
            
            // col-2 amount
            var col5 = document.createElement('div');
            col5.setAttribute('class','col-2');
            var amount = document.createElement('input')
            amount.setAttribute('class','form-control amount_v required')
            amount.setAttribute('placeholder',"Service Amount")
            amount.setAttribute('name','product_amount_' + added_selection.value)
            added_selection.addEventListener('click', function() {
                quantity.setAttribute('name','product_quantity_' + added_selection.value)
                price.setAttribute('name','product_price_' + added_selection.value)
                amount.setAttribute('name','product_amount_' + added_selection.value)
                added_selection.setAttribute('name' ,'product_id_' + added_selection.value)
            });
            col5.appendChild(amount)
            
            // col-1 ( the delete button )
            var col1 = document.createElement('div')
            col1.setAttribute('class','col-1 text-center')
            col1.setAttribute('style','background:#ff0303; border-radius:10px')
            // delete row
            var delete_row = document.createElement('i');
            delete_row.setAttribute('class','fa fa-trash')
            delete_row.setAttribute('style','color:white');
            // var delete_text = document.createTextNode("delete");
            // delete_row.appendChild(delete_text);


            col1.addEventListener('click',function(){
                col1.parentNode.remove();
            })
            col1.appendChild(delete_row);
            // append the two cols i nrow
            row.appendChild(col6);
            row.appendChild(col_quantity);
            row.appendChild(col_price);
            row.appendChild(col5);
            row.appendChild(col1);
            // append row to form gorup
            service_form_group.appendChild(row);

        });
        
        
        // first selector action
        var all_selections = document.querySelectorAll(" .service_selection");
        all_selections.forEach(function(current_selection){
            var consistent_amount = document.getElementById('consistent_amount');
            var consistent_quantity = document.getElementById('consistent_quantity');
            var consistent_price = document.getElementById('consistent_price');
            current_selection.setAttribute('name','product_id_' + current_selection.value)
            current_selection.addEventListener('click', function() {
                consistent_amount.setAttribute('name','product_amount_' + current_selection.value);
                consistent_quantity.setAttribute('name','product_quantity_' + current_selection.value);
                consistent_price.setAttribute('name','product_price_' + current_selection.value);
                current_selection.setAttribute('name','product_id_' + current_selection.value)
            });
        });
    }
});

