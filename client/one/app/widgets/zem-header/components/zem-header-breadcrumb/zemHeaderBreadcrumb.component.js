angular.module('one.widgets').component('zemHeaderBreadcrumb', {
    templateUrl: '/app/widgets/zem-header/components/zem-header-breadcrumb/zemHeaderBreadcrumb.component.html',
    controller: ['$document', 'config', 'zemPermissions', 'zemNavigationNewService', function ($document, config, zemPermissions, zemNavigationNewService) { // eslint-disable-line max-len

        var $ctrl = this;
        $ctrl.config = config;
        $ctrl.getHomeHref = getHomeHref;
        $ctrl.getItemHref = getItemHref;

        $ctrl.$onInit = function () {
            $ctrl.userCanSeeAllAccounts = zemPermissions.hasPermission('dash.group_account_automatically_add');
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

        function getHomeHref () {
            return zemNavigationNewService.getHomeHref();
        }

        function getItemHref (item) {
            return zemNavigationNewService.getEntityHref(item.entity);
        }
    }]
});
