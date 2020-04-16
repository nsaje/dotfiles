import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {AccessPermissionsComponent} from './components/access-permissions/access-permissions.component';
import {UserPermissionsView} from './views/user-permissions/user-permissions.view';

@NgModule({
    declarations: [AccessPermissionsComponent, UserPermissionsView],
    imports: [SharedModule],
    entryComponents: [UserPermissionsView],
})
export class UserPermissionsModule {}
