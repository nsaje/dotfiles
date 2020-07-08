import {ICellRendererParams} from 'ag-grid-community';
import {UsersView} from '../../../views/users.view';
import {User} from '../../../../../core/users/types/user';

export interface UserRendererParams extends ICellRendererParams {
    context: {
        componentParent: UsersView;
    };
    data: User;
}
