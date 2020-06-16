import {NgModule} from '@angular/core';
import {AlertsEndpoint} from './services/alerts.endpoint';
import {AlertsService} from './services/alerts.service';

@NgModule({
    providers: [AlertsEndpoint, AlertsService],
})
export class AlertsModule {}
