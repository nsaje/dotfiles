angular.module('one.services').service('zemUserEndpoint', ['$q', '$http', function ($q, $http) {
    this.loadUser = loadUser;

    function loadUser (id) {
        var deferred = $q.defer();
        var url = '/api/users/' + id + '/';
        var config = {
            params: {},
        };

        $http.get(url, config).
            success(function (data) {
                var user;
                if (data && data.data) {
                    user = data.data.user;
                }
                deferred.resolve(convertFromApi(user));
            }).
            error(function (data) {
                deferred.reject(data);
            });

        return deferred.promise;

        function convertFromApi (user) {
            return {
                id: user.id,
                name: user.name,
                email: user.email,
                agency: user.agency,
                permissions: user.permissions,
                timezoneOffset: user.timezone_offset,
            };
        }
    }
}]);
