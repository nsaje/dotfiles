# List Group Component

This component is able to render recursive component tree structure used for expandable and collapsable menu. Each item (of `ListGroupItem` type) is able to have array of sub items (also `ListGroupItem` type), this structure can go `n` level deep. `ListGroupComponent` itself is a component that renders all root nodes (level 0) using `ListGroupItemComponent`. Every sub item is then also rendered by `ListGroupItemComponent` in recursive fashion (component recursion).

## List Group Item Component

This component represents the tree node itself which in this context is a menu item containing a name, an icon and a value (path segment) and sub items, this `item` is the main input. Each item also receives information about a whole path to the root from it's parent. That together with it's own path forms the main output event value that is then used outside to control router navigation and also as an input into it's own sub items.

Example:

    Automation rules (parentItemPath: ['v2'], value: 'rules', selectedItemPath: ['v2', 'rules', 'history']) - will be Expanded by default, because it has selected sub items
      |
      |---- Library (parentItemPath: ['v2', 'rules'], value: '', selectedItemPath: ['v2', 'rules', 'history'])
      |---- History (parentItemPath: ['v2', 'rules'], value: 'history', selectedItemPath: ['v2', 'rules', 'history']) - will be Selected, because parentItemPath + itself matches selectedItemPath

From this example the output event payload of the first sub item is `['v2', 'rules']` (empty string is ignored and not appended) and output of second sub item is `['v2', 'rules', 'history']` . These arrays are then used in the parent view by the router to navigate to URLs `/v2/rules` and `/v2/rules/history` respectively. These arrays also serve as the `parentItemPath` input to their potential sub items and also same structure is used `selectedItemPath` input that contains current navigation to mark selected item.

This mechanism allows us to define just segments of the URL path as `RoutePathName`, for example`{ RULES = 'rules', RULES_HISTORY = 'history' }` instead of defining a composite path like ~~`RULES_HISTORY = 'rules/history'`~~ this means and it is visible from previous example that each node carries it's own segment and the overall path is constructed by collecting the value of nodes on the path from root to leaf nodes.

## N-level menu item style

Each level menu item has associated class with `--level-n` (where `n` is a number) modifier so that sub items on different levels can have different look. These styles are defined in `list-group-item/list-group-item.component.less`

Example:

    .zem-list-group-item__item--level-1 {
      height: 40px;
      background-color: darken(@color--lighter-neutral, 12%);
    }
