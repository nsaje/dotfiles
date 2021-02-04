import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {CreativesView} from './views/creatives/creatives.view';
import {CreativesSharedModule} from './creatives-shared/creatives-shared.module';
import {CreativeBatchView} from './views/creative-batch/creative-batch.view';

@NgModule({
    declarations: [CreativesView, CreativeBatchView],
    imports: [SharedModule, CreativesSharedModule],
    entryComponents: [CreativesView, CreativeBatchView],
})
export class CreativesModule {}
