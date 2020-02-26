var commonHelpers = require('../../../shared/helpers/common.helpers');
var routerHelpers = require('../../../shared/helpers/router.helpers');

angular
    .module('one.widgets')
    .service('zemHistoryService', function(
        $rootScope,
        $location,
        NgRouter,
        $timeout,
        $q,
        zemPubSubService,
        zemHistoryEndpoint
    ) {
        // eslint-disable-line max-len
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
        this.QUERY_PARAM = QUERY_PARAM;

        //
        // Public methods
        //
        function init() {
            $rootScope.$on('$locationChangeSuccess', handleLocationChange);
        }

        function open() {
            $location.search(QUERY_PARAM, true).replace();
            pubsub.notify(EVENTS.ON_OPEN);
        }

        function close() {
            clearParams();
            pubsub.notify(EVENTS.ON_CLOSE);
        }

        function clearParams() {
            $location.search(QUERY_PARAM, null).replace();
            var activatedRoute = routerHelpers.getActivatedRoute(NgRouter);
            var value = activatedRoute.snapshot.queryParams[QUERY_PARAM];
            if (commonHelpers.isDefined(value)) {
                var queryParams = commonHelpers.getValueWithoutProps(
                    $location.search(),
                    [QUERY_PARAM]
                );
                NgRouter.navigate([], {
                    relativeTo: activatedRoute,
                    queryParams: queryParams,
                });
            }
        }

        function loadHistory(entity, order) {
            var deferred = $q.defer();

            if (!entity || !entity.id || !entity.type) {
                deferred.reject();
            } else {
                zemHistoryEndpoint
                    .getHistory(entity.id, entity.type, order)
                    .then(function(data) {
                        deferred.resolve(formatHistoryData(data));
                    })
                    .catch(function(error) {
                        deferred.reject(error);
                    });
            }

            return deferred.promise;
        }

        //
        // Events
        //
        function onOpen(callback) {
            return pubsub.register(EVENTS.ON_OPEN, callback);
        }

        function onClose(callback) {
            return pubsub.register(EVENTS.ON_CLOSE, callback);
        }

        //
        // Private methods
        //

        function handleLocationChange() {
            var value = $location.search()[QUERY_PARAM];
            if (commonHelpers.isDefined(value)) {
                $timeout(function() {
                    pubsub.notify(EVENTS.ON_OPEN);
                });
            }
        }

        function formatHistoryData(data) {
            return data.map(function(item) {
                if (item.datetime) {
                    var datetime = moment(item.datetime);
                    item.datetime = datetime.isValid()
                        ? datetime.format('M/D/YYYY h:mm A')
                        : 'N/A';
                } else {
                    item.datetime = 'N/A';
                }
                return item;
            });
        }
    });
