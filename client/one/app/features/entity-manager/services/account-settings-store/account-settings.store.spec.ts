import {AccountService} from '../../../../core/entities/services/account/account.service';
import {AccountSettingsStore} from './account-settings.store';
import {AccountWithExtras} from '../../../../core/entities/types/account/account-with-extras';
import {Account} from '../../../../core/entities/types/account/account';
import {AccountExtras} from '../../../../core/entities/types/account/account-extras';
import * as clone from 'clone';
import {fakeAsync, tick} from '@angular/core/testing';
import {asapScheduler, of, throwError} from 'rxjs';
import {AccountSettingsStoreFieldsErrorsState} from './account-settings.store.fields-errors-state';
import {AccountType, Currency} from '../../../../app.constants';
import {AccountMediaSource} from '../../../../core/entities/types/account/account-media-source';

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

    it('should correctly change account name', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.updateState('Generic name', 'entity', 'name');
        expect(store.state.entity.name).toEqual('Generic name');
        store.setName('Generic name 2');
        expect(store.state.entity.name).toEqual('Generic name 2');
    });

    it('should correctly change account manager', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.updateState('22', 'entity', 'defaultAccountManager');
        expect(store.state.entity.defaultAccountManager).toEqual('22');
        store.setAccountManager('11');
        expect(store.state.entity.defaultAccountManager).toEqual('11');
    });

    it('should correctly change sales representative', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.updateState('22', 'entity', 'defaultSalesRepresentative');
        expect(store.state.entity.defaultSalesRepresentative).toEqual('22');
        store.setSalesRepresentative('11');
        expect(store.state.entity.defaultSalesRepresentative).toEqual('11');
    });

    it('should correctly change cs representative', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.updateState('22', 'entity', 'defaultCsRepresentative');
        expect(store.state.entity.defaultCsRepresentative).toEqual('22');
        store.setCustomerSuccessRepresentative('11');
        expect(store.state.entity.defaultCsRepresentative).toEqual('11');
    });

    it('should correctly change ob representative', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.updateState('22', 'entity', 'obRepresentative');
        expect(store.state.entity.obRepresentative).toEqual('22');
        store.setOutbrainRepresentative('11');
        expect(store.state.entity.obRepresentative).toEqual('11');
    });

    it('should correctly change account type', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.updateState(AccountType.UNKNOWN, 'entity', 'accountType');
        expect(store.state.entity.accountType).toEqual(AccountType.UNKNOWN);
        store.setAccountType(AccountType.PILOT);
        expect(store.state.entity.accountType).toEqual(AccountType.PILOT);
    });

    it('should correctly change agency id', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.updateState('22', 'entity', 'agencyId');
        expect(store.state.entity.agencyId).toEqual('22');
        store.setAgency('11');
        expect(store.state.entity.agencyId).toEqual('11');
    });

    it('should correctly change salesforce url', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.updateState('http://salesforce.com', 'entity', 'salesforceUrl');
        expect(store.state.entity.salesforceUrl).toEqual(
            'http://salesforce.com'
        );
        store.setSalesforceUrl('http://salesforce2.com');
        expect(store.state.entity.salesforceUrl).toEqual(
            'http://salesforce2.com'
        );
    });

    it('should correctly change currency', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.updateState(Currency.USD, 'entity', 'currency');
        expect(store.state.entity.currency).toEqual(Currency.USD);
        store.setCurrency(Currency.EUR);
        expect(store.state.entity.currency).toEqual(Currency.EUR);
    });

    it('should correctly change frequency capping', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.updateState(22, 'entity', 'frequencyCapping');
        expect(store.state.entity.frequencyCapping).toEqual(22);
        store.setFrequencyCapping('30');
        expect(store.state.entity.frequencyCapping).toEqual(30);
    });

    it('should correctly set publisher groups', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();
        const $event: any = {
            whitelistedPublisherGroups: [123, 456, 789],
            blacklistedPublisherGroups: [],
        };

        expect(store.state.entity.targeting.publisherGroups).toEqual({
            included: [],
            excluded: [],
        });

        store.setPublisherGroupsTargeting($event);

        expect(store.state.entity.targeting.publisherGroups).toEqual({
            included: $event.whitelistedPublisherGroups,
            excluded: $event.blacklistedPublisherGroups,
        });
    });

    it('should correctly change auto add new sources', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.updateState(false, 'entity', 'autoAddNewSources');
        expect(store.state.entity.autoAddNewSources).toEqual(false);
        store.setAutoAddNewSources(true);
        expect(store.state.entity.autoAddNewSources).toEqual(true);
    });

    it('should correctly add to allowed media sources', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        const mockedMediaSources: AccountMediaSource[] = [
            {
                id: '1',
                name: 'Source 1',
                released: true,
                deprecated: false,
                allowed: false,
            },
            {
                id: '2',
                name: 'Source 2',
                released: true,
                deprecated: false,
                allowed: false,
            },
        ];

        store.updateState(mockedMediaSources, 'entity', 'mediaSources');
        expect(store.state.entity.mediaSources).toEqual(mockedMediaSources);
        store.addToAllowedMediaSources(['1', '2']);
        expect(store.state.entity.mediaSources).toEqual(
            mockedMediaSources.map(item => {
                return {
                    ...item,
                    allowed: true,
                };
            })
        );
    });

    it('should correctly remove from allowed media sources', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        const mockedMediaSources: AccountMediaSource[] = [
            {
                id: '1',
                name: 'Source 1',
                released: true,
                deprecated: false,
                allowed: true,
            },
            {
                id: '2',
                name: 'Source 2',
                released: true,
                deprecated: false,
                allowed: true,
            },
        ];

        store.updateState(mockedMediaSources, 'entity', 'mediaSources');
        expect(store.state.entity.mediaSources).toEqual(mockedMediaSources);
        store.removeFromAllowedMediaSources(['1', '2']);
        expect(store.state.entity.mediaSources).toEqual(
            mockedMediaSources.map(item => {
                return {
                    ...item,
                    allowed: false,
                };
            })
        );
    });
});
