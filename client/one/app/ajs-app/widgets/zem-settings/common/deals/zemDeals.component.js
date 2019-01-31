angular.module('one.widgets').component('zemDeals', {
    bindings: {
        entity: '<',
        api: '<',
    },
    template: require('./zemDeals.component.html'),
    controller: function($q, config, zemPermissions) {
        var $ctrl = this;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.deals = [];
        $ctrl.$onInit = function() {
            $ctrl.api.register({});
        };
        $ctrl.$onChanges = function() {
            $ctrl.deals = getDirectDealConnections();
        };
        function getDirectDealConnections() {
            if (!$ctrl.entity) {
                return [];
            }
            var allDeals = [];
            var directDealConnections = $ctrl.entity.deals || [];
            directDealConnections.forEach(function(ddc) {
                ddc.deals.forEach(function(deal) {
                    allDeals.push({
                        directDealConnectionId: ddc.id,
                        adminURL:
                            'https://one.zemanta.com/admin/dash/directdealconnection/' +
                            ddc.id +
                            '/change/',
                        description: deal.description,
                        dealId: deal.dealId,
                        level: ddc.level,
                        exclusive: ddc.exclusive,
                        source: ddc.source,
                    });
                });
            });
            return allDeals;
        }
    },
});
