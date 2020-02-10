require('./zemHistory.component.less');

angular.module('one.common').component('zemHistory', {
    template: require('./zemHistory.component.html'),
    controller: function(hotkeys, zemHistoryService, zemNavigationNewService) {
        var $ctrl = this;
        $ctrl.close = zemHistoryService.close;
        $ctrl.changeOrder = changeOrder;

        var openHistoryHandler, closeHistoryHandler;

        $ctrl.$onInit = function() {
            zemHistoryService.init();

            $ctrl.sidePanel = {};
            $ctrl.orderField = 'datetime';
            $ctrl.orderReversed = true;

            openHistoryHandler = zemHistoryService.onOpen(open);
            closeHistoryHandler = zemHistoryService.onClose(close);

            hotkeys.add({
                combo: 'h',
                callback: function() {
                    zemHistoryService.open();
                },
            });
        };

        $ctrl.$onDestroy = function() {
            if (openHistoryHandler) openHistoryHandler();
            if (closeHistoryHandler) closeHistoryHandler();
            hotkeys.del('h');
        };

        function open() {
            $ctrl.sidePanel.open();
            reloadHistory();
        }

        function close() {
            $ctrl.sidePanel.close();
            $ctrl.history = null;
            $ctrl.requestInProgress = false;
        }

        function reloadHistory() {
            var entity = zemNavigationNewService.getActiveEntity();
            var order = (($ctrl.orderReversed && '-') || '') + $ctrl.orderField;

            $ctrl.history = null;
            $ctrl.requestInProgress = true;

            zemHistoryService
                .loadHistory(entity, order)
                .then(function(history) {
                    $ctrl.history = history;
                })
                .finally(function() {
                    $ctrl.requestInProgress = false;
                });
        }

        function changeOrder(field) {
            $ctrl.orderField = field;
            $ctrl.orderReversed = !$ctrl.orderReversed;
            reloadHistory();
        }
    },
});
