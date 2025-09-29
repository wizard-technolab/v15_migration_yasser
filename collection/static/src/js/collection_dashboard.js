odoo.define('collection.dashboard', function (require) {
    "use strict";

    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');
    const rpc = require('web.rpc');
    const QWeb = core.qweb;


    const CollectionDashboard = AbstractAction.extend({
        template: 'CollectionDashboardMain',

        start: async function () {
            try {
                const result = await rpc.query({
                    model: 'collection.collection',
                    method: 'get_dashboard_data',
                });
                console.log("Dashboard result:", result);
                if (result && result.cards && Array.isArray(result.cards)) {
                    console.log("Rendering dashboard data:", result.cards);
                    console.log("Dashboard result:", result);
                    this.$el.html(QWeb.render('CollectionDashboardMain', {
                        data: result,
                    }));
                } else {
                    console.error("خطأ: البيانات غير مكتملة أو غير موجودة");
                    this.$el.html("<p>فشل تحميل البيانات.</p>");
                }

                this._bindEvents();
            } catch (error) {
                console.error("خطأ في تحميل البيانات:", error);
                this.$el.html("<p>حدث خطأ أثناء تحميل البيانات. حاول مرة أخرى لاحقًا.</p>");
            }
        },

        _bindEvents: function () {
            this.$('.collection-box').on('click', function () {
                const action_id = $(this).data('action');
                if (action_id) {
                    window.location = '#action=' + action_id;
                }
            });
        }
    });

    core.action_registry.add('collection_dashboard', CollectionDashboard);

    return CollectionDashboard;
});