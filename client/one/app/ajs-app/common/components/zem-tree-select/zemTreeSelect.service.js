angular.module('one.common').service('zemTreeSelectService', function() {
    this.createList = createList;
    this.getVisibleItems = getVisibleItems;
    this.getVisibleItemsMatchingQuery = getVisibleItemsMatchingQuery;
    this.getVisibleItemsAfterItemToggled = getVisibleItemsAfterItemToggled;

    function createList(root) {
        var list = createListRecursion(root, [], null);
        list.shift(); // Remove root from list
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
        initializeVisibleAndCollapsedProperty(item);

        return item;
    }

    function initializeVisibleAndCollapsedProperty(item) {
        item.isVisible = item.level < 2;
        item.isCollapsed = true;
    }

    function getVisibleItems(allItems) {
        return allItems.filter(function(item) {
            return item.isVisible;
        });
    }

    function getVisibleItemsMatchingQuery(query, allItems) {
        query = query ? query.toLowerCase() : null;

        allItems.forEach(function(item) {
            if (query) {
                item.isVisible = false;
                item.isCollapsed = true;
            } else {
                initializeVisibleAndCollapsedProperty(item);
            }
        });

        if (query) {
            allItems.forEach(function(item) {
                if (
                    item.name.toLowerCase().indexOf(query) !== -1 ||
                    item.id.indexOf(query) !== -1
                ) {
                    item.isVisible = true;
                    makeParentsVisibleAndExpanded(item);
                }
            });
        }

        return getVisibleItems(allItems);
    }

    function getVisibleItemsAfterItemToggled(toggledItem, allItems) {
        toggleItemCollapse(toggledItem, allItems);
        return getVisibleItems(allItems);
    }

    function toggleItemCollapse(toggledItem, allItems) {
        toggledItem.isCollapsed = !toggledItem.isCollapsed;
        toggleChildrenVisibility(toggledItem, allItems);
    }

    function toggleChildrenVisibility(parent, allItems) {
        allItems
            .filter(function(item) {
                return item.parent === parent;
            })
            .forEach(function(item) {
                item.isVisible = !parent.isCollapsed;
                item.isCollapsed = true;
                toggleChildrenVisibility(item, allItems);
            });
    }

    function makeParentsVisibleAndExpanded(item) {
        var parent = (item || {}).parent;
        while (parent) {
            parent.isVisible = true;
            parent.isCollapsed = false;
            parent = parent.parent;
        }
    }
});
