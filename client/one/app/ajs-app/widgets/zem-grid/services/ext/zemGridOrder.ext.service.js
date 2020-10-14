angular
    .module('one.widgets')
    .factory('zemGridOrderService', function(
        zemGridConstants,
        zemGridUIService,
        zemGridStorageService
    ) {
        // eslint-disable-line max-len

        function OrderService(grid) {
            var pubsub = grid.meta.pubsub;
            var lastOrder;

            initialize();

            //
            // Public API
            //
            this.destroy = destroy;
            this.getColumnOrder = getColumnOrder;
            this.setColumnOrder = setColumnOrder;

            var onDataUpdatedHandler;

            function initialize() {
                loadOrder();
                onDataUpdatedHandler = pubsub.register(
                    pubsub.EVENTS.DATA_UPDATED,
                    grid.meta.scope,
                    initializeOrder
                );
            }

            function destroy() {
                if (onDataUpdatedHandler) onDataUpdatedHandler();
            }

            function loadOrder() {
                // Load order when METADATA is updated for the first time (metadata is required for load)
                var deregister = pubsub.register(
                    pubsub.EVENTS.METADATA_UPDATED,
                    grid.meta.scope,
                    function() {
                        zemGridStorageService.loadOrder(grid);
                        initializeOrder();
                        deregister();
                    }
                );
            }

            function initializeOrder() {
                var order = grid.meta.api.getOrder();
                if (!order) return;
                if (order === lastOrder) return;
                lastOrder = order;

                var direction = zemGridConstants.gridColumnOrder.ASC;
                if (order[0] === '-') {
                    direction = zemGridConstants.gridColumnOrder.DESC;
                    order = order.substr(1);
                }

                resetColumnOrders();
                var orderedColumn = findColumnByOrderField(order);
                if (orderedColumn) orderedColumn.order = direction;

                pubsub.notify(pubsub.EVENTS.EXT_ORDER_UPDATED);
            }

            function resetColumnOrders() {
                grid.header.columns.forEach(function(column) {
                    column.order = zemGridConstants.gridColumnOrder.NONE;
                });
            }

            function findColumnByOrderField(orderField) {
                return grid.header.columns.filter(function(column) {
                    var columnOrderField =
                        column.data.orderField || column.field;
                    return columnOrderField === orderField;
                })[0];
            }

            function getColumnOrder(column) {
                return column.order;
            }

            function setColumnOrder(column, order) {
                resetColumnOrders();
                column.order = order;

                // Resize columns to prevent flickering when rows are emptied
                zemGridUIService.resizeGridColumns(grid);

                var orderField = column.data.orderField || column.field;
                if (order === zemGridConstants.gridColumnOrder.DESC) {
                    orderField = '-' + orderField;
                }
                grid.meta.api.setOrder(orderField);
                grid.meta.api.loadData();
                zemGridStorageService.saveOrder(grid);

                pubsub.notify(pubsub.EVENTS.EXT_ORDER_UPDATED);
            }
        }

        return {
            createInstance: function(grid) {
                return new OrderService(grid);
            },
        };
    });
