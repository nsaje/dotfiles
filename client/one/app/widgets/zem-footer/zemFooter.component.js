angular.module('one.widgets').component('zemFooter', {
    templateUrl: '/app/widgets/zem-footer/zemFooter.component.html',
    controller: function (config) {
        var $ctrl = this;
        $ctrl.config = config;
    },
});
