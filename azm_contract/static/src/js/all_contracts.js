// Define an Odoo module named "azm_contract.all_contracts"
odoo.define("azm_contract.all_contracts", function (require) {
    "use strict";  // Enforce strict mode for better error checking and cleaner code
    // Require necessary Odoo modules
    var rpc = require("web.rpc");            // Import the RPC (Remote Procedure Call) module to make server calls
    var ListController = require("web.ListController"); // Import the ListController module to extend list view functionality
    // Extend the ListController to add custom behavior
    ListController.include({
        // Add additional event handlers to the existing ListController events
        events: _.extend({}, ListController.prototype.events, {
            // Bind the 'click' event on elements with class '.get_all_contracts' to the 'get_call_contracts' method
            "click .get_all_contracts": "get_call_contracts",
        }),
        // Define the method to be executed when the '.get_all_contracts' element is clicked
        get_call_contracts: function (e) {
            var self = this; // Preserve the reference to 'this' for use within the promise callback
            // Make an RPC call to the server
            this._rpc({
                model: "all.contracts.integration", // The model to call on the server side
                method: "action_all_contracts",      // The method to call on the server side
                args: [[]],                         // Arguments to pass to the server method
            }).then(function (result) {
                // Reload the page when the RPC call is successful
                window.location.reload();
            });
        },
    });
});
