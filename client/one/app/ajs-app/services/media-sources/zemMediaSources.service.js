angular.module('one.services').service('zemMediaSourcesService', function ($http, $q, zemMediaSourcesEndpoint, zemPubSubService) { // eslint-disable-line max-len
    this.init = init;
    this.getSources = getSources;
    this.getAvailableSources = getAvailableSources;

    this.onSourcesUpdate = onSourcesUpdate;

    var pubSub = zemPubSubService.createInstance();
    var EVENTS = {
        ON_SOURCES_UPDATE: 'zem-media-sources-service-on-sources-update',
    };

    var sources;

    function init () {
        loadSources();
    }

    function getSources (reload) {
        var deferred = $q.defer();

        if (!reload && sources) {
            deferred.resolve(sources);
        } else {
            loadSources().then(function () {
                deferred.resolve(sources);
            });
        }

        return deferred.promise;
    }

    function getAvailableSources (reload) {
        var deferred = $q.defer();

        if (!reload && sources) {
            deferred.resolve(sources.filter(function (source) {
                return !source.deprecated;
            }));
        } else {
            getSources(reload).then(function () {
                var availableSources = sources.filter(function (source) {
                    return !source.deprecated;
                });
                deferred.resolve(availableSources);
            });
        }

        return deferred.promise;
    }


    function onSourcesUpdate (callback) {
        return pubSub.register(EVENTS.ON_SOURCES_UPDATE, callback);
    }


    function loadSources () {
        return zemMediaSourcesEndpoint.getSources().then(function (data) {
            sources = data.data.sources;
            pubSub.notify(EVENTS.ON_SOURCES_UPDATE, sources);
        });
    }
});
