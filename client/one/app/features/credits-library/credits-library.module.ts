import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {CreditsLibraryView} from './views/credits-library/credits-library.view';
import {AccountCreditComponent} from './components/account-credit/account-credit.component';

@NgModule({
    declarations: [CreditsLibraryView, AccountCreditComponent],
    imports: [SharedModule],
    entryComponents: [CreditsLibraryView],
})
export class CreditsLibraryModule {}
