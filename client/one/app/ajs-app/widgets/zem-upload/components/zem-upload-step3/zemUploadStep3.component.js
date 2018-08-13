angular.module('one.widgets').directive('zemUploadStep3', function() {
    // eslint-disable-line max-len
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        bindToController: {
            callback: '&',
            numSuccessful: '=',
            adGroup: '=',
            close: '=',
            onSave: '=',
        },
        controllerAs: 'ctrl',
        template: require('./zemUploadStep3.component.html'),
        controller: function(config) {
            var vm = this;
            vm.config = config;

            if (vm.onSave) {
                vm.onSave();
            }
        },
    };
});
