angular
    .module('one.widgets')
    .service('zemDemoRequestEndpoint', function($http) {
        this.requestDemo = requestDemo;

        function requestDemo() {
            var url = '/api/demov3/';
            return $http.get(url);
        }
    });
