angular.module('one.common').service('zemTreeSelectService', function() {
    //eslint-disable-line max-len

    this.createList = createList;
    this.filterList = filterList;

    function createList(root) {
        var list = createListRecursion(root, [], null);

        // Remove root from list and make childs visible
        list[0].isCollapsed = false;
        list.shift();

        return list;
    }

    function createListRecursion(node, list, parent) {
        var item = createItem(node, parent);
        list.push(item);

        if (node.childNodes && node.childNodes.length > 0) {
            node.childNodes.forEach(function(child) {
                createListRecursion(child, list, item);
            });
        }

        return list;
    }

    function createItem(node, parent) {
        var item = {
            id: node.id.toString(),
            name: node.name,
            value: node,
            parent: parent,
            level: parent ? parent.level + 1 : 0,
            isLeaf: true,
            isSelectable: !node.navigationOnly,
        };
        item.isLeaf = !node.childNodes || !node.childNodes.length;
        item.isCollapsed = !item.isLeaf;

        return item;
    }

    function filterList(list, searchQuery) {
        if (searchQuery) {
            searchQuery = searchQuery.toLowerCase();
            return list.filter(function(item) {
                return (
                    item.name.toLowerCase().indexOf(searchQuery) >= 0 ||
                    item.id.indexOf(searchQuery) >= 0
                );
            });
        }

        return list.filter(function(item) {
            var parent = item.parent;
            while (parent) {
                if (parent.isCollapsed) return false;
                parent = parent.parent;
            }
            return true;
        });
    }
});
