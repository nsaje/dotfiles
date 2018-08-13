angular.module('one.mocks.NgZone', []).service('NgZone', function() {
    this.runOutsideAngular = runOutsideAngular;

    function runOutsideAngular(fn) {
        fn();
    }
});
