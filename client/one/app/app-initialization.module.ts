import {NgModule, APP_INITIALIZER} from '@angular/core';
import {UpgradeModule} from '@angular/upgrade/static';

export function bootstrap(upgrade: UpgradeModule) {
    return () => upgrade.bootstrap(document.body, ['one'], {strictDi: true});
}

@NgModule({
    providers: [
        {
            provide: APP_INITIALIZER,
            useFactory: bootstrap,
            deps: [UpgradeModule],
            multi: true,
        },
    ],
})
export class AppInitializationModule {}
