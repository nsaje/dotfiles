/* globals angular */
'use strict';

angular.module('one.legacy').directive('zemGridBody', function (zemGridConstants, zemGridUIService) { // eslint-disable-line max-len

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_body.html',
        link: function (scope, element) {
            var grid = scope.ctrl.grid;
            var pubsub = grid.meta.pubsub;

            grid.body.ui.numOfRows = calculateNumOfRows();
            grid.body.ui.element = element;
            grid.body.ui.scrollLeft = 0;
            grid.body.ui.scrollTop = 0;
            scope.state = {
                renderedRows: [],
            };

            var visibleRows;

            function calculateNumOfRows () {
                // Calculate how much rows we need to fill the entire page
                // To simplify handling (window resize, etc.) we enforce that MIN_NUM_OF_ROWS_PER_PAGE (25)
                // is always prepared and can be greater if viewport is higher than 1125px + 90px (footer+header).
                // TODO: This can be improved in future if we find it necessary
                var numOfRows = Math.ceil (document.documentElement.clientHeight / zemGridConstants.gridBodyRendering.ROW_HEIGHT);
                numOfRows = Math.max (numOfRows, zemGridConstants.gridBodyRendering.MIN_NUM_OF_ROWS_PER_PAGE);
                return numOfRows;
            }

            function scrollListener (event) {
                if (grid.body.ui.scrollLeft !== event.target.scrollLeft) {
                    grid.body.ui.scrollLeft = event.target.scrollLeft;
                    pubsub.notify(
                        pubsub.EVENTS.BODY_HORIZONTAL_SCROLL,
                        grid.body.ui.scrollLeft
                    );
                }
            }

            function scrollWindowListener () {
                var scrollTop = Math.max(0, window.pageYOffset - element.offset().top);
                if (grid.body.ui.scrollTop !== scrollTop) {
                    grid.body.ui.scrollTop = scrollTop;
                    pubsub.notify(
                        pubsub.EVENTS.BODY_VERTICAL_SCROLL,
                        grid.body.ui.scrollTop
                    );
                }
            }

            var visibleRowsCount;

            function updateVisibleRows () {
                visibleRows = [];
                visibleRowsCount = 0;
                grid.body.rows.forEach(function (row) {
                    if (row.visible) {
                        row.style = getTranslateYStyle(
                            visibleRowsCount * zemGridConstants.gridBodyRendering.ROW_HEIGHT
                        );
                        visibleRows.push(row);
                        visibleRowsCount++;
                    }
                });

                for (var i = 0; i < visibleRows.length; i++) {
                    visibleRows[i].index = i % grid.body.ui.numOfRows;
                }

                scope.ctrl.grid.body.visibleRows = visibleRows;
                var renderedRows = visibleRows.slice(0, grid.body.ui.numOfRows);
                graduallyPopulateRenderedRows(renderedRows);
            }

            function graduallyPopulateRenderedRows (renderedRows) {
                // Add rows gradually (step by step in 50ms interval) to avoid browser freeze
                // All rows will be hidden when added to scope.renderedRows collection
                // After first draw, grid columns will be resized and newly added rows will become visible
                renderedRows.forEach(function (row) { row.dummy = true; });
                var step = zemGridConstants.gridBodyRendering.GRADUAL_POPULATE_STEP;

                scope.state.renderedRows = renderedRows.slice(0, scope.state.renderedRows.length);
                scope.state.renderedRows.forEach(function (row) { row.dummy = false; });

                doLoadingStep();

                var interval = setInterval(function () {
                    if (renderedRows.length <= scope.state.renderedRows.length) {
                        clearInterval(interval);
                        return;
                    }
                    doLoadingStep ();
                    scope.$digest();
                }, 50);

                function doLoadingStep () {
                    scope.state.renderedRows = renderedRows.slice(0, scope.state.renderedRows.length + step);
                    setTimeout(function () {
                        scope.state.renderedRows.forEach(function (row) { row.dummy = false; });
                        zemGridUIService.resizeGridColumns(scope.ctrl.grid);
                        scope.$digest();
                    }, 0);
                }
            }

            function getTranslateYStyle (top) {
                var translateCssProperty = 'translateY(' + top + 'px)';

                return {
                    '-webkit-transform': translateCssProperty,
                    '-ms-transform': translateCssProperty,
                    '-moz-transform': translateCssProperty,
                    'transform': translateCssProperty,
                    'display': 'block',
                };
            }

            function updateTableStyle () {
                // Update virtual scroll viewport (zem-gird-table)
                var height = visibleRowsCount * zemGridConstants.gridBodyRendering.ROW_HEIGHT;
                element.find('.zem-grid-table').css({
                    height: height + 'px',
                });
            }

            function updateBody () {
                updateVisibleRows();
                updateTableStyle();
                pubsub.notify(pubsub.EVENTS.BODY_ROWS_UPDATED);
            }


            // Initialize dummy rows to optimize initial data rendering
            // Delay 0.5s to allow quick page switch and before data is loaded (delayed for 1s)
            setTimeout(initialLoad, 500);
            function initialLoad () {
                if (scope.state.renderedRows.length > 0) return;
                for (var idx = 0; idx < zemGridConstants.gridBodyRendering.GRADUAL_POPULATE_STEP; ++idx) {
                    scope.state.renderedRows.push({index: idx});
                }
                scope.$digest();
            }

            pubsub.register(pubsub.EVENTS.DATA_UPDATED, scope, updateBody);

            element.on('scroll', scrollListener);
            window.addEventListener('scroll', scrollWindowListener);
            scope.$on('$destroy', function () {
                window.removeEventListener ('scroll', scrollWindowListener);
            });
        },
        controller: function () {},
    };
});
