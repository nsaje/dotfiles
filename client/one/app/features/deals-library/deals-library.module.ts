import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {DealsLibraryView} from './views/deals-library/deals-library.view';

@NgModule({
    declarations: [DealsLibraryView],
    imports: [SharedModule],
    entryComponents: [DealsLibraryView],
})
export class DealsLibraryModule {}
