import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {ScheduledReportsComponent} from './components/scheduled-reports/scheduled-reports.component';
import {ScheduledReportsView} from './views/scheduled-reports/scheduled-reports.view';

@NgModule({
    declarations: [ScheduledReportsComponent, ScheduledReportsView],
    imports: [SharedModule],
    entryComponents: [ScheduledReportsView],
})
export class ScheduledReportsModule {}
