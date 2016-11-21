angular.module('one.widgets').component('zemSidePanel', {
    transclude: true,
    bindings: {
        api: '<',
        onClose: '&'
    },
    templateUrl: '/app/common/components/zem-side-panel/zemSidePanel.component.html',
    controller: function ($window, hotkeys) {
        var $ctrl = this;

        $ctrl.close = close;
        $ctrl.api.open = open;
        $ctrl.api.close = close;
        $ctrl.api.isVisible = isVisible;

        $ctrl.$onInit = function () {
            hotkeys.add({combo: 'esc', callback: function () { close(); }});
        };

        function isVisible () {
            return $ctrl.visible;
        }

        function open () {
            $ctrl.visible = true;
            $window.scrollTo(0, 0);
            $('body').addClass('no-scroll');
        }

        function close () {
            $ctrl.visible = false;
            $('body').removeClass('no-scroll');
            $ctrl.onClose();
        }
    }
});
