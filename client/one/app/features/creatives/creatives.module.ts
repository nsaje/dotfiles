import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {CreativesView} from './views/creatives/creatives.view';
import {CreativesSharedModule} from './creatives-shared/creatives-shared.module';

@NgModule({
    declarations: [CreativesView],
    imports: [SharedModule, CreativesSharedModule],
    entryComponents: [CreativesView],
})
export class CreativesModule {}
