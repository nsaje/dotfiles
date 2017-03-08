angular.module('one.widgets').component('zemGridContainerTabs', {
    templateUrl: '/app/widgets/zem-grid-container/components/tabs/zemGridContainerTabs.component.html',
    bindings: {
        entity: '<',
        breakdown: '<'
    },
    controller: function ($state) {
        var $ctrl = this;

        $ctrl.navigateTo = navigateTo;

        $ctrl.$onInit = function () {
            $ctrl.options = createTabOptions($ctrl.entity);
            $ctrl.options.forEach(function (option) { option.selected = option.breakdown === $ctrl.breakdown; });
        };

        $ctrl.$onChanges = function () {
            $ctrl.options = createTabOptions($ctrl.entity);

            // Set option.selected flag based on the current breakdown
            $ctrl.options.forEach(function (option) { option.selected = option.breakdown === $ctrl.breakdown; });
        };

        function navigateTo (option) {
            var id = $ctrl.entity ? $ctrl.entity.id : null;
            var level = $ctrl.entity ? constants.entityTypeToLevelMap[$ctrl.entity.type] : constants.level.ALL_ACCOUNTS;
            var levelStateParam = constants.levelToLevelStateParamMap[level];
            var breakdownStateParam = constants.breakdownToBreakdownStateParamMap[option.breakdown];

            $state.go('v2.analytics', {
                id: id,
                level: levelStateParam,
                breakdown: breakdownStateParam
            }, {notify: false, location: 'replace'});
        }

        function createTabOptions (entity) {
            var options = [];
            if (!entity) {
                options = [
                    {
                        name: 'Accounts',
                        breakdown: constants.breakdown.ACCOUNT,
                    },
                    {
                        name: 'Sources',
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
                        name: 'Sources',
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
                        name: 'Sources',
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
                        name: 'Sources',
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

    }
});
