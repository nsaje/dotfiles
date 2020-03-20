import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {CreditsLibraryView} from './views/credits-library/credits-library.view';
import {CreditsComponent} from './components/credits/credits.component';
import {CreditsScopeSelectorComponent} from './components/credits-scope-selector/credits-scope-selector.component';

@NgModule({
    declarations: [
        CreditsLibraryView,
        CreditsComponent,
        CreditsScopeSelectorComponent,
    ],
    imports: [SharedModule],
    entryComponents: [CreditsLibraryView, CreditsScopeSelectorComponent],
})
export class CreditsLibraryModule {}
