angular
    .module('one.common')
    .service('zemDemographicTaxonomyService', function(
        $q,
        $http,
        $timeout,
        zemUtils,
        zemDemographicTargetingEndpoint
    ) {
        //eslint-disable-line max-len
        var taxonomyPromise = null;
        var taxonomy = null;
        var mapNodeIds = null;

        this.getTaxonomy = getTaxonomy;
        this.getNodeById = getNodeById;

        initialize();

        function initialize() {
            taxonomyPromise = zemDemographicTargetingEndpoint
                .getTaxonomy()
                .then(initializeTaxonomy);
        }

        function initializeTaxonomy(data) {
            taxonomy = data;
            mapNodeIds = {};
            zemUtils.traverseTree(taxonomy, function(node) {
                node.id = node.categoryId;
                mapNodeIds[node.id] = node;
            });
            return taxonomy;
        }

        function getTaxonomy() {
            if (taxonomy) {
                return $q.resolve(taxonomy);
            }

            return taxonomyPromise;
        }

        function getNodeById(id) {
            return mapNodeIds[id];
        }
    });
