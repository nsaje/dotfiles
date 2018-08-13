angular.module('one.common').factory('zemSelectList', function() {
    //eslint-disable-line max-len

    function UISelectList(items) {
        var vm = this;

        vm.first = first;
        vm.last = last;
        vm.next = next;
        vm.previous = previous;
        vm.indexOf = indexOf;
        vm.getItem = getItem;
        vm.items = [];

        initTree();

        function initTree() {
            var header1,
                header2,
                tree = {};
            for (var i = 0; i < items.length; i++) {
                header1 = items[i].h1 || '';
                header2 = items[i].h2 || '';

                if (!tree.hasOwnProperty(header1)) tree[header1] = {};
                if (!tree[header1].hasOwnProperty(header2))
                    tree[header1][header2] = [];
                tree[header1][header2].push(items[i]);
            }

            // make list including header nodes
            vm.items = [];
            angular.forEach(tree, function(h2Tree, h1) {
                if (h1) vm.items.push({name: h1, isH1: true, isHeader: true});

                angular.forEach(h2Tree, function(leafs, h2) {
                    if (h2)
                        vm.items.push({name: h2, isH2: true, isHeader: true});

                    leafs.forEach(function(item) {
                        vm.items.push(item);
                    });
                });
            });
        }

        function first() {
            return next(-1);
        }

        function last() {
            return previous(0);
        }

        function next(idx) {
            if (idx >= vm.items.length) idx = -1;

            var item;
            do {
                idx++;
                item = vm.items[idx];
            } while (item.isHeader);
            return item;
        }

        function previous(idx) {
            if (idx <= 0) idx = vm.items.length;

            var item;
            do {
                idx--;
                item = vm.items[idx];
            } while (item.isHeader);
            return item;
        }

        function indexOf(item) {
            return vm.items.indexOf(item);
        }

        function getItem(idx) {
            // returns also unselectable items
            return vm.items[idx];
        }
    }

    return {
        createInstance: function(items) {
            return new UISelectList(items);
        },
    };
});
