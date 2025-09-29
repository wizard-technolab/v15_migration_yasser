odoo.define('dev_hide_delete.hide_delete', function(require) {
    "use strict";

    var KanbanController = require("web.KanbanController");
    var ListController = require("web.ListController");
    var FormController = require("web.FormController");
    var session = require('web.session');
    var core = require('web.core');
    var _t = core._t;

    var includeDict = {
        _getActionMenuItems: function (state) {
        	var result = this._super.apply(this, arguments);
        	if(result && result.items && result.items.other && result.items.other.length && !session.is_show_delete_button){
        		result.items.other.splice(_.findIndex(result.items.other, { description: "Delete" }), 1);
        	}
        	return result
		},
    };

    KanbanController.include(includeDict);
    ListController.include(includeDict);
    
    FormController.include({
    	_getActionMenuItems: function (state) {
        	var result = this._super.apply(this, arguments);
        	if(result && result.items && result.items.other && result.items.other.length && !session.is_show_delete_button){
        		result.items.other.splice(_.findIndex(result.items.other, { description: "Delete" }), 1);
        	}
        	return result
		},
    });
});
