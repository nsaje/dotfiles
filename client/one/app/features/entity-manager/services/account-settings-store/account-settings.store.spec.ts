import {AccountService} from '../../../../core/entities/services/account/account.service';
import {AccountSettingsStore} from './account-settings.store';
import {AccountWithExtras} from '../../../../core/entities/types/account/account-with-extras';
import {Account} from '../../../../core/entities/types/account/account';
import {AccountExtras} from '../../../../core/entities/types/account/account-extras';
import * as clone from 'clone';
import {fakeAsync, tick} from '@angular/core/testing';
import {asapScheduler, of, throwError} from 'rxjs';
import {AccountSettingsStoreFieldsErrorsState} from './account-settings.store.fields-errors-state';

describe('AccountSettingsStore', () => {
    let accountServiceStub: jasmine.SpyObj<AccountService>;
    let store: AccountSettingsStore;
    let accountWithExtras: AccountWithExtras;
    let account: Account;
    let accountExtras: AccountExtras;

    beforeEach(() => {
        accountServiceStub = jasmine.createSpyObj(AccountService.name, [
            'defaults',
            'get',
            'validate',
            'save',
            'archive',
        ]);

        store = new AccountSettingsStore(accountServiceStub);
        account = clone(store.state.entity);
        accountExtras = clone(store.state.extras);
        accountWithExtras = {
            account: account,
            extras: accountExtras,
        };
    });

    it('should get default account via service', fakeAsync(() => {
        const mockedAccountWithExtras = clone(accountWithExtras);
        mockedAccountWithExtras.account.name = 'New account';
        mockedAccountWithExtras.account.agencyId = '12345';

        accountServiceStub.defaults.and
            .returnValue(of(mockedAccountWithExtras, asapScheduler))
            .calls.reset();

        expect(store.state.entity).toEqual(account);
        expect(store.state.extras).toEqual(accountExtras);
        expect(store.state.fieldsErrors).toEqual(
            new AccountSettingsStoreFieldsErrorsState()
        );

        store.loadEntityDefaults();
        tick();

        expect(store.state.entity).toEqual(mockedAccountWithExtras.account);
        expect(store.state.extras).toEqual(mockedAccountWithExtras.extras);
        expect(store.state.fieldsErrors).toEqual(
            new AccountSettingsStoreFieldsErrorsState()
        );

        expect(accountServiceStub.defaults).toHaveBeenCalledTimes(1);
    }));

    it('should get account via service', fakeAsync(() => {
        const mockedAccountWithExtras = clone(accountWithExtras);
        mockedAccountWithExtras.account.id = '12345';
        mockedAccountWithExtras.account.name = 'Test account 1';
        mockedAccountWithExtras.account.agencyId = '12345';

        accountServiceStub.get.and
            .returnValue(of(mockedAccountWithExtras, asapScheduler))
            .calls.reset();

        expect(store.state.entity).toEqual(account);
        expect(store.state.extras).toEqual(accountExtras);
        expect(store.state.fieldsErrors).toEqual(
            new AccountSettingsStoreFieldsErrorsState()
        );

        store.loadEntity('12345');
        tick();

        expect(store.state.entity).toEqual(mockedAccountWithExtras.account);
        expect(store.state.extras).toEqual(mockedAccountWithExtras.extras);
        expect(store.state.fieldsErrors).toEqual(
            new AccountSettingsStoreFieldsErrorsState()
        );

        expect(accountServiceStub.get).toHaveBeenCalledTimes(1);
    }));

    it('should correctly handle errors when validating account via service', fakeAsync(() => {
        const mockedAccountWithExtras = clone(accountWithExtras);
        mockedAccountWithExtras.account.id = '12345';
        mockedAccountWithExtras.account.agencyId = '12345';

        store.state.entity = mockedAccountWithExtras.account;
        store.state.extras = mockedAccountWithExtras.extras;

        accountServiceStub.validate.and
            .returnValue(
                throwError({
                    message: 'Validation error',
                    error: {
                        details: {name: ['Please specify account name.']},
                    },
                })
            )
            .calls.reset();

        store.validateEntity();
        tick();

        expect(store.state.entity).toEqual(mockedAccountWithExtras.account);
        expect(store.state.extras).toEqual(mockedAccountWithExtras.extras);
        expect(store.state.fieldsErrors).toEqual(
            jasmine.objectContaining({
                ...new AccountSettingsStoreFieldsErrorsState(),
                name: ['Please specify account name.'],
            })
        );

        expect(accountServiceStub.validate).toHaveBeenCalledTimes(1);

        accountServiceStub.validate.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();

        store.validateEntity();
        tick();

        expect(store.state.entity).toEqual(mockedAccountWithExtras.account);
        expect(store.state.extras).toEqual(mockedAccountWithExtras.extras);
        expect(store.state.fieldsErrors).toEqual(
            new AccountSettingsStoreFieldsErrorsState()
        );

        expect(accountServiceStub.validate).toHaveBeenCalledTimes(1);
    }));

    it('should successfully save account via service', fakeAsync(() => {
        const mockedAccountWithExtras = clone(accountWithExtras);
        mockedAccountWithExtras.account.id = '12345';
        mockedAccountWithExtras.account.name = 'Test account 1';
        mockedAccountWithExtras.account.agencyId = '12345';

        accountServiceStub.get.and
            .returnValue(of(mockedAccountWithExtras, asapScheduler))
            .calls.reset();

        accountServiceStub.save.and
            .returnValue(of(mockedAccountWithExtras.account, asapScheduler))
            .calls.reset();

        store.loadEntity('12345');
        tick();

        store.saveEntity();
        tick();

        expect(store.state.entity).toEqual(mockedAccountWithExtras.account);
        expect(store.state.fieldsErrors).toEqual(
            new AccountSettingsStoreFieldsErrorsState()
        );
        expect(accountServiceStub.save).toHaveBeenCalledTimes(1);
    }));

    it('should correctly handle errors when saving account via service', fakeAsync(() => {
        const mockedAccountWithExtras = clone(accountWithExtras);
        mockedAccountWithExtras.account.id = '12345';
        mockedAccountWithExtras.account.agencyId = '12345';

        accountServiceStub.get.and
            .returnValue(of(mockedAccountWithExtras, asapScheduler))
            .calls.reset();

        accountServiceStub.save.and
            .returnValue(
                throwError({
                    message: 'Validation error',
                    error: {
                        details: {name: ['Please specify account name.']},
                    },
                })
            )
            .calls.reset();

        store.loadEntity('12345');
        tick();

        store.saveEntity();
        tick();

        expect(store.state.entity).toEqual(mockedAccountWithExtras.account);
        expect(store.state.fieldsErrors).toEqual(
            jasmine.objectContaining({
                ...new AccountSettingsStoreFieldsErrorsState(),
                name: ['Please specify account name.'],
            })
        );
        expect(accountServiceStub.save).toHaveBeenCalledTimes(1);
    }));

    it('should successfully archive account via service', async () => {
        const mockedAccount = clone(account);
        mockedAccount.id = '12345';
        mockedAccount.name = 'Test campaign 1';
        mockedAccount.agencyId = '12345';
        mockedAccount.archived = false;

        store.state.entity = mockedAccount;

        const archivedAccount = clone(mockedAccount);
        archivedAccount.archived = true;

        accountServiceStub.archive.and
            .returnValue(of(archivedAccount, asapScheduler))
            .calls.reset();

        const shouldReload = await store.archiveEntity();

        expect(accountServiceStub.archive).toHaveBeenCalledTimes(1);
        expect(shouldReload).toBe(true);
    });

    it('should successfully handle errors when archiving account via service', async () => {
        const mockedAccount = clone(account);
        mockedAccount.id = '12345';
        mockedAccount.name = 'Test campaign 1';
        mockedAccount.agencyId = '12345';
        mockedAccount.archived = false;

        store.state.entity = mockedAccount;

        accountServiceStub.archive.and
            .returnValue(
                throwError({
                    message: 'Internal server error',
                })
            )
            .calls.reset();

        const shouldReload = await store.archiveEntity();

        expect(accountServiceStub.archive).toHaveBeenCalledTimes(1);
        expect(shouldReload).toBe(false);
    });

    it('should correctly determine if account settings have unsaved changes', fakeAsync(() => {
        accountServiceStub.get.and
            .returnValue(of(clone(accountWithExtras), asapScheduler))
            .calls.reset();

        expect(store.doEntitySettingsHaveUnsavedChanges()).toBe(false);

        store.loadEntity('12345');
        tick();
        expect(store.doEntitySettingsHaveUnsavedChanges()).toBe(false);

        store.setState({
            ...store.state,
            entity: {...store.state.entity, name: 'Modified name'},
        });
        expect(store.doEntitySettingsHaveUnsavedChanges()).toBe(true);
    }));
});
