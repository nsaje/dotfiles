import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {CreativesView} from './views/creatives/creatives.view';

@NgModule({
    declarations: [CreativesView],
    imports: [SharedModule],
    entryComponents: [CreativesView],
})
export class CreativesModule {}
