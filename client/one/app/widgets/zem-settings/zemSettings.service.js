angular.module('one.widgets').service('zemSettingsService', function ($rootScope, $location, $state, $timeout, zemPubSubService, zemNavigationNewService) { // eslint-disable-line max-len
    var QUERY_PARAM = 'settings';
    var QUERY_VALUE_CREATE = 'create';

    var EVENTS = {
        ON_OPEN: 'zem-settings-open',
        ON_CLOSE: 'zem-settings-close',
    };
    var pubsub = zemPubSubService.createInstance();
    var currentEntity;

    this.init = init;
    this.open = open;
    this.close = close;
    this.getCurrentEntity = getCurrentEntity;

    this.onOpen = onOpen;
    this.onClose = onClose;

    function init () {
        $rootScope.$on('$stateChangeSuccess', handleStateChange);
    }

    function handleStateChange () {
        var value = $location.search()[QUERY_PARAM];
        if (value) {
            $timeout(function () {
                open();
            }, 2000);
        }
    }

    function open (entity) {
        $location.search(QUERY_PARAM, true);
        currentEntity = entity || zemNavigationNewService.getActiveEntity();
        if (currentEntity !== null) pubsub.notify(EVENTS.ON_OPEN, currentEntity);
    }

    function close () {
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
