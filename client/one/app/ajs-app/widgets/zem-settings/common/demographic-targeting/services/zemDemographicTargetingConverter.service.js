angular
    .module('one.widgets')
    .service('zemDemographicTargetingConverter', function() {
        //eslint-disable-line max-len
        this.convertFromApi = convertFromApi;
        this.convertToApi = convertToApi;

        function convertFromApi(apiData) {
            if (!apiData) return null;
            return parseNode(apiData);
        }

        function parseNode(dataNode, parent) {
            var node;
            var key = Object.keys(dataNode)[0];
            var value = dataNode[key];

            if (!key) return null;

            if (Array.isArray(value)) {
                node = {
                    type: key.toLowerCase(),
                    parent: parent,
                };
                node.childNodes = value.map(function(n) {
                    return parseNode(n, node);
                });
            } else {
                node = {
                    type: key.toLowerCase(),
                    parent: parent,
                    provider: value.split(':')[0],
                    value: value.split(':')[1],
                };
            }

            return node;
        }

        function convertToApi(data) {
            return formatNode(data) || {};
        }

        function formatNode(node) {
            if (!node) return null;
            var formattedNode = {};

            if (node.type === 'category') {
                formattedNode[node.type] = node.provider + ':' + node.value;
                return formattedNode;
            }

            var childs = node.childNodes.map(formatNode).filter(function(n) {
                return n;
            });
            if (childs.length > 0) {
                formattedNode[node.type] = childs;
                return formattedNode;
            }
            return null;
        }
    });
