angular.module('one.widgets').component('zemGridContainer', {
    templateUrl: '/app/widgets/zem-grid-container/zemGridContainer.component.html',
    bindings: {
        entity: '<',
        breakdown: '<',
    },
    controller: function ($scope, $timeout, zemGridIntegrationService) { // eslint-disable-line max-len
        var $ctrl = this;

        $ctrl.constants = constants;
        $ctrl.onGridInitialized = onGridInitialized;

        $ctrl.$onInit = function () {
            initializeTabs();
            $ctrl.initialized = true;

            // [UX] Delay tab activation (zemGrid) to
            // show tab container as fast as possible on initial render
            var tab = getTab($ctrl.breakdown);
            activateTab(tab);
        };

        $ctrl.$onChanges = function (changes) {
            if (!$ctrl.initialized) return;
            if (changes.entity) {
                initializeTabs();
            }

            var tab = getTab($ctrl.breakdown);
            activateTab(tab);
        };

        function initializeTabs () {
            $ctrl.tabs = createTabOptions($ctrl.entity);
            var tab = getTab($ctrl.breakdown);
            selectTab(tab);
        }

        function activateTab (tab) {
            selectTab(tab);

            if (isGridTab(tab)) {
                activateGridTab(tab);
            } else {
                tab.activated = true;
            }
        }

        function isGridTab (tab) {
            return tab.breakdown !== constants.breakdown.INSIGHTS;
        }

        function activateGridTab (tab) {
            if (!tab.activated) {
                $timeout(function () {
                    var $childScope = $scope.$new();
                    tab.gridIntegrationService = zemGridIntegrationService.createInstance($childScope);
                    tab.gridIntegrationService.initialize();
                    tab.gridIntegrationService.configureDataSource($ctrl.entity, tab.breakdown);
                    tab.grid = tab.gridIntegrationService.getGrid();
                    tab.activated = true;
                });
            } else {
                // [UX] Refresh/resize Grid UI if already activated
                //   -> column sizes, pivot columns, sticky header/footer
                $timeout(function () { tab.grid.api.refreshUI(); }, 100);
            }
        }

        function selectTab (tab) {
            $ctrl.tabs.forEach(function (tab) { tab.selected = false; });
            tab.selected = true;
        }

        function getTab (breakdown) {
            return $ctrl.tabs.filter(function (tab) { return tab.breakdown === breakdown; })[0];
        }

        function onGridInitialized (tab, gridApi) {
            tab.gridIntegrationService.setGridApi(gridApi);
        }

        // TODO: Refactor if further expanded (create dedicated service)
        function createTabOptions (entity) {
            var options = [];
            if (!entity) {
                options = [
                    {
                        name: 'Accounts',
                        breakdown: constants.breakdown.ACCOUNT,
                    },
                    {
                        name: 'Media Sources',
                        breakdown: constants.breakdown.MEDIA_SOURCE,
                    },
                ];
            }

            if (entity && entity.type === constants.entityType.ACCOUNT) {
                options = [
                    {
                        name: 'Campaigns',
                        breakdown: constants.breakdown.CAMPAIGN,
                    },
                    {
                        name: 'Media Sources',
                        breakdown: constants.breakdown.MEDIA_SOURCE,
                    },
                ];
            }

            if (entity && entity.type === constants.entityType.CAMPAIGN) {
                options = [
                    {
                        name: 'Ad groups',
                        breakdown: constants.breakdown.AD_GROUP,
                    },
                    {
                        name: 'Media Sources',
                        breakdown: constants.breakdown.MEDIA_SOURCE,
                    },
                    {
                        name: 'Content Insights',
                        breakdown: 'insights',
                    },
                ];
            }

            if (entity && entity.type === constants.entityType.AD_GROUP) {
                options = [
                    {
                        name: 'Content Ads',
                        breakdown: constants.breakdown.CONTENT_AD,
                    },
                    {
                        name: 'Media Sources',
                        breakdown: constants.breakdown.MEDIA_SOURCE,
                    },
                    {
                        name: 'Publishers',
                        breakdown: constants.breakdown.PUBLISHER,
                    },
                ];
            }
            return options;
        }
    },
});
