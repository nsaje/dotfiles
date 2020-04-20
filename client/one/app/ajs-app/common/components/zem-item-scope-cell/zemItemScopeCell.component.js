require('./zemItemScopeCell.component.less');
var commonHelpers = require('../../../../shared/helpers/common.helpers');

angular.module('one.common').component('zemItemScopeCell', {
    bindings: {
        item: '=',
        agencyIdField: '=',
        agencyNameField: '=',
        canUseAgencyLink: '=',
        agencyLink: '=',
        accountIdField: '=',
        accountNameField: '=',
        canUseAccountLink: '=',
        accountLink: '=',
    },
    template: require('./zemItemScopeCell.component.html'),
    controller: function() {
        var $ctrl = this;

        $ctrl.ITEM_SCOPE_STATE = {
            agencyScope: 'Agency',
            accountScope: 'Account',
        };

        $ctrl.$onInit = function() {
            $ctrl.itemScopeState = getItemScopeState($ctrl.item);

            if ($ctrl.itemScopeState === $ctrl.ITEM_SCOPE_STATE.agencyScope) {
                $ctrl.entityName = commonHelpers.getValueOrDefault(
                    $ctrl.item[
                        commonHelpers.getValueOrDefault(
                            $ctrl.agencyNameField,
                            'agencyName'
                        )
                    ],
                    'N/A'
                );
                $ctrl.canUseEntityLink = commonHelpers.getValueOrDefault(
                    $ctrl.canUseAgencyLink,
                    true
                );
                $ctrl.entityLink = commonHelpers.getValueOrDefault(
                    $ctrl.agencyLink,
                    null
                );
            } else if (
                $ctrl.itemScopeState === $ctrl.ITEM_SCOPE_STATE.accountScope
            ) {
                $ctrl.entityName = commonHelpers.getValueOrDefault(
                    $ctrl.item[
                        commonHelpers.getValueOrDefault(
                            $ctrl.accountNameField,
                            'accountName'
                        )
                    ],
                    'N/A'
                );
                $ctrl.canUseEntityLink = commonHelpers.getValueOrDefault(
                    $ctrl.canUseAccountLink,
                    true
                );
                $ctrl.entityLink = commonHelpers.getValueOrDefault(
                    $ctrl.accountLink,
                    null
                );
            }
        };

        function getItemScopeState(item) {
            if (
                commonHelpers.isDefined(
                    item[
                        commonHelpers.getValueOrDefault(
                            $ctrl.agencyIdField,
                            'agencyId'
                        )
                    ]
                )
            ) {
                return $ctrl.ITEM_SCOPE_STATE.agencyScope;
            } else if (
                commonHelpers.isDefined(
                    item[
                        commonHelpers.getValueOrDefault(
                            $ctrl.accountIdField,
                            'accountId'
                        )
                    ]
                )
            ) {
                return $ctrl.ITEM_SCOPE_STATE.accountScope;
            }
            return null;
        }
    },
});
