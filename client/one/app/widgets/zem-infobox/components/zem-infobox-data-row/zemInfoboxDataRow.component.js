angular.module('one.widgets').component('zemInfoboxDataRow', {
    bindings: {
        row: '<',
    },
    templateUrl: '/app/widgets/zem-infobox/components/zem-infobox-data-row/zemInfoboxDataRow.component.html',
    controller: function () {
        var $ctrl = this;

        $ctrl.constants = constants;
    },
});
