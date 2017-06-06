angular.module('one.widgets').service('zemDemographicTargetingStateService', function ($filter, $timeout, zemUtils, zemDemographicTargetingConstants, zemDemographicTargetingEndpoint, zemDemographicTargetingConverter, zemDemographicTaxonomyService) { //eslint-disable-line max-len

    function StateService (entity) { // eslint-disable-line
        //
        // State Object
        //
        var state = {
            expressionTree: null,
            info: null,
            editable: false,
        };

        //
        // Public API
        //
        this.initialize = initialize;
        this.getState = getState;

        this.createNode = createNode;
        this.removeNode = removeNode;
        this.updateCategories = updateCategories;

        ///////////////////////////////////////////////////////////////////////////////////////////////
        // Internals
        //
        function initialize () {
            state.expressionTree = zemDemographicTargetingConverter.convertFromApi(entity.settings.bluekaiTargeting);
            state.editable = isEditable(state.expressionTree);
            updateInfo();
        }

        function getState () {
            return state;
        }

        function createNode (type, parent) {
            var node = {type: type};
            if (type !== zemDemographicTargetingConstants.EXPRESSION_TYPE.CATEGORY) node.childNodes = [];
            node.parent = parent;

            if (parent) parent.childNodes.push(node);
            else state.expressionTree = node;

            update();
            return node;
        }

        function removeNode (node) {
            if (!node.parent) {
                state.expressionTree = null;
                return;
            }

            var idx = node.parent.childNodes.indexOf(node);
            node.parent.childNodes.splice(idx, 1);
            update();
        }

        function updateCategories (node, categories, provider) {
            node.childNodes = categories.map(function (category) {
                return {
                    type: zemDemographicTargetingConstants.EXPRESSION_TYPE.CATEGORY,
                    value: category,
                    provider: provider,
                };
            });
            update();
        }

        function update () {
            entity.settings.bluekaiTargeting = zemDemographicTargetingConverter.convertToApi (state.expressionTree);
            updateInfo();
        }

        function updateInfo () {
            if (!state.editable) {
                state.info = null;
                return;
            }

            state.info = {};
            var categories = getCategories(state.expressionTree);

            if (categories.length === 0) {
                state.info.price = 0;
                state.info.reach = {value: 'All', relative: 100};
                return;
            }

            state.info.price = categories.reduce(function (max, c) {
                return c.price > max ? c.price : max;
            }, 0);

            zemDemographicTargetingEndpoint.getReach(entity.settings.bluekaiTargeting).then (function (data) {
                state.info.reach = {
                    value: $filter('number')(data.value),
                    relative: data.relative
                };
            });
        }


        function isEditable (expressionTree) {
            if (!expressionTree) return true;
            if (expressionTree.type !== zemDemographicTargetingConstants.EXPRESSION_TYPE.AND) return false;

            for (var i = 0; i < expressionTree.childNodes.length; ++i) {
                var node = expressionTree.childNodes[i];
                if (node.type === zemDemographicTargetingConstants.EXPRESSION_TYPE.OR
                    && !isFlatNode(node))
                    return false;

                if (node.type === zemDemographicTargetingConstants.EXPRESSION_TYPE.NOT) {
                    if (node.childNodes.length !== 1) return false;

                    if (!(node.childNodes[0].type === zemDemographicTargetingConstants.EXPRESSION_TYPE.OR
                        && isFlatNode(node.childNodes[0]))) return false;
                }
            }

            return true;
        }

        function isFlatNode (node) {
            if (node.type === zemDemographicTargetingConstants.EXPRESSION_TYPE.CATEGORY) return false;

            for (var i = 0; i < node.childNodes.length; ++i) {
                if (node.childNodes[i].type !== zemDemographicTargetingConstants.EXPRESSION_TYPE.CATEGORY) return false;
                if (node.childNodes[i].provider !== zemDemographicTargetingConstants.PROVIDER.BLUEKAI) return false;
            }

            return true;
        }

        function getCategories (root) {
            if (!root) return [];

            var categories = [];
            zemUtils.traverseTree(root, function (node) {
                if (node.type === zemDemographicTargetingConstants.EXPRESSION_TYPE.CATEGORY) {
                    var category = zemDemographicTaxonomyService.getNodeById(node.value);
                    categories.push(category);
                }
            });
            return categories;
        }

    }

    return {
        createInstance: function (entity) {
            return new StateService(entity);
        }
    };
});
