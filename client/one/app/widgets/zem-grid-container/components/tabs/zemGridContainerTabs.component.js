angular.module('one.widgets').component('zemGridContainerTabs', {
    templateUrl: '/app/widgets/zem-grid-container/components/tabs/zemGridContainerTabs.component.html',
    bindings: {
        options: '<',
        onSelected: '&',
    },
    controller: function () {
        var $ctrl = this;

        $ctrl.$onInit = function () {
            // TODO: Initially selected option based on input
            $ctrl.selectedOption = $ctrl.options[0];
        };

        $ctrl.selectOption = function (option) {
            if ($ctrl.selectedOption === option) return;
            $ctrl.selectedOption = option;
            $ctrl.onSelected({option: option});
        };
    },
});
