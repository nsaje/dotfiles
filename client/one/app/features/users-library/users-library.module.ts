import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {AccessPermissionsComponent} from './components/access-permissions/access-permissions.component';
import {UsersLibraryView} from './views/users-library/users-library.view';

@NgModule({
    declarations: [AccessPermissionsComponent, UsersLibraryView],
    imports: [SharedModule],
    entryComponents: [UsersLibraryView],
})
export class UsersLibraryModule {}
