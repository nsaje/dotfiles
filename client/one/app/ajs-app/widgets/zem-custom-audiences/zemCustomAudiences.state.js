angular
    .module('one.widgets')
    .service('zemCustomAudiencesStateService', function(
        $q,
        $http,
        zemDataFilterService,
        zemPubSubService,
        zemCustomAudiencesEndpoint,
        zemConversionPixelsEndpoint
    ) {
        //eslint-disable-line max-len

        function StateService(account) {
            //
            // State Object
            //
            var state = {
                audiences: {},
                audiencesList: [],
                audiencePixels: [],
                requests: {
                    create: null,
                    list: null,
                    get: {},
                    update: {},
                    archive: {},
                    restore: {},
                },
            };

            //
            // Public API
            //
            this.getState = getState;
            this.initialize = initialize;
            this.destroy = destroy;

            this.get = get;
            this.create = create;
            this.update = update;
            this.archive = archive;
            this.restore = restore;
            this.list = list;
            this.clearRequestError = clearRequestError;
            this.listAudiencePixels = listAudiencePixels;

            //
            // Handlers
            //
            var filteredStatusesUpdateHandler;

            ///////////////////////////////////////////////////////////////////////////////////////////////
            // Internals
            //
            function initialize() {
                filteredStatusesUpdateHandler = zemDataFilterService.onFilteredStatusesUpdate(
                    list
                );

                return $q.all(list(), listAudiencePixels()).then(function() {
                    state.initialized = true;
                });
            }

            function destroy() {
                if (filteredStatusesUpdateHandler)
                    filteredStatusesUpdateHandler();
            }

            function getState() {
                return state;
            }

            function create(audienceData) {
                state.requests.create = {inProgress: true};
                return zemCustomAudiencesEndpoint
                    .post(account.id, audienceData)
                    .then(
                        function(data) {
                            state.audiences[data.id] = data;
                            list(); // refresh audiences list
                        },
                        function(errors) {
                            state.requests.create.validationErrors = errors;
                            return $q.reject(errors);
                        }
                    )
                    .finally(function() {
                        state.requests.create.inProgress = false;
                    });
            }

            function update(audienceId, data) {
                state.requests.update[audienceId] = {inProgress: true};
                return zemCustomAudiencesEndpoint
                    .put(account.id, audienceId, data)
                    .then(
                        function() {
                            list(); // refresh audiences list
                        },
                        function(errors) {
                            state.requests.update[
                                audienceId
                            ].validationErrors = errors;
                            return $q.reject(errors);
                        }
                    )
                    .finally(function() {
                        state.requests.update[audienceId].inProgress = false;
                    });
            }

            function get(audienceId) {
                state.requests.get[audienceId] = {inProgress: true};
                return zemCustomAudiencesEndpoint
                    .get(account.id, audienceId)
                    .then(function(data) {
                        state.audiences[audienceId] = data;
                        return data;
                    })
                    .finally(function() {
                        state.requests.get[audienceId].inProgress = false;
                    });
            }

            function list() {
                state.requests.list = {inProgress: true};

                var showArchived = zemDataFilterService.getShowArchived();

                return zemCustomAudiencesEndpoint
                    .list(account.id, showArchived, true)
                    .then(function(data) {
                        for (var i = 0; i < data.length; i++) {
                            data[i].count = data[i].count || 'N/A';
                            data[i].countYesterday =
                                data[i].countYesterday || 'N/A';
                        }
                        state.audiencesList = data;
                        return data;
                    })
                    .finally(function() {
                        state.requests.list.inProgress = false;
                    });
            }

            function archive(audience) {
                state.requests.archive[audience.id] = {inProgress: true};
                return zemCustomAudiencesEndpoint
                    .archive(account.id, audience.id)
                    .then(
                        function() {
                            audience.archived = true;
                            return audience;
                        },
                        function(errors) {
                            state.requests.archive.validationErrors = errors;
                            return $q.reject(errors);
                        }
                    )
                    .finally(function() {
                        state.requests.archive[audience.id].inProgress = false;
                    });
            }

            function restore(audience) {
                state.requests.restore[audience.id] = {inProgress: true};
                return zemCustomAudiencesEndpoint
                    .restore(account.id, audience.id)
                    .then(function() {
                        audience.archived = false;
                        return audience;
                    })
                    .finally(function() {
                        state.requests.restore[audience.id].inProgress = false;
                    });
            }

            function listAudiencePixels() {
                return zemConversionPixelsEndpoint
                    .list(account.id)
                    .then(function(data) {
                        if (data.rows) {
                            state.audiencePixels = data.rows.filter(function(
                                pixel
                            ) {
                                return (
                                    pixel.audienceEnabled ||
                                    pixel.additionalPixel
                                );
                            });

                            return state.audiencePixels;
                        }
                    });
            }

            function clearRequestError(request, validationErrorField) {
                if (!request) return;

                if (validationErrorField) {
                    if (request.validationErrors) {
                        delete request.validationErrors[validationErrorField];
                    }
                } else {
                    delete request.validationErrors;
                    delete request.errors;
                }
            }
        }

        return {
            getInstance: function(account) {
                return new StateService(account);
            },
        };
    });
