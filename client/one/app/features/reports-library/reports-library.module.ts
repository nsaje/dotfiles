import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {ScheduledReportsComponent} from './components/scheduled-reports/scheduled-reports.component';
import {ReportsLibraryView} from './views/reports-library/reports-library.view';

@NgModule({
    declarations: [ScheduledReportsComponent, ReportsLibraryView],
    imports: [SharedModule],
    entryComponents: [ReportsLibraryView],
})
export class ReportsLibraryModule {}
