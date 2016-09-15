angular.module('one.widgets').component('zemHeader', {
    bindings: {
        level: '=',
        enablePublisherFilter: '=',
        showPublisherSelected: '=',
    },
    templateUrl: '/app/widgets/zem-header/zemHeader.component.html',
    controller: ['config', function (config) {
        var $ctrl = this;
        $ctrl.config = config;
    }],
});
