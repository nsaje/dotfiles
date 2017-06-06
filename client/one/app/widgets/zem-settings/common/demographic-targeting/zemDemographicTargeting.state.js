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
            if (state.editable) updateInfo();
        }

        function getState () {
            return state;
        }

        function createNode (type, parent) {
            var node = {type: type};
            if (type !== zemDemographicTargetingConstants.EXPRESSION_TYPE.CATEGORY) node.childNodes = [];
            addNodeSorted(node, parent);
            update();
            return node;
        }

        function addNodeSorted (node, parent) {
            // Push 'NOT' nodes to back
            node.parent = parent;
            parent.childNodes.push(node);
            parent.childNodes.sort(function (n1, n2) {
                if (n1.type === zemDemographicTargetingConstants.EXPRESSION_TYPE.NOT) return 1;
                if (n2.type === zemDemographicTargetingConstants.EXPRESSION_TYPE.NOT) return -1;
                return 0;
            });
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
            }, function (error) {
                if (!error) return; // Promise aborted

                state.info.reach = {
                    error: true
                };
            });
        }


        function isEditable (expressionTree) {
            if (!expressionTree) return true;
            if (expressionTree.type !== zemDemographicTargetingConstants.EXPRESSION_TYPE.AND) return false;

            for (var i = 0; i < expressionTree.childNodes.length; ++i) {
                var node = expressionTree.childNodes[i];
                if (node.type === zemDemographicTargetingConstants.EXPRESSION_TYPE.OR
                    && !isBlukaiCategoriesNode(node))
                    return false;

                if (node.type === zemDemographicTargetingConstants.EXPRESSION_TYPE.NOT) {
                    if (node.childNodes.length !== 1) return false;

                    if (!(node.childNodes[0].type === zemDemographicTargetingConstants.EXPRESSION_TYPE.OR
                        && isBlukaiCategoriesNode(node.childNodes[0]))) return false;
                }
            }

            return true;
        }

        function isBlukaiCategoriesNode (node) {
            if (node.type === zemDemographicTargetingConstants.EXPRESSION_TYPE.CATEGORY) return false;

            for (var i = 0; i < node.childNodes.length; ++i) {
                var childNode = node.childNodes[i];
                if (childNode.type !== zemDemographicTargetingConstants.EXPRESSION_TYPE.CATEGORY) return false;
                if (childNode.provider !== zemDemographicTargetingConstants.PROVIDER.BLUEKAI) return false;
                if (!zemDemographicTaxonomyService.getNodeById(childNode.value)) return false;
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
