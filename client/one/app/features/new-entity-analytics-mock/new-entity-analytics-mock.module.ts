import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {NewEntityAnalyticsMockView} from './views/new-entity-analytics-mock/new-entity-analytics-mock.view';

@NgModule({
    declarations: [NewEntityAnalyticsMockView],
    imports: [SharedModule],
    entryComponents: [NewEntityAnalyticsMockView],
})
export class NewEntityAnalyticsMockModule {}
