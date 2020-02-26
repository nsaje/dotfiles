angular
    .module('one.widgets')
    .service('zemAdGroupSourcesStateService', function(
        $q,
        zemNavigationNewService,
        zemDataFilterService,
        zemAdGroupSourcesEndpoint
    ) {
        //eslint-disable-line max-len

        function StateService(adGroup) {
            var state = {
                sources: [],
                requests: {
                    list: null,
                    create: null,
                },
            };

            // Public API
            this.getState = getState;
            this.initialize = initialize;
            this.list = list;
            this.create = create;

            function initialize() {
                list();
            }

            function getState() {
                return state;
            }

            function create(sourceId) {
                state.requests.create = {};
                state.requests.create.inProgress = true;
                return zemAdGroupSourcesEndpoint
                    .create(adGroup.id, sourceId)
                    .then(
                        function() {
                            zemNavigationNewService.reloadCurrentRoute();
                        },
                        function(err) {
                            state.requests.create.error = true;
                            return $q.reject(err);
                        }
                    )
                    .finally(function() {
                        state.requests.create.inProgress = false;
                    });
            }

            function list() {
                state.requests.list = {};
                state.requests.list.inProgress = true;
                var config = {
                    filteredSources: zemDataFilterService.getFilteredSources(),
                };
                zemAdGroupSourcesEndpoint
                    .list(adGroup.id, config)
                    .then(
                        function(data) {
                            state.sources = [];
                            for (
                                var source, i = 0;
                                i < data.sources.length;
                                i++
                            ) {
                                source = data.sources[i];

                                var notificationMsg = '';
                                if (!source.canTargetExistingRegions) {
                                    notificationMsg =
                                        source.name +
                                        " doesn't support DMA targeting. " +
                                        'Turn off DMA targeting to add ' +
                                        source.name +
                                        '.';
                                }
                                if (!source.canRetarget) {
                                    notificationMsg =
                                        (notificationMsg
                                            ? notificationMsg + ' '
                                            : '') +
                                        source.name +
                                        " doesn't support retargeting. " +
                                        'Turn off retargeting to add ' +
                                        source.name +
                                        '.';
                                }
                                state.sources.push({
                                    name: source.name,
                                    value: source.id,
                                    hasPermission: true,
                                    disabled:
                                        !source.canTargetExistingRegions ||
                                        !source.canRetarget,
                                    notification: notificationMsg,
                                });
                            }
                        },
                        function(err) {
                            state.requests.list.error = true;
                            return $q.reject(err);
                        }
                    )
                    .finally(function() {
                        state.requests.list.inProgress = false;
                    });
            }
        }

        return {
            getInstance: function(account) {
                return new StateService(account);
            },
        };
    });
