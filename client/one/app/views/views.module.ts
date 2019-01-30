import {NgModule} from '@angular/core';
import {NewEntityAnalyticsMockView} from './zem-new-entity-analytics-mock/new-entity-analytics-mock.view';

const EXPORTED_DECLARATIONS = [NewEntityAnalyticsMockView];

@NgModule({
    declarations: EXPORTED_DECLARATIONS,
    exports: [...EXPORTED_DECLARATIONS],
    entryComponents: [NewEntityAnalyticsMockView],
})
export class ViewsModule {}
