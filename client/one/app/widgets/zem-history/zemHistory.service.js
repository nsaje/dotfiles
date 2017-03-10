angular.module('one.widgets').service('zemHistoryService', function ($rootScope, $location, $state, $timeout, $q, zemPubSubService, zemHistoryEndpoint) { // eslint-disable-line max-len
    this.init = init;
    this.open = open;
    this.close = close;
    this.loadHistory = loadHistory;

    this.onOpen = onOpen;
    this.onClose = onClose;


    var pubsub = zemPubSubService.createInstance();
    var EVENTS = {
        ON_OPEN: 'zem-history-open',
        ON_CLOSE: 'zem-history-close',
    };

    var QUERY_PARAM = 'history';


    //
    // Public methods
    //
    function init () {
        handleStateChange();
        $rootScope.$on('$stateChangeSuccess', handleStateChange);
        $rootScope.$on('$locationChangeSuccess', handleLocationChange);
    }

    function open () {
        $location.search(QUERY_PARAM, true);
        pubsub.notify(EVENTS.ON_OPEN);
    }

    function close () {
        $location.search(QUERY_PARAM, null);
        pubsub.notify(EVENTS.ON_CLOSE);
    }

    function loadHistory (entity, order) {
        var deferred = $q.defer();

        if (!entity || !entity.id || !entity.type) {
            deferred.reject();
        } else {
            zemHistoryEndpoint.getHistory(entity.id, entity.type, order)
                .then(function (data) {
                    deferred.resolve(formatHistoryData(data));
                })
                .catch(function (error) {
                    deferred.reject(error);
                });
        }

        return deferred.promise;
    }


    //
    // Events
    //
    function onOpen (callback) {
        return pubsub.register(EVENTS.ON_OPEN, callback);
    }

    function onClose (callback) {
        return pubsub.register(EVENTS.ON_CLOSE, callback);
    }


    //
    // Private methods
    //
    function handleStateChange () {
        // Support for $state params (history)
        // If settings parameters set when using $state transition pass it to the $location.search
        // which will trigger change event which is again handled in this service
        var value = $state.params[QUERY_PARAM];
        if (value) {
            $location.search(QUERY_PARAM, true);
        }
    }

    function handleLocationChange () {
        var value = $location.search()[QUERY_PARAM];
        if (value) {
            $timeout(function () {
                open();
            });
        }
    }

    function formatHistoryData (data) {
        return data.map(function (item) {
            if (item.datetime) {
                var datetime = moment(item.datetime);
                item.datetime = datetime.isValid() ? datetime.format('M/D/YYYY h:mm A') : 'N/A';
            } else {
                item.datetime = 'N/A';
            }
            return item;
        });
    }
});
