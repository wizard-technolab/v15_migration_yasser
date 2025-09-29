odoo.define('bi_timer_widget', function (require) {
	'use strict';

	var AbstractField = require('web.AbstractField');
	var core = require('web.core');
	var field_registry = require('web.field_registry');
	var time = require('web.time');
	var fields = require('web.basic_fields')
	var fieldUtils = require('web.field_utils')
	



	var TimeCounter = AbstractField.extend({
		supportedFieldTypes: [],
		/**
		 * @override
		 */

		init: function () {
			this._super.apply(this, arguments);
			this.timer = this.record.data.timer;
		},
		willStart: function () {
			this.timerStart()        
			return $.when(this._super.apply(this, arguments));
		},

		timerStart: function(){
			var self = this;
			
			if (self.record.data.id){
				var def = this._rpc({
					model: self.model,
					method: 'search_read',
					domain: [
						['id', '=', self.record.data.id],
						['timer_start', '=', true],
					],
				}).then(function (result) {
					var currentDate = new Date();
					var duration = 0;
					if (result.length > 0) {
						duration += self._getDateDifference(time.auto_str_to_date(result[0].timer_start_date), currentDate);
					}
					
					if(result.length > 0){
						if (result[0].timer_start) {
							var dur = duration / 1000
							self.timer += dur;
						}
						else{
                            var dur = duration / 1000
                            var stop_time = self.timer + dur

                        }
					}
						
				});  
			}
		},

		destroy: function () {
			this._super.apply(this, arguments);
			clearTimeout(this.timer);
		},

		_getDateDifference: function (dateStart, dateEnd) {
			return moment(dateEnd).diff(moment(dateStart), 'milliseconds');
		},

		//--------------------------------------------------------------------------
		// Public
		//--------------------------------------------------------------------------

		/**
		 * @override
		 */
		isSet: function () {
			return true;
		},

		//--------------------------------------------------------------------------
		// Private
		//--------------------------------------------------------------------------

		
		/**
		 * @override
		 */
		_render: function () {
			this._startTimeCounter();
		},
		/**
		 * @private
		 */
		_startTimeCounter: function () {
			var self = this;
			clearTimeout(this.duration);
			if (this.record.data.timer_start) {
				this.duration = setTimeout(function () {
					self.timer += 60/60;
					self._startTimeCounter();
				}, 1000);
			} else {
				clearTimeout(this.duration);
			}

			
			const duration = moment.duration(this.timer, 'seconds');
			const hours = Math.floor(duration.asHours());
			const minutes = duration.minutes();
			const seconds = duration.seconds();
			//display the variables in two-character format, e.g: 09 intead of 9
			const text = _.str.sprintf("%02d:%02d:%02d", hours, minutes, seconds);
			const $mrpTimeText = $('<span>', { text });
			this.$el.empty().append($mrpTimeText);
				
		},
	});

	field_registry.add('timer', TimeCounter);
	fieldUtils.format.timer = fieldUtils.format.float_time
	return {
		TimeCounter: TimeCounter,
	};
});