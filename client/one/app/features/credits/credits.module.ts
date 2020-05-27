import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {CreditsLegacyView} from './views/credits-legacy/credits-legacy.view';
import {CreditsView} from './views/credits/credits.view';
import {CreditsComponent} from './components/credits/credits.component';
import {CreditsScopeSelectorComponent} from './components/credits-scope-selector/credits-scope-selector.component';
import {CreditsTotalsComponent} from './components/credits-totals/credits-totals.component';
import {CreditEditFormComponent} from './components/credit-edit-form/credit-edit-form.component';

@NgModule({
    declarations: [
        CreditsLegacyView,
        CreditsView,
        CreditsComponent,
        CreditsScopeSelectorComponent,
        CreditsTotalsComponent,
        CreditEditFormComponent,
    ],
    imports: [SharedModule],
    entryComponents: [
        CreditsLegacyView,
        CreditsView,
        CreditsScopeSelectorComponent,
    ],
})
export class CreditsModule {}
