angular.module('one.widgets').component('zemHeaderBreadcrumb', {
    templateUrl: '/app/widgets/zem-header/components/zem-header-breadcrumb/zemHeaderBreadcrumb.component.html',
    controller: function ($rootScope, $state, $location, $document, config, zemPermissions, zemNavigationNewService) { // eslint-disable-line max-len

        var $ctrl = this;
        $ctrl.config = config;
        $ctrl.getHomeHref = getHomeHref;

        $ctrl.$onInit = function () {
            $ctrl.userCanSeeAllAccounts = zemPermissions.hasPermission('dash.group_account_automatically_add');

            $rootScope.$on('$stateChangeSuccess', update);
            zemNavigationNewService.onActiveEntityChange(update);

            // FIXME: Use Entity services for name changes
            zemNavigationNewService.onHierarchyUpdate(update);
        };

        function update () {
            var activeEntity = zemNavigationNewService.getActiveEntity();
            updateTitle(activeEntity);
            updateBreadcrumb(activeEntity);
        }

        function updateTitle (entity) {
            var title;
            if (entity) {
                title = entity.name + ' | Zemanta';
            } else {
                title = 'My accounts';
                if (zemPermissions.hasPermission('dash.group_account_automatically_add')) {
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
                    href: zemNavigationNewService.getEntityHref(entity, true),
                });
                entity = entity.parent;
            }

            var administrationPage = getAdministrationPage();
            if (administrationPage) $ctrl.breadcrumb.push(administrationPage);
        }

        function getTypeName (type) {
            if (type === constants.entityType.ACCOUNT) return 'Account';
            if (type === constants.entityType.CAMPAIGN) return 'Campaign';
            if (type === constants.entityType.AD_GROUP) return 'Ad Group';
        }

        function getAdministrationPage () {
            if ($state.includes('**.users')) {
                return {typeName: 'Administration', name: 'User permissions', href: $location.absUrl()};
            }
            if ($state.includes('**.credit_v2')) {
                return {typeName: 'Administration', name: 'Account credit', href: $location.absUrl()};
            }
            if ($state.includes('**.scheduled_reports_v2')) {
                return {typeName: 'Administration', name: 'Scheduled reports', href: $location.absUrl()};
            }
            return null;
        }

        function getHomeHref () {
            return zemNavigationNewService.getHomeHref();
        }
    }
});
