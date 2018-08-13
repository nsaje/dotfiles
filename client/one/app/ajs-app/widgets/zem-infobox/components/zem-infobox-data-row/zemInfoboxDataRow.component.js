angular.module('one.widgets').component('zemInfoboxDataRow', {
    bindings: {
        row: '<',
    },
    template: require('./zemInfoboxDataRow.component.html'),
    controller: function() {
        var $ctrl = this;

        $ctrl.constants = constants;
    },
});
