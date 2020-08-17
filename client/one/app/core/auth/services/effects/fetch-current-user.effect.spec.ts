import {UsersService} from '../../../users/services/users.service';
import {User} from '../../../users/types/user';
import {UserStatus} from '../../../../app.constants';
import {
    FetchCurrentUserActionEffect,
    FetchCurrentUserAction,
} from './fetch-current-user.effect';
import {of, asapScheduler} from 'rxjs';
import {AuthStoreState} from '../auth.store.state';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import {SetCurrentUserAction} from '../reducers/set-current-user.reducer';
import {fakeAsync, tick} from '@angular/core/testing';

describe('FetchCurrentUserActionEffect', () => {
    let usersServiceStub: jasmine.SpyObj<UsersService>;
    let mockedUser: User;
    let effect: FetchCurrentUserActionEffect;
    let requestStateUpdater: RequestStateUpdater;

    beforeEach(() => {
        usersServiceStub = jasmine.createSpyObj(UsersService.name, ['current']);
        requestStateUpdater = (requestName, requestState) => {};

        effect = new FetchCurrentUserActionEffect(usersServiceStub);
        mockedUser = {
            id: '123',
            email: 'test@test.com',
            firstName: 'test',
            lastName: 'test',
            name: 'test tests',
            status: UserStatus.ACTIVE,
            agencies: [71],
            timezoneOffset: -4000,
            intercomUserHash: '$test$',
            defaultCsvSeparator: ',',
            defaultCsvDecimalSeparator: '.',
            permissions: [],
            entityPermissions: [],
        };
    });

    it('should fetch user via service', fakeAsync(() => {
        spyOn(effect, 'dispatch').and.returnValue(Promise.resolve(true));

        usersServiceStub.current.and
            .returnValue(of(mockedUser, asapScheduler))
            .calls.reset();

        effect.effect(
            new AuthStoreState(),
            new FetchCurrentUserAction({
                requestStateUpdater: requestStateUpdater,
            })
        );
        tick();

        expect(usersServiceStub.current).toHaveBeenCalledTimes(1);
        expect(usersServiceStub.current).toHaveBeenCalledWith(
            requestStateUpdater
        );

        expect(effect.dispatch).toHaveBeenCalledTimes(1);
        expect(effect.dispatch).toHaveBeenCalledWith(
            new SetCurrentUserAction(mockedUser)
        );
    }));
});
