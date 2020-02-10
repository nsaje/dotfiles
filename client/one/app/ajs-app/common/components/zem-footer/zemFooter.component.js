require('./zemFooter.component.less');

angular.module('one.common').component('zemFooter', {
    template: require('./zemFooter.component.html'),
    controller: function(config) {
        var $ctrl = this;
        $ctrl.config = config;
    },
});
