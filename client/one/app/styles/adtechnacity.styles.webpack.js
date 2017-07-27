function requireAll (r) { r.keys().forEach(r); }

require('./adtechnacity/main.less');
requireAll(require.context('../ajs-app/common', true, /\.less$/));
requireAll(require.context('../ajs-app/views', true, /\.less$/));
requireAll(require.context('../ajs-app/widgets', true, /\.less$/));
