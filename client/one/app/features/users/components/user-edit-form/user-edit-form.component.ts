import './user-edit-form.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';
import {User} from '../../../../core/users/types/user';
import {ChangeEvent} from '../../../../shared/types/change-event';
import {UsersStoreFieldsErrorsState} from '../../services/users-store/users.store.fields-errors-state';

@Component({
    selector: 'zem-user-edit-form',
    templateUrl: './user-edit-form.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class UserEditFormComponent {
    @Input()
    user: User;
    @Input()
    userErrors: UsersStoreFieldsErrorsState;
    @Input()
    isDisabled: boolean = false;
    @Output()
    userChange = new EventEmitter<ChangeEvent<User>>();

    onEmailChange(email: string) {
        this.emitUserChanges({email});
    }

    onFirstNameChange(firstName: string) {
        this.emitUserChanges({firstName});
    }

    onLastNameChange(lastName: string) {
        this.emitUserChanges({lastName});
    }

    private emitUserChanges(changes: Partial<User>) {
        this.userChange.emit({
            target: this.user,
            changes,
        });
    }
}
