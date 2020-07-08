import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {UsersView} from './views/users.view';
import {UsersGridComponent} from './components/users-grid/users-grid.component';
import {UsersActionsComponent} from './components/users-actions/users-actions.component';
import {AccountListItemComponent} from './components/account-list-item/account-list-item.component';
import {EntityPermissionSelectorComponent} from './components/entity-permission-selector/entity-permission-selector.component';
import {UserActionsCellComponent} from './components/user-actions-cell/user-actions-cell.component';
import {UserEditFormComponent} from './components/user-edit-form/user-edit-form.component';

@NgModule({
    declarations: [
        UsersView,
        UsersGridComponent,
        UsersActionsComponent,
        AccountListItemComponent,
        EntityPermissionSelectorComponent,
        UserActionsCellComponent,
        UserEditFormComponent,
    ],
    imports: [SharedModule],
    entryComponents: [UsersView, UserActionsCellComponent],
})
export class UsersModule {}
