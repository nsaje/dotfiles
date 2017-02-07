angular.module('one.widgets').service('zemSettingsService', function ($rootScope, $location, $state, $timeout, zemPubSubService, zemNavigationNewService) { // eslint-disable-line max-len
    var QUERY_PARAM = 'settings';

    var EVENTS = {
        ON_OPEN: 'zem-settings-open',
        ON_CLOSE: 'zem-settings-close',
    };
    var pubsub = zemPubSubService.createInstance();
    var currentEntity;
    var areSettingsOpen;

    this.init = init;
    this.open = open;
    this.close = close;
    this.getCurrentEntity = getCurrentEntity;

    this.onOpen = onOpen;
    this.onClose = onClose;

    function init () {
        $rootScope.$on('$stateChangeSuccess', handleStateChange);
        // Listen for $locationChangeSuccess to open settings when query parameter is added to URL without state change
        $rootScope.$on('$locationChangeSuccess', handleLocationChange);
    }

    function handleStateChange () {
        var value = $location.search()[QUERY_PARAM] || $state.params[QUERY_PARAM];
        if (value) {
            $timeout(function () {
                open();
            }, 2000);
        }
    }

    function handleLocationChange () {
        var value = $location.search()[QUERY_PARAM];
        if (value && !areSettingsOpen) {
            open();
        }
    }

    function open (entity) {
        areSettingsOpen = true;
        $location.search(QUERY_PARAM, true);
        currentEntity = entity || zemNavigationNewService.getActiveEntity();
        if (currentEntity !== null) pubsub.notify(EVENTS.ON_OPEN, currentEntity);
    }

    function close () {
        areSettingsOpen = false;
        $location.search(QUERY_PARAM, null);
        currentEntity = null;
        pubsub.notify(EVENTS.ON_CLOSE);
    }

    function getCurrentEntity () {
        return currentEntity;
    }


    function onOpen (callback) {
        return pubsub.register(EVENTS.ON_OPEN, callback);
    }

    function onClose (callback) {
        return pubsub.register(EVENTS.ON_CLOSE, callback);
    }
});
