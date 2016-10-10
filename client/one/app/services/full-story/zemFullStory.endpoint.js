angular.module('one.services').service('zemFullStoryEndpoint', ['$http', function ($http) {
    this.allowLivestream = allowLivestream;

    function allowLivestream (sessionUrl) {
        var url = '/api/live-stream/allow/';
        return $http.post(url, {
            session_url: sessionUrl,
        });
    }
}]);
