import {CommonModule} from '@angular/common';
import {HttpClientModule, HttpClientXsrfModule} from '@angular/common/http';
import {NgModule} from '@angular/core';

@NgModule({
    imports: [
        HttpClientModule,
        HttpClientXsrfModule.withOptions({
            cookieName: 'csrftoken',
            headerName: 'X-CSRFToken',
        }),
    ],
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
