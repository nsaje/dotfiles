import {CommonModule} from '@angular/common';
import {NgModule} from '@angular/core';

@NgModule({
    declarations: [
    ],
    exports: [
        CommonModule,
    ],
    providers: [
        ng1ServiceProvider('zemPermissions'),
    ],
})
export class SharedModule {}


function ng1ServiceProvider (serviceName: string): any {
    return {
        provide: serviceName,
        useFactory: (i: any) => i.get(serviceName), deps: ['$injector'],
    };
}
