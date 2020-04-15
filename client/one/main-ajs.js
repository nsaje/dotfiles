require('./app/ajs-app/config.module.js');
require('./app/app.constants');
require('./app/app.options');
require('./app/app.whitelabel');

requireAll(require.context('./app/ajs-app/', true, /module\.js$/));
requireAll(
    require.context(
        './app/ajs-app/',
        true,
        /^(?!.*(?:\/constants\.js$|webpack\.js$|module\.js$|tests\.ajs\.js$|spec\.js$|mock\.js$)).*\.js$/
    )
);

function requireAll(r) {
    r.keys().forEach(r);
}
