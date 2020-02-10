import {asapScheduler, of} from 'rxjs';
import * as clone from 'clone';
import {EntitiesUpdatesService} from '../entities-updates.service';
import {EntityType, EntityUpdateAction} from '../../../../app.constants';
import {tick, fakeAsync} from '@angular/core/testing';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import * as mockHelpers from '../../../../testing/mock.helpers';
import {Account} from '../../types/account/account';
import {AccountService} from './account.service';
import {AccountEndpoint} from './account.endpoint';
import {AccountWithExtras} from '../../types/account/account-with-extras';
import {AccountExtras} from '../../types/account/account-extras';

describe('AccountService', () => {
    let service: AccountService;
    let accountEndpointStub: jasmine.SpyObj<AccountEndpoint>;
    let entitiesUpdatesServiceStub: jasmine.SpyObj<EntitiesUpdatesService>;
    let mockedAccountWithExtras: AccountWithExtras;
    let mockedAccount: Account;
    let mockedAccountExtras: AccountExtras;
    let requestStateUpdater: RequestStateUpdater;

    beforeEach(() => {
        accountEndpointStub = jasmine.createSpyObj(AccountEndpoint.name, [
            'defaults',
            'get',
            'list',
            'validate',
            'create',
            'edit',
        ]);

        entitiesUpdatesServiceStub = jasmine.createSpyObj(
            EntitiesUpdatesService.name,
            ['registerEntityUpdate']
        );

        mockedAccount = mockHelpers.getMockedAccount();
        mockedAccount.id = '12345';
        mockedAccount.agencyId = '12345';
        mockedAccount.name = 'Test account';

        mockedAccountExtras = mockHelpers.getMockedAccountExtras();

        mockedAccountWithExtras = {
            account: mockedAccount,
            extras: mockedAccountExtras,
        };

        service = new AccountService(
            accountEndpointStub,
            entitiesUpdatesServiceStub
        );

        requestStateUpdater = (requestName, requestState) => {};
    });

    it('should get default account via endpoint', () => {
        const mockedNewAccountWithExtras = clone(mockedAccountWithExtras);
        mockedNewAccountWithExtras.account.id = null;
        mockedNewAccountWithExtras.account.name = 'New account';

        accountEndpointStub.defaults.and
            .returnValue(of(mockedNewAccountWithExtras, asapScheduler))
            .calls.reset();

        service.defaults(requestStateUpdater).subscribe(accountWithExtras => {
            expect(accountWithExtras.account).toEqual(
                mockedNewAccountWithExtras.account
            );
            expect(accountWithExtras.extras).toEqual(
                mockedNewAccountWithExtras.extras
            );
        });
        expect(accountEndpointStub.defaults).toHaveBeenCalledTimes(1);
        expect(accountEndpointStub.defaults).toHaveBeenCalledWith(
            requestStateUpdater
        );
    });

    it('should get account via endpoint', () => {
        accountEndpointStub.get.and
            .returnValue(of(mockedAccountWithExtras, asapScheduler))
            .calls.reset();

        service
            .get(mockedAccount.id, requestStateUpdater)
            .subscribe(accountWithExtras => {
                expect(accountWithExtras.account).toEqual(mockedAccount);
                expect(accountWithExtras.extras).toEqual(mockedAccountExtras);
            });
        expect(accountEndpointStub.get).toHaveBeenCalledTimes(1);
        expect(accountEndpointStub.get).toHaveBeenCalledWith(
            mockedAccount.id,
            requestStateUpdater
        );
    });

    it('should list all accounts for user via endpoint', () => {
        const mockedAgencyId = '1';
        accountEndpointStub.list.and
            .returnValue(of([mockedAccount], asapScheduler))
            .calls.reset();

        service
            .list(mockedAgencyId, requestStateUpdater)
            .subscribe(accounts => {
                expect(accounts[0]).toEqual(mockedAccount);
            });
        expect(accountEndpointStub.list).toHaveBeenCalledTimes(1);
        expect(accountEndpointStub.list).toHaveBeenCalledWith(
            mockedAgencyId,
            requestStateUpdater
        );
    });

    it('should save new account and register entity update', fakeAsync(() => {
        accountEndpointStub.create.and
            .returnValue(of(mockedAccount, asapScheduler))
            .calls.reset();

        const mockedNewAccount = clone(mockedAccount);
        mockedNewAccount.id = null;
        service
            .save(mockedNewAccount, requestStateUpdater)
            .subscribe(account => {
                expect(account).toEqual(mockedAccount);
            });
        tick();

        expect(accountEndpointStub.create).toHaveBeenCalledTimes(1);
        expect(accountEndpointStub.create).toHaveBeenCalledWith(
            mockedNewAccount,
            requestStateUpdater
        );
        expect(accountEndpointStub.edit).not.toHaveBeenCalled();
        expect(
            entitiesUpdatesServiceStub.registerEntityUpdate
        ).toHaveBeenCalledWith({
            id: mockedAccount.id,
            type: EntityType.ACCOUNT,
            action: EntityUpdateAction.CREATE,
        });
    }));

    it('should edit existing account and register entity update', fakeAsync(() => {
        accountEndpointStub.edit.and
            .returnValue(of(mockedAccount, asapScheduler))
            .calls.reset();

        service.save(mockedAccount, requestStateUpdater).subscribe(account => {
            expect(account).toEqual(mockedAccount);
        });
        tick();

        expect(accountEndpointStub.edit).toHaveBeenCalledTimes(1);
        expect(accountEndpointStub.edit).toHaveBeenCalledWith(
            mockedAccount,
            requestStateUpdater
        );
        expect(accountEndpointStub.create).not.toHaveBeenCalled();
        expect(
            entitiesUpdatesServiceStub.registerEntityUpdate
        ).toHaveBeenCalledWith({
            id: mockedAccount.id,
            type: EntityType.ACCOUNT,
            action: EntityUpdateAction.EDIT,
        });
    }));

    it('should archive account and register entity update', fakeAsync(() => {
        accountEndpointStub.edit.and
            .returnValue(of({...mockedAccount, archived: true}, asapScheduler))
            .calls.reset();

        service.archive(mockedAccount.id, requestStateUpdater).subscribe();
        tick();

        expect(accountEndpointStub.edit).toHaveBeenCalledTimes(1);
        expect(accountEndpointStub.edit).toHaveBeenCalledWith(
            {
                id: mockedAccount.id,
                archived: true,
            },
            requestStateUpdater
        );
        expect(
            entitiesUpdatesServiceStub.registerEntityUpdate
        ).toHaveBeenCalledWith({
            id: mockedAccount.id,
            type: EntityType.ACCOUNT,
            action: EntityUpdateAction.ARCHIVE,
        });
    }));
});
