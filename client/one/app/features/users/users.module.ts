import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {UsersView} from './views/users.view';
import {UsersGridComponent} from './components/users-grid/users-grid.component';
import {UsersActionsComponent} from './components/users-actions/users-actions.component';

@NgModule({
    declarations: [UsersView, UsersGridComponent, UsersActionsComponent],
    imports: [SharedModule],
    entryComponents: [UsersView],
})
export class UsersModule {}
