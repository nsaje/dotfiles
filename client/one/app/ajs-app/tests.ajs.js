requireAll(require.context('./test/', true, /\.js$/));
requireAll(require.context('./', true, /spec\.js$|mock\.js$/));

function requireAll (r) { r.keys().forEach(r); }
