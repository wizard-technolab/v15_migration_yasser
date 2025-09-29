//odoo.define('loan.loan_order', function (require) {
//    'use strict';
//
//    const rpc = require('web.rpc');
//    const FormRenderer = require('web.FormRenderer');
//    const core = require('web.core');
//
//    const _t = core._t; // Translation function for Odoo
//
//    FormRenderer.include({
//        async _render() {
//            await this._super(...arguments);
//
//            try {
//                // Check if the current user is in both groups individually
//                const inGroupL1 = await rpc.query({
//                    model: 'res.users',
//                    method: 'has_group',
//                    args: ['loan.group_credit_l1']
//                });
//                const inGroupSimah = await rpc.query({
//                    model: 'res.users',
//                    method: 'has_group',
//                    args: ['loan.group_simah_access']
//                });
//
//                // Find the loan_type field
//                const loanTypeField = this.$el.find('input[name="loan_type"]');
//
//                // Debugging: Check the groups
//                console.log('In group L1:', inGroupL1);
//                console.log('In group Simah:', inGroupSimah);
//
//                // If the user is in both groups, remove readonly attribute from 'loan_type' field
//                if (inGroupL1 && inGroupSimah) {
//                    loanTypeField.prop('readonly', false);
//                    console.log('Loan type field set to editable');
//                } else {
//                    loanTypeField.prop('readonly', true); // Set readonly to true if not in both groups
//                    console.log('Loan type field set to readonly');
//                }
//            } catch (error) {
//                console.error('Error checking user groups:', error);
//                // Optional: Show an error message to the user
//                alert(_t('An error occurred while checking permissions.'));
//            }
//        },
//    });
//});
