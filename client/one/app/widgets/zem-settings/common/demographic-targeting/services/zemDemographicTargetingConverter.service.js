angular.module('one.widgets').service('zemDemographicTargetingConverter', function () { //eslint-disable-line max-len
    this.convertFromApi = convertFromApi;
    this.convertToApi = convertToApi;

    function convertFromApi (apiData) {
        if (!apiData || apiData.length === 0) return null;
        return parseNode(apiData);
    }

    function parseNode (dataNode, parent) {
        var node;
        if (Array.isArray(dataNode)) {
            node = {
                type: dataNode[0],
                parent: parent,
            };
            node.childNodes = dataNode.slice(1).map(function (n) { return parseNode(n, node); });
        } else {
            node = {
                type: 'category',
                parent: parent,
                provider: dataNode.split(':')[0],
                value: dataNode.split(':')[1]
            };
        }

        return node;
    }

    function convertToApi (data) {
        return formatNode(data);
    }

    function formatNode (node) {
        if (!node) return [];

        if (node.type === 'category') {
            return node.provider + ':' + node.value;
        }

        var childs = node.childNodes.map(formatNode).filter(function (n) { return n; });
        if (childs.length > 0) {
            return [node.type].concat(childs);
        }
        return [];
    }
});
