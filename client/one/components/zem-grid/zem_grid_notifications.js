/* globals oneApp */
'use strict';

oneApp.directive('zemGridNotifications', [function () {

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_notifications.html',
        controller: [function () {
            var vm = this;
            var pubsub = this.grid.meta.pubsub;
            var notificationService = this.grid.meta.notificationService;

            initialize();

            function initialize () {
                initializeNotifications();
                pubsub.register(pubsub.EVENTS.EXT_NOTIFICATIONS_UPDATED, initializeNotifications);
            }

            function initializeNotifications () {
                vm.notifications = notificationService.getNotifications();
            }
        }],
    };
}]);
