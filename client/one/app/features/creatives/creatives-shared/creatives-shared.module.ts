import {NgModule} from '@angular/core';

import {SharedModule} from '../../../shared/shared.module';
import {CreativesComponent} from './components/creatives/creatives.component';
import {CreativesActionsComponent} from './components/creatives-actions/creatives-actions.component';

const EXPORTED_DECLARATIONS = [CreativesComponent, CreativesActionsComponent];

@NgModule({
    imports: [SharedModule],
    entryComponents: [],
    declarations: EXPORTED_DECLARATIONS,
    exports: EXPORTED_DECLARATIONS,
})
export class CreativesSharedModule {}
