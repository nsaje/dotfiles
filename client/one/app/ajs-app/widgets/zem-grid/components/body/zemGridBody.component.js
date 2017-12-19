angular.module('one.widgets').directive('zemGridBody', function (zemGridConstants, NgZone) {

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            grid: '=',
        },
        template: require('./zemGridBody.component.html'),
        link: function (scope, element) {
            var grid = scope.ctrl.grid;
            var pubsub = grid.meta.pubsub;

            grid.body.visibleRows = [];
            grid.body.ui.numOfRows = calculateNumOfRows();
            grid.body.ui.element = element;
            grid.body.ui.scrollLeft = 0;
            grid.body.ui.scrollTop = 0;
            scope.state = {
                renderedRows: [],
            };

            function calculateNumOfRows () {
                // Calculate how much rows we need to fill the entire page
                // To simplify handling (window resize, etc.) we enforce that MIN_NUM_OF_ROWS_PER_PAGE (25)
                // is always prepared and can be greater if viewport is higher than 1125px + 90px (footer+header).
                // TODO: This can be improved in future if we find it necessary
                var numOfRows = Math.ceil(document.documentElement.clientHeight /
                                           zemGridConstants.gridBodyRendering.ROW_HEIGHT);
                numOfRows = Math.max(numOfRows, zemGridConstants.gridBodyRendering.MIN_NUM_OF_ROWS_PER_PAGE);
                return numOfRows;
            }

            function scrollListener (event) {
                NgZone.runOutsideAngular(function () {
                    if (grid.body.ui.scrollLeft !== event.target.scrollLeft) {
                        grid.body.ui.scrollLeft = event.target.scrollLeft;
                        pubsub.notify(
                            pubsub.EVENTS.BODY_HORIZONTAL_SCROLL,
                            grid.body.ui.scrollLeft
                        );
                    }
                });
            }

            var isScrolling;
            function scrollWindowListener () {
                NgZone.runOutsideAngular(function () {
                    var scrollTop = Math.max(0, window.pageYOffset - element.offset().top);
                    if (grid.body.ui.scrollTop !== scrollTop) {
                        grid.body.ui.scrollTop = scrollTop;
                        pubsub.notify(
                            pubsub.EVENTS.BODY_VERTICAL_SCROLL,
                            grid.body.ui.scrollTop
                        );
                    }

                    // Disable triggering of elements' event listeners while scrolling
                    element.addClass('disable-pointer-events');
                    window.clearTimeout(isScrolling);
                    isScrolling = setTimeout(function () {
                        element.removeClass('disable-pointer-events');
                    }, 500);
                });
            }

            var visibleRowsCount;

            function updateVisibleRows () {
                var visibleRows = [];
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
                scope.state.renderedRows = visibleRows.slice(0, grid.body.ui.numOfRows);
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
            // Delay 0.25s to allow quick page switch and before data is loaded (delayed for 1s)
            setTimeout(initialLoad, 250);
            function initialLoad () {
                if (scope.state.renderedRows.length > 0) return;
                for (var idx = 0; idx < zemGridConstants.gridBodyRendering.NUM_OF_PRERENDERED_ROWS; ++idx) {
                    scope.state.renderedRows.push({index: idx});
                }
                NgZone.runOutsideAngular(function () {
                    scope.$digest();
                });
            }

            pubsub.register(pubsub.EVENTS.DATA_UPDATED, scope, updateBody);

            NgZone.runOutsideAngular(function () {
                element.on('scroll', scrollListener);
                window.addEventListener('scroll', scrollWindowListener);
            });
            scope.$on('$destroy', function () {
                window.removeEventListener('scroll', scrollWindowListener);
            });
        },
        controller: function () {},
    };
});
