import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {CreditsView} from './views/credits/credits.view';
import {CreditsComponent} from './components/credits/credits.component';
import {CreditsScopeSelectorComponent} from './components/credits-scope-selector/credits-scope-selector.component';

@NgModule({
    declarations: [
        CreditsView,
        CreditsComponent,
        CreditsScopeSelectorComponent,
    ],
    imports: [SharedModule],
    entryComponents: [CreditsView, CreditsScopeSelectorComponent],
})
export class CreditsModule {}
