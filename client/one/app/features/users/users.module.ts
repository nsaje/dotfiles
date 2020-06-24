import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {UsersView} from './views/users.view';
import {UsersGridComponent} from './components/users-grid/users-grid.component';
import {UsersActionsComponent} from './components/users-actions/users-actions.component';
import {AccountListItemComponent} from './components/account-list-item/account-list-item.component';
import {EntityPermissionSelectorComponent} from './components/entity-permission-selector/entity-permission-selector.component';

@NgModule({
    declarations: [
        UsersView,
        UsersGridComponent,
        UsersActionsComponent,
        AccountListItemComponent,
        EntityPermissionSelectorComponent,
    ],
    imports: [SharedModule],
    entryComponents: [UsersView],
})
export class UsersModule {}
