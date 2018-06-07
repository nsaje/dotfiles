angular.module('one.widgets').service('zemConversionPixelsStateService', function ($q, $http, zemPubSubService, zemDataFilterService, zemConversionPixelsEndpoint) { //eslint-disable-line max-len

    function StateService (account) {

        //
        // State Object
        //
        var state = {
            conversionPixels: [],
            tagPrefix: '',
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
        this.create = create;
        this.update = update;
        this.archive = archive;
        this.restore = restore;
        this.clearRequestError = clearRequestError;

        ///////////////////////////////////////////////////////////////////////////////////////////////
        // Internals
        //
        var filteredStatusesUpdateHandler;
        var conversionPixelsCache = [];

        function initialize () {
            filteredStatusesUpdateHandler = zemDataFilterService.onFilteredStatusesUpdate(function () {
                state.conversionPixels = conversionPixelsCache.filter(filterPixelsByStatus);
            });

            return getConversionPixels();
        }

        function destroy () {
            if (filteredStatusesUpdateHandler) filteredStatusesUpdateHandler();
        }

        function getState () {
            return state;
        }

        function getConversionPixels () {
            state.requests.list = {};
            state.requests.list.inProgress = true;
            return zemConversionPixelsEndpoint.list(account.id).then(
                function (data) {
                    conversionPixelsCache = data.rows;
                    state.conversionPixels = conversionPixelsCache.filter(filterPixelsByStatus);
                    state.tagPrefix = data.tagPrefix;
                },
                function () {
                    state.requests.list.error = true;
                    $q.reject();
                }
            ).finally(function () {
                state.requests.list.inProgress = false;

            });
        }

        function create (pixel) {
            state.requests.create = {};
            state.requests.create.inProgress = true;
            return zemConversionPixelsEndpoint.post(account.id, pixel).then(
                function (data) {
                    conversionPixelsCache.push(data);
                    state.conversionPixels = conversionPixelsCache.filter(filterPixelsByStatus);
                },
                function (data) {
                    if (data && data.errors) {
                        state.requests.create.validationErrors = data.errors;
                    } else {
                        state.requests.create.error = true;
                    }

                    return $q.reject();
                }
            ).finally(function () {
                state.requests.create.inProgress = false;
            });
        }

        function update (pixel) {
            state.requests.update[pixel.id] = {inProgress: true};
            return zemConversionPixelsEndpoint.put(pixel.id, pixel).then(
                function (data) {
                    angular.extend(getPixelById(pixel.id), data);
                    state.conversionPixels = conversionPixelsCache.filter(filterPixelsByStatus);
                },
                function (data) {
                    if (data && data.errors) {
                        state.requests.update[pixel.id].validationErrors = data.errors;
                    } else {
                        state.requests.update[pixel.id].error = true;
                    }
                    return $q.reject();
                }
            ).finally(function () {
                state.requests.update[pixel.id].inProgress = false;
            });
        }

        function archive (conversionPixel) {
            state.requests.archive[conversionPixel.id] = {inProgress: true};
            return zemConversionPixelsEndpoint.archive(conversionPixel).then(
                function (data) {
                    conversionPixel.archived = data.archived;
                },
                function () {
                    state.requests.archive[conversionPixel.id].error = true;
                    $q.reject();
                }
            ).finally(function () {
                state.requests.archive[conversionPixel.id].inProgress = false;
            });
        }


        function restore (conversionPixel) {
            state.requests.restore[conversionPixel.id] = {inProgress: true};
            return zemConversionPixelsEndpoint.restore(conversionPixel).then(
                function (data) {
                    conversionPixel.archived = data.archived;
                },
                function () {
                    state.requests.restore[conversionPixel.id].error = true;
                    $q.reject();
                }
            ).finally(function () {
                state.requests.restore[conversionPixel.id].inProgress = false;
            });
        }

        function getPixelById (id) {
            return conversionPixelsCache.filter(function (pixel) { return pixel.id === id; })[0];
        }

        function filterPixelsByStatus (pixel) {
            if (zemDataFilterService.getShowArchived()) {
                return true;
            }
            return !pixel.archived;
        }

        function clearRequestError (request, validationErrorField) {
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
        getInstance: function (account) {
            return new StateService(account);
        }
    };
});
