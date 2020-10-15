var Queue = require('promise-queue');

angular
    .module('one.widgets')
    .factory('zemGridDataService', function(
        $q,
        $timeout,
        zemGridParser,
        zemAlertsStore,
        zemGridConstants
    ) {
        // eslint-disable-line max-len

        // GridDataService is responsible to request data from DataSource and listen to any DataSource changes
        // It prepares data suitable for Grid component along with data states (initializing, loading, etc.) used
        // to communicate current data source status

        function GridDataService(grid, dataSource) {
            // Last notification cached to close it when new arrives (e.g. saving data)
            var lastNotification = null;

            var onMetaDataUpdatedHandler;
            var onDataUpdatedHandler;
            var onRowUpdatedHandler;
            var onStatsUpdatedHandler;

            var promiseQueue = null;

            //
            // Public API
            //
            this.initialize = initialize;
            this.destroy = destroy;
            this.loadMetaData = loadMetaData;
            this.loadData = loadData;
            this.replaceDataSource = replaceDataSource;
            this.saveData = saveData;
            this.saveDataQueued = saveDataQueued;

            //
            // Rewire calls to dataSource
            // DataSource can be replaced and this pattern is used to always access correct object
            //
            this.DS_FILTER = function() {
                return dataSource.FILTER;
            };
            this.setBreakdown = function() {
                return dataSource.setBreakdown.apply(dataSource, arguments);
            };
            this.getBreakdown = function() {
                return dataSource.getBreakdown.apply(dataSource, arguments);
            };
            this.getBreakdownLevel = function() {
                return dataSource.getBreakdownLevel.apply(
                    dataSource,
                    arguments
                );
            };
            this.setOrder = function() {
                return dataSource.setOrder.apply(dataSource, arguments);
            };
            this.getOrder = function() {
                return dataSource.getOrder.apply(dataSource, arguments);
            };
            this.setFilter = function() {
                return dataSource.setFilter.apply(dataSource, arguments);
            };
            this.getFilter = function() {
                return dataSource.getFilter.apply(dataSource, arguments);
            };
            this.updateData = function() {
                return dataSource.updateData.apply(dataSource, arguments);
            };
            this.isSaveRequestInProgress = function() {
                return dataSource.isSaveRequestInProgress.apply(
                    dataSource,
                    arguments
                );
            };
            this.editRow = function() {
                return dataSource.editRow.apply(dataSource, arguments);
            };

            function initialize() {
                promiseQueue = new Queue(1, Infinity);

                if (onMetaDataUpdatedHandler) onMetaDataUpdatedHandler();
                onMetaDataUpdatedHandler = dataSource.onMetaDataUpdated(
                    grid.meta.scope,
                    handleSourceMetaDataUpdate
                );
                if (onDataUpdatedHandler) onDataUpdatedHandler();
                onDataUpdatedHandler = dataSource.onDataUpdated(
                    grid.meta.scope,
                    handleSourceDataUpdate
                );
                if (onRowUpdatedHandler) onRowUpdatedHandler();
                onRowUpdatedHandler = dataSource.onRowUpdated(
                    grid.meta.scope,
                    handleSourceRowUpdate
                );
                if (onStatsUpdatedHandler) onStatsUpdatedHandler();
                onStatsUpdatedHandler = dataSource.onStatsUpdated(
                    grid.meta.scope,
                    handleSourceStatsUpdate
                );
            }

            function destroy() {
                if (onMetaDataUpdatedHandler) onMetaDataUpdatedHandler();
                if (onDataUpdatedHandler) onDataUpdatedHandler();
                if (onRowUpdatedHandler) onRowUpdatedHandler();
                if (onStatsUpdatedHandler) onStatsUpdatedHandler();
            }

            function loadMetaData() {
                var deferred = $q.defer();
                dataSource.loadMetaData().then(
                    function() {
                        // MetaData is already been processed
                        // on source metaData update event
                        deferred.resolve();
                    },
                    function(err) {
                        grid.meta.initialized = false;
                        deferred.reject(err);
                    }
                );
                return deferred.promise;
            }

            function loadData(row, offset, limit) {
                var breakdown;
                if (row) {
                    // When additional data (load more...) is requested
                    // breakdown row is passed as an argument
                    breakdown = row.data;
                }
                var deferred = $q.defer();
                grid.meta.loading = true;
                dataSource.loadData(breakdown, offset, limit).then(
                    function() {
                        // Workaround - goals/pixels are defined after initial data is loaded; therefor reload metadata
                        loadMetaData();
                        // Data is already been processed
                        // on source data update event
                        deferred.resolve();
                    },
                    function(err) {
                        if (grid.meta.loading && err) {
                            // Don't hide loader when initial request is aborted by user (e.g. filter updated)
                            // Workaround - err is in this case null (see zem_grid_endpoint_api.js abortable promise)
                            grid.meta.loading = false;
                        }
                        grid.meta.pubsub.notify(
                            grid.meta.pubsub.EVENTS.DATA_UPDATED_ERROR,
                            err
                        );
                        deferred.reject(err);
                    }
                );
                return deferred.promise;
            }

            function replaceDataSource(_dataSource) {
                dataSource = _dataSource;

                initialize();

                zemGridParser.clear(grid);
                zemGridParser.parseMetaData(grid, dataSource.getMetaData());
                zemGridParser.parse(grid, dataSource.getData());

                if (
                    grid.meta.renderingEngine ===
                    zemGridConstants.gridRenderingEngineType.CUSTOM_GRID
                ) {
                    // [OPTIMIZATION] Speed up first render (e.g. tab switch)
                    // Only prepare/render first 10 rows an after that show all data
                    grid.body.rows = grid.body.rows.slice(0, 10);
                    $timeout(function() {
                        // Render All Data
                        zemGridParser.parse(grid, dataSource.getData());
                        grid.meta.pubsub.notify(
                            grid.meta.pubsub.EVENTS.DATA_UPDATED
                        );
                    });
                }

                grid.meta.pubsub.notify(
                    grid.meta.pubsub.EVENTS.METADATA_UPDATED
                );
                grid.meta.pubsub.notify(grid.meta.pubsub.EVENTS.DATA_UPDATED);
            }

            function saveData(value, row, column) {
                var deferred = $q.defer();
                dataSource.saveData(value, row.data, column.data).then(
                    function(data) {
                        if (data.notification)
                            showNotification(data.notification);
                    },
                    function(err) {
                        deferred.reject(err);
                    }
                );
                return deferred.promise;
            }

            function saveDataQueued(value, row, column) {
                promiseQueue
                    .add(function() {
                        return dataSource.saveData(
                            value,
                            row.data,
                            column.data
                        );
                    })
                    .then(function(data) {
                        if (data.notification) {
                            showNotification(data.notification);
                        }
                    })
                    .catch(function(error) {
                        grid.meta.pubsub.notify(
                            grid.meta.pubsub.EVENTS.ROW_UPDATED_ERROR,
                            {
                                row: row,
                                error: error,
                            }
                        );
                    });
            }

            function showNotification(notification) {
                if (lastNotification) {
                    zemAlertsStore.removeAlert(lastNotification);
                }
                lastNotification = {
                    type: notification.type,
                    message: notification.message,
                    isClosable: true,
                };
                zemAlertsStore.registerAlert(lastNotification);
            }

            function handleSourceMetaDataUpdate(event, metaData) {
                zemGridParser.parseMetaData(grid, metaData);
                grid.meta.initialized = true;
                grid.meta.pubsub.notify(
                    grid.meta.pubsub.EVENTS.METADATA_UPDATED
                );
            }

            function handleSourceDataUpdate(event, data) {
                zemGridParser.parse(grid, data);
                grid.meta.loading = !data.breakdown;
                grid.meta.pubsub.notify(grid.meta.pubsub.EVENTS.DATA_UPDATED);
            }

            function handleSourceRowUpdate(event, data) {
                grid.meta.pubsub.notify(
                    grid.meta.pubsub.EVENTS.ROW_UPDATED,
                    data
                );
            }

            function handleSourceStatsUpdate() {
                grid.meta.pubsub.notify(grid.meta.pubsub.EVENTS.DATA_UPDATED);
            }
        }

        return {
            createInstance: function(grid, dataSource) {
                return new GridDataService(grid, dataSource);
            },
        };
    });
