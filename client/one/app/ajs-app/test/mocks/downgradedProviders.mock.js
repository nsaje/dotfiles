var empty = require('rxjs').empty;
var of = require('rxjs').of;
var arrayHelpers = require('../../../shared/helpers/array.helpers');
var LevelParam = require('../../../app.constants').LevelParam;
var BreakdownParam = require('../../../app.constants').BreakdownParam;

angular
    .module('one.mocks.downgradedProviders', [])
    .service('zemEntitiesUpdatesService', function() {
        this.getAllUpdates$ = function() {
            return empty();
        };
        this.getUpdatesOfEntity$ = function() {
            return empty();
        };
    })
    .service('zemBidModifierUpdatesService', function() {
        this.getAllUpdates$ = function() {
            return empty();
        };
    })
    .service('zemAccountService', function() {
        this.list = function() {
            return empty();
        };
    })
    .service('zemPublishersService', function() {
        this.updateBlacklistStatuses = function() {
            return empty();
        };
    })
    .service('zemExceptionHandlerService', function() {
        this.handleHttpException = function() {
            return empty();
        };
        this.shouldRetryRequest = function() {
            return empty();
        };
        this.getRequestRetryTimeout = function() {
            return empty();
        };
    })
    .service('zemAlertsStore', function() {
        this.registerAlert = angular.noop;
        this.removeAlert = angular.noop;
    })
    .service('NgZone', function() {
        this.runOutsideAngular = function(fn) {
            fn();
        };
    })
    .service('NgRouter', function() {
        this.url = '/';
        this.routerState = {
            root: {
                firstChild: null,
                snapshot: {
                    data: {},
                    params: {},
                    queryParams: {},
                },
            },
        };
        this.events = of('/');
        this.browserUrlTree = {};

        this.createUrlTree = function(commands) {
            return {
                toString: function() {
                    if (arrayHelpers.isEmpty(commands)) {
                        return '/';
                    }
                    return '/' + commands.join('/');
                },
            };
        };

        this.navigateByUrl = function() {
            return true;
        };

        this.navigate = function(commands) {
            this.url = this.createUrlTree(commands).toString();
            var levelParams = this.getLevelParams(commands);
            this.routerState.root.snapshot.data = {
                level: levelParams,
            };
            var breakdownParams = this.getBreakdownParams(commands);
            this.routerState.root.snapshot.params = {
                breakdown: breakdownParams,
            };
            return true;
        };

        this.getLevelParams = function(commands) {
            if (arrayHelpers.isEmpty(commands)) {
                return null;
            }
            var levelParams = null;
            var levelsParams = [
                LevelParam.ACCOUNTS,
                LevelParam.ACCOUNT,
                LevelParam.CAMPAIGN,
                LevelParam.AD_GROUP,
            ];
            commands.forEach(function(command) {
                if (levelsParams.includes(command)) {
                    levelParams = command;
                    return;
                }
            });
            return levelParams;
        };

        this.getBreakdownParams = function(commands) {
            if (arrayHelpers.isEmpty(commands)) {
                return null;
            }
            var breakdownParams = null;
            var breakdownsParams = [
                BreakdownParam.SOURCES,
                BreakdownParam.PUBLISHERS,
                BreakdownParam.INSIGHTS,
                BreakdownParam.COUNTRY,
                BreakdownParam.STATE,
                BreakdownParam.DMA,
                BreakdownParam.DEVICE,
                BreakdownParam.PLACEMENT,
                BreakdownParam.OPERATING_SYSTEM,
            ];
            commands.forEach(function(command) {
                if (breakdownsParams.includes(command)) {
                    breakdownParams = command;
                    return;
                }
            });
            return breakdownParams;
        };
    });
