angular.module('one.widgets').component('zemSidePanel', {
    transclude: true,
    bindings: {
        api: '<',
        onCloseRequest: '&'
    },
    templateUrl: '/app/common/components/zem-side-panel/zemSidePanel.component.html',
    controller: function ($window, hotkeys) {
        var $ctrl = this;

        $ctrl.requestClose = $ctrl.onCloseRequest;
        $ctrl.api.open = open;
        $ctrl.api.close = close;
        $ctrl.api.isVisible = isVisible;

        function isVisible () {
            return $ctrl.visible;
        }

        function isModalOpened () {
            // when uib modal opened, special class (.modal-open) is added to body
            return $('body').hasClass('modal-open');
        }

        function open () {
            $ctrl.visible = true;
            $window.scrollTo(0, 0);
            $('body').addClass('no-scroll');

            hotkeys.add({combo: 'esc', callback: function () {
                if (!isModalOpened()) $ctrl.requestClose();
            }});
        }

        function close () {
            $ctrl.visible = false;
            $('body').removeClass('no-scroll');
            hotkeys.del('esc');
        }
    }
});
