function requireAll (r) { r.keys().forEach(r); }

require('./greenpark/main.less');
requireAll(require.context('../common', true, /\.less$/));
requireAll(require.context('../views', true, /\.less$/));
requireAll(require.context('../widgets', true, /\.less$/));
