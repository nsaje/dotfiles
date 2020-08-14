import './user-actions-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {User} from '../../../../core/users/types/user';
import {UserRendererParams} from './types/user.renderer-params';

@Component({
    templateUrl: './user-actions-cell.component.html',
})
export class UserActionsCellComponent implements ICellRendererAngularComp {
    params: UserRendererParams;
    user: User;
    isReadOnlyUser: boolean;
    isCurrentUser: boolean;

    agInit(params: UserRendererParams) {
        this.params = params;
        this.user = params.data;

        this.isReadOnlyUser = this.params.context.componentParent.store.isUserReadOnly(
            this.user
        );

        this.isCurrentUser = this.params.context.componentParent.store.isCurrentUser(
            this.user
        );
    }

    removeUser() {
        this.params.context.componentParent.removeUser(this.user);
    }

    openEditUserModal() {
        this.params.context.componentParent.openEditUserModal(this.user);
    }

    resendEmail() {
        this.params.context.componentParent.resendEmail(this.user);
    }

    refresh(): boolean {
        return false;
    }
}
