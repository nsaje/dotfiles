angular.module('one.widgets').service('zemCampaignLauncherEndpoint', function ($q, $http) {
    this.validate = validate;
    this.launchCampaign = launchCampaign;

    function validate (account, fields) {
        var deferred = $q.defer();
        var url = '/rest/internal/accounts/' + account.id + '/campaignlauncher/validate';
        $http.post(url, fields)
            .then(function () {
                deferred.resolve();
            })
            .catch(function (response) {
                deferred.reject(response.data);
            });
        return deferred.promise;
    }

    function launchCampaign (account, fields) {
        var deferred = $q.defer();
        var url = '/rest/internal/accounts/' + account.id + '/campaignlauncher';
        $http.post(url, fields)
            .then(function (response) {
                deferred.resolve(response.data.data.campaignId);
            })
            .catch(function (response) {
                deferred.reject(response.data);
            });
        return deferred.promise;
    }
});
