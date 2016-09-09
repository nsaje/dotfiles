/* globals oneApp, constants */
'use strict';

angular.module('one.widgets').component('zemHeaderBreadcrumb', { // eslint-disable-line max-len
    templateUrl: '/app/widgets/zem-header/components/zem-header-breadcrumb/zemHeaderBreadcrumb.component.html',
    controller: ['$document', 'config', 'zemUserService', 'zemNavigationNewService', function ($document, config, zemUserService, zemNavigationNewService) {

        var $ctrl = this;
        $ctrl.config = config;
        $ctrl.navigateTo = navigateTo;
        $ctrl.navigateToHome = navigateToHome;

        $ctrl.$onInit = function () {
            zemNavigationNewService.onActiveEntityChange(onEntityChange);
        };

        function onEntityChange (event, activeEntity) {
            updateTitle(activeEntity);
            updateBreadcrumb(activeEntity);
        }

        function updateTitle (entity) {
            var title;
            if (entity) {
                title = entity.name + ' | Zemanta';
            } else {
                title = 'My accounts';
                if (zemUserService.userHasPermissions('dash.group_account_automatically_add')) {
                    title = 'All accounts';
                }
            }
            $document.prop('title', title);
        }

        function updateBreadcrumb (entity) {
            $ctrl.breadcrumb = [];
            while (entity) {
                $ctrl.breadcrumb.unshift({
                    name: entity.name,
                    typeName: getTypeName(entity.type),
                    entity: entity,
                });
                entity = entity.parent;
            }
        }

        function getTypeName (type) {
            if (type === constants.entityType.ACCOUNT) return 'Account';
            if (type === constants.entityType.CAMPAIGN) return 'Campaign';
            if (type === constants.entityType.AD_GROUP) return 'Ad Group';
        }

        function navigateToHome () {
            zemNavigationNewService.navigateTo();
        }
        function navigateTo (item) {
            zemNavigationNewService.navigateTo(item.entity);
        }
    }]
});
