angular
    .module('one.widgets')
    .service('zemCreateEntityActionService', function(
        zemUploadService,
        zemNavigationNewService
    ) {
        this.createContentAds = createContentAds;

        function createContentAds(entityProperties) {
            return zemUploadService.openUploadModal(
                entityProperties.parent,
                function onSave() {
                    zemNavigationNewService.reloadCurrentRoute();
                }
            );
        }
    });
