angular
    .module('one.widgets')
    .factory('zemGridDataService', function(
        $q,
        $timeout,
        zemGridParser,
        zemAlertsService
    ) {
        // eslint-disable-line max-len

        // GridDataService is responsible to request data from DataSource and listen to any DataSource changes
        // It prepares data suitable for Grid component along with data states (initializing, loading, etc.) used
        // to communicate current data source status

        function GridDataService(grid, dataSource) {
            // Last notification cached to close it when new arrives (e.g. saving data)
            var lastNotification = null;

            var onStatsUpdatedHandler;
            var onDataUpdatedHandler;

            //
            // Public API
            //
            this.initialize = initialize;
            this.reload = initializeData;
            this.loadData = loadData;
            this.loadMetaData = loadMetaData;
            this.saveData = saveData;
            this.editRow = editRow;
            this.replaceDataSource = replaceDataSource;

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

            function initialize() {
                initializeData();
                onStatsUpdatedHandler = dataSource.onStatsUpdated(
                    grid.meta.scope,
                    handleSourceStatsUpdate
                );
                onDataUpdatedHandler = dataSource.onDataUpdated(
                    grid.meta.scope,
                    handleSourceDataUpdate
                );
            }

            function initializeData() {
                return loadMetaData().then(function() {
                    grid.meta.initialized = true;
                    loadData().then(function() {
                        // Workaround - goals are defined after initial data is loaded; therefor reload metadata
                        loadMetaData();
                    });
                });
            }

            function replaceDataSource(_dataSource) {
                dataSource = _dataSource;

                // Rewire DataSource listeners
                onStatsUpdatedHandler();
                onDataUpdatedHandler();
                onStatsUpdatedHandler = dataSource.onStatsUpdated(
                    grid.meta.scope,
                    handleSourceStatsUpdate
                );
                onDataUpdatedHandler = dataSource.onDataUpdated(
                    grid.meta.scope,
                    handleSourceDataUpdate
                );

                zemGridParser.clear(grid);
                if (dataSource.getData().stats) {
                    // If data already initialized use it
                    zemGridParser.parseMetaData(grid, dataSource.getMetaData());
                    zemGridParser.parse(grid, dataSource.getData());

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

                    grid.meta.pubsub.notify(
                        grid.meta.pubsub.EVENTS.METADATA_UPDATED
                    );
                    grid.meta.pubsub.notify(
                        grid.meta.pubsub.EVENTS.DATA_UPDATED
                    );
                } else {
                    initializeData();
                }
            }

            function loadMetaData() {
                var deferred = $q.defer();
                dataSource.loadMetaData(true).then(function(data) {
                    zemGridParser.parseMetaData(grid, data);
                    grid.meta.pubsub.notify(
                        grid.meta.pubsub.EVENTS.METADATA_UPDATED
                    );
                    deferred.resolve();
                });
                return deferred.promise;
            }

            function loadData(row, size) {
                var breakdown;
                if (row) {
                    // When additional data (load more...) is requested
                    // breakdown row is passed as an argument
                    breakdown = row.data;
                }
                var deferred = $q.defer();
                dataSource.loadData(breakdown, size).then(
                    function() {
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
                        // TODO: Handle errors
                        deferred.reject(err);
                    }
                );
                return deferred.promise;
            }

            function saveData(value, row, column) {
                var deferred = $q.defer();
                dataSource.saveData(value, row.data, column.data).then(
                    function(data) {
                        if (data.notification) {
                            if (lastNotification) lastNotification.close();
                            lastNotification = zemAlertsService.notify(
                                data.notification.type,
                                data.notification.msg,
                                true
                            );
                        }
                        deferred.resolve(data);
                    },
                    function(err) {
                        deferred.reject(err);
                    }
                );
                return deferred.promise;
            }

            function editRow(row) {
                return dataSource.editRow(row);
            }

            function handleSourceStatsUpdate() {
                grid.meta.pubsub.notify(grid.meta.pubsub.EVENTS.DATA_UPDATED);
            }

            function handleSourceDataUpdate(event, data) {
                if (!delayInitialDataUpdate(data)) {
                    doHandleSourceDataUpdate(data);
                }
            }

            function doHandleSourceDataUpdate(data) {
                zemGridParser.parse(grid, data);
                grid.meta.loading = !data.breakdown;
                grid.meta.pubsub.notify(grid.meta.pubsub.EVENTS.DATA_UPDATED);
            }

            // Delay initial load (data update) to allow faster switching between pages
            // Data rows add significant JS work at initialization therefor we
            // are deferring this for 1s
            var metaDataLoadTime;
            var dataLoadTime;

            function delayInitialDataUpdate(data) {
                if (!metaDataLoadTime) {
                    metaDataLoadTime = new Date().getTime();
                } else if (!dataLoadTime) {
                    dataLoadTime = new Date().getTime();
                    var diff = dataLoadTime - metaDataLoadTime;
                    if (diff < 1000) {
                        $timeout(function() {
                            doHandleSourceDataUpdate(data);
                        }, 1000 - diff);
                        return true;
                    }
                }
                return false;
            }
        }

        return {
            createInstance: function(grid, dataSource) {
                return new GridDataService(grid, dataSource);
            },
        };
    });
