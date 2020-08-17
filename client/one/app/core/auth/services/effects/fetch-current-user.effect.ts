import {StoreAction} from '../../../../shared/services/store/store.action';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import {StoreEffect} from '../../../../shared/services/store/store.effect';
import {Injectable} from '@angular/core';
import {SetCurrentUserAction} from '../reducers/set-current-user.reducer';
import {AuthStoreState} from '../auth.store.state';
import {UsersService} from '../../../users/services/users.service';
import {User} from '../../../users/types/user';
import {takeUntil} from 'rxjs/operators';

export class FetchCurrentUserAction extends StoreAction<{
    requestStateUpdater: RequestStateUpdater;
}> {}

// tslint:disable-next-line: max-classes-per-file
@Injectable()
export class FetchCurrentUserActionEffect extends StoreEffect<
    AuthStoreState,
    FetchCurrentUserAction
> {
    constructor(private service: UsersService) {
        super();
    }

    effect(
        state: AuthStoreState,
        action: FetchCurrentUserAction
    ): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            this.service
                .current(action.payload.requestStateUpdater)
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (user: User) => {
                        this.dispatch(new SetCurrentUserAction(user));
                        resolve(true);
                    },
                    () => {
                        resolve(false);
                    }
                );
        });
    }
}
