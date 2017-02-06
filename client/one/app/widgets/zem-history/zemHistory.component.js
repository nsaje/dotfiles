angular.module('one.widgets').component('zemHistory', {
    templateUrl: '/app/widgets/zem-history/zemHistory.component.html',
    controller: function (hotkeys, zemHistoryService, zemNavigationNewService) {
        var $ctrl = this;
        $ctrl.close = zemHistoryService.close;
        $ctrl.changeOrder = changeOrder;

        $ctrl.$onInit = function () {
            $ctrl.sidePanel = {};
            $ctrl.orderField = 'datetime';
            $ctrl.orderReversed = false;

            zemHistoryService.onOpen(open);
            zemHistoryService.onClose(close);

            hotkeys.add({combo: 'h', callback: function () { zemHistoryService.open(); }});
        };

        function open () {
            $ctrl.sidePanel.open();
            reloadHistory();
        }

        function close () {
            $ctrl.sidePanel.close();
            $ctrl.history = null;
            $ctrl.requestInProgress = false;
        }

        function reloadHistory () {
            var entity = zemNavigationNewService.getActiveEntity();
            var order = ($ctrl.orderReversed && '-' || '') + $ctrl.orderField;

            $ctrl.history = null;
            $ctrl.requestInProgress = true;

            zemHistoryService.loadHistory(entity, order)
                .then(function (history) {
                    $ctrl.history = history;
                })
                .finally(function () {
                    $ctrl.requestInProgress = false;
                });
        }

        function changeOrder (field) {
            $ctrl.orderField = field;
            $ctrl.orderReversed = !$ctrl.orderReversed;
            reloadHistory();
        }
    },
});
