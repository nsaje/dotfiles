angular.module('one.common').service('zemPubSubService', function($rootScope) {
    this.createInstance = createInstance;

    function PubSub() {
        this.register = register;
        this.notify = notify;
        this.destroy = destroy;

        var $scope = $rootScope.$new();
        function destroy() {
            return $scope.$destroy();
        }

        function register(event, listener) {
            var handler = $scope.$on(event, listener);
            $scope.$on('$destroy', handler);
            return handler;
        }

        function notify(event, data) {
            $scope.$broadcast(event, data);
        }
    }

    function createInstance() {
        return new PubSub();
    }
});
