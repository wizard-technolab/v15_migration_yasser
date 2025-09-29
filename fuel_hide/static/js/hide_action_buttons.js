// Define a new JavaScript module named 'hide_action_menu_buttons.hide_buttons'
odoo.define('hide_action_menu_buttons.hide_buttons', function (require) {
    "use strict";

    // Import necessary modules
    const ListView = require('web.ListView'); // Import ListView module
    const FormView = require('web.FormView'); // Import FormView module
    const rpc = require('web.rpc'); // Import rpc module for making requests to the server

    // Function to hide the "Delete" and "Archive" buttons based on group access
    function hideButtons(view) {
        // Define the name of the custom group for access control
        const CUSTOM_GROUP = 'fuel_hide.group_hide_action_menu_button';

        // Function to check user's group access asynchronously
        function checkGroupAccess() {
            return rpc.query({
                model: 'res.users',
                method: 'has_group',
                args: [CUSTOM_GROUP],
            });
        }

        // Check user's group access and hide buttons accordingly
        checkGroupAccess().then(function (hasAccess) {
            if (!hasAccess) { // If user does not have access to the custom group
                // Hide the "Delete" and "Archive" buttons
                view.controllerParams.activeActions.delete = false;
                view.controllerParams.archiveEnabled = false;
            }
        });
    }

    // Extend the ListView module to include functionality for hiding buttons
    ListView.include({
        init: function () {
            this._super.apply(this, arguments); // Call the parent method
            hideButtons(this); // Call the function to hide buttons
        },
    });

    // Extend the FormView module to include functionality for hiding buttons
    FormView.include({
        init: function () {
            this._super.apply(this, arguments); // Call the parent method
            hideButtons(this); // Call the function to hide buttons
        },
    });
});



