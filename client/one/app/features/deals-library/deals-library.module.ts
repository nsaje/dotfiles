import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {DealsLibraryView} from './views/deals-library/deals-library.view';
import {DealEditFormComponent} from './components/deal-edit-form/deal-edit-form.component';

@NgModule({
    declarations: [DealsLibraryView, DealEditFormComponent],
    imports: [SharedModule],
    entryComponents: [DealsLibraryView],
})
export class DealsLibraryModule {}
