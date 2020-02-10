require('./zemFooter.component.less');

angular.module('one.widgets').component('zemFooter', {
    template: require('./zemFooter.component.html'),
    controller: function(config) {
        var $ctrl = this;
        $ctrl.config = config;
    },
});
