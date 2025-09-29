//+=============================================================================================
//*
//*                     This File Content On All Hide And Disable Parts Of Loan
//*
//+=============================================================================================


//----------------------------------| Disable Create Edit Button By Group | ---------------------

odoo.define('loan_order.customize_loan_order_view', function (require) {
    "use strict";

    var FormController = require('web.FormController');
    var KanbanController = require('web.KanbanController');
    var ListView = require('web.ListController');
    var session = require('web.session');

    var modelName = 'loan.order';


    // Form View
    FormController.include({
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.modelName === modelName && this.$buttons) {
                session.user_has_group('loan.group_loan_write').then(function(hasGroup) {
                    if (!hasGroup) {
                        this.$buttons.find('button.o_form_button_create').hide();
                        this.$buttons.find('button.o_form_button_edit').hide();
                    }
                }.bind(this));
            }
        },
    });

    // List View
    ListView.include({
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.modelName === modelName && this.$buttons) {
                session.user_has_group('loan.group_loan_write').then(function(hasGroup) {
                    if (!hasGroup) {
                        this.$buttons.find('.o_list_button_add').hide();
                    }
                }.bind(this));
            }
        },
    });

    // Kanban View
    KanbanController.include({
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.modelName === modelName && this.$buttons) {
                session.user_has_group('loan.group_loan_write').then(function(hasGroup) {
                    if (!hasGroup) {
                        this.$buttons.find('.o-kanban-button-new').hide();
                    }
                }.bind(this));
            }
        },
    });
});
