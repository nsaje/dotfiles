angular.module('one.widgets').service('zemSettingsService', function ($rootScope, $location, $state, $timeout, zemPubSubService, zemNavigationNewService) { // eslint-disable-line max-len
    var QUERY_PARAM = 'settings';
    var QUERY_SCROLL_TO_PARAM = 'settingsScrollTo';

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
        handleStateChange();
        handleLocationChange();

        $rootScope.$on('$stateChangeSuccess', handleStateChange);
        $rootScope.$on('$locationChangeSuccess', handleLocationChange);

        if (zemNavigationNewService.getActiveEntity() === undefined) {
            var unsubscribe = zemNavigationNewService.onActiveEntityChange(function () {
                // Wait until active entity is initialized and then check if settings needs to be opened
                handleLocationChange();
                unsubscribe();
            });
        }
    }

    function handleStateChange () {
        // Support for $state params (settings, settingsScrollTo)
        // If settings parameters set when using $state transition pass it to the $location.search
        // which will trigger change event which is again handled in this service
        var value = $state.params[QUERY_PARAM];
        if (value) {
            $location.search(QUERY_PARAM, true);
            $location.search(QUERY_SCROLL_TO_PARAM, $state.params[QUERY_SCROLL_TO_PARAM]);
        }
    }

    function handleLocationChange () {
        var value = $location.search()[QUERY_PARAM];
        if (value) {
            $timeout(function () {
                var entity = zemNavigationNewService.getActiveEntity();
                var scrollTo = $location.search()[QUERY_SCROLL_TO_PARAM];
                open(entity, scrollTo);
            });
        }
    }

    function open (entity, scrollToComponent) {
        entity = entity || zemNavigationNewService.getActiveEntity();

        if (entity !== null && currentEntity !== entity) {
            currentEntity = entity;
            pubsub.notify(EVENTS.ON_OPEN, {
                entity: currentEntity,
                scrollToComponent: scrollToComponent,
            });
            $location.search(QUERY_PARAM, true);
            $location.search(QUERY_SCROLL_TO_PARAM, scrollToComponent);
        }
    }

    function close () {
        $location.search(QUERY_PARAM, null);
        $location.search(QUERY_SCROLL_TO_PARAM, null);
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
