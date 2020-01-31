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
import {DealsService} from '../../../../core/deals/services/deals.service';
import {Deal} from '../../../../core/deals/types/deal';
import {SourcesService} from '../../../../core/sources/services/sources.service';
import {Source} from '../../../../core/sources/types/source';

describe('AccountSettingsStore', () => {
    let accountServiceStub: jasmine.SpyObj<AccountService>;
    let dealsServiceStub: jasmine.SpyObj<DealsService>;
    let sourcesServiceStub: jasmine.SpyObj<SourcesService>;
    let store: AccountSettingsStore;
    let accountWithExtras: AccountWithExtras;
    let account: Account;
    let accountExtras: AccountExtras;
    let mockedSources: Source[];

    beforeEach(() => {
        accountServiceStub = jasmine.createSpyObj(AccountService.name, [
            'defaults',
            'get',
            'validate',
            'save',
            'archive',
        ]);
        dealsServiceStub = jasmine.createSpyObj(DealsService.name, ['list']);
        sourcesServiceStub = jasmine.createSpyObj(SourcesService.name, [
            'list',
        ]);

        store = new AccountSettingsStore(
            accountServiceStub,
            dealsServiceStub,
            sourcesServiceStub
        );
        account = clone(store.state.entity);
        accountExtras = clone(store.state.extras);
        accountWithExtras = {
            account: account,
            extras: accountExtras,
        };
        mockedSources = [
            {slug: 'smaato', name: 'Smaato', released: true, deprecated: false},
        ];
    });

    it('should get default account and sources list via service', fakeAsync(() => {
        const mockedAccountWithExtras = clone(accountWithExtras);
        mockedAccountWithExtras.account.name = 'New account';
        mockedAccountWithExtras.account.agencyId = '12345';

        accountServiceStub.defaults.and
            .returnValue(of(mockedAccountWithExtras, asapScheduler))
            .calls.reset();

        sourcesServiceStub.list.and
            .returnValue(of(mockedSources, asapScheduler))
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
        expect(store.state.sources).toEqual(mockedSources);

        expect(accountServiceStub.defaults).toHaveBeenCalledTimes(1);
        expect(sourcesServiceStub.list).toHaveBeenCalledTimes(1);
    }));

    it('should get account via service', fakeAsync(() => {
        const mockedAccountWithExtras = clone(accountWithExtras);
        mockedAccountWithExtras.account.id = '12345';
        mockedAccountWithExtras.account.name = 'Test account 1';
        mockedAccountWithExtras.account.agencyId = '12345';

        accountServiceStub.get.and
            .returnValue(of(mockedAccountWithExtras, asapScheduler))
            .calls.reset();

        sourcesServiceStub.list.and
            .returnValue(of(mockedSources, asapScheduler))
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
        expect(store.state.sources).toEqual(mockedSources);

        expect(accountServiceStub.get).toHaveBeenCalledTimes(1);
        expect(sourcesServiceStub.list).toHaveBeenCalledTimes(1);
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

        sourcesServiceStub.list.and
            .returnValue(of(mockedSources, asapScheduler))
            .calls.reset();

        store.loadEntity('12345');
        tick();

        store.saveEntity();
        tick();

        expect(store.state.entity).toEqual(mockedAccountWithExtras.account);
        expect(store.state.fieldsErrors).toEqual(
            new AccountSettingsStoreFieldsErrorsState()
        );
        expect(store.state.sources).toEqual(mockedSources);

        expect(accountServiceStub.save).toHaveBeenCalledTimes(1);
        expect(sourcesServiceStub.list).toHaveBeenCalledTimes(1);
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

        sourcesServiceStub.list.and
            .returnValue(of(mockedSources, asapScheduler))
            .calls.reset();

        store.loadEntity('12345');
        tick();

        store.saveEntity();
        tick();

        expect(store.state.entity).toEqual(mockedAccountWithExtras.account);
        expect(store.state.sources).toEqual(mockedSources);
        expect(store.state.fieldsErrors).toEqual(
            jasmine.objectContaining({
                ...new AccountSettingsStoreFieldsErrorsState(),
                name: ['Please specify account name.'],
            })
        );
        expect(accountServiceStub.save).toHaveBeenCalledTimes(1);
        expect(sourcesServiceStub.list).toHaveBeenCalledTimes(1);
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

        sourcesServiceStub.list.and
            .returnValue(of(mockedSources, asapScheduler))
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

        store.patchState('Generic name', 'entity', 'name');
        expect(store.state.entity.name).toEqual('Generic name');
        store.setName('Generic name 2');
        expect(store.state.entity.name).toEqual('Generic name 2');
    });

    it('should correctly change account manager', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.patchState('22', 'entity', 'defaultAccountManager');
        expect(store.state.entity.defaultAccountManager).toEqual('22');
        store.setAccountManager('11');
        expect(store.state.entity.defaultAccountManager).toEqual('11');
    });

    it('should correctly change sales representative', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.patchState('22', 'entity', 'defaultSalesRepresentative');
        expect(store.state.entity.defaultSalesRepresentative).toEqual('22');
        store.setSalesRepresentative('11');
        expect(store.state.entity.defaultSalesRepresentative).toEqual('11');
    });

    it('should correctly change cs representative', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.patchState('22', 'entity', 'defaultCsRepresentative');
        expect(store.state.entity.defaultCsRepresentative).toEqual('22');
        store.setCustomerSuccessRepresentative('11');
        expect(store.state.entity.defaultCsRepresentative).toEqual('11');
    });

    it('should correctly change ob sales representative', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.patchState('22', 'entity', 'obSalesRepresentative');
        expect(store.state.entity.obSalesRepresentative).toEqual('22');
        store.setOutbrainSalesRepresentative('11');
        expect(store.state.entity.obSalesRepresentative).toEqual('11');
    });

    it('should correctly change ob account manager', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.patchState('22', 'entity', 'obAccountManager');
        expect(store.state.entity.obAccountManager).toEqual('22');
        store.setOutbrainAccountManager('11');
        expect(store.state.entity.obAccountManager).toEqual('11');
    });

    it('should correctly change account type', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.patchState(AccountType.UNKNOWN, 'entity', 'accountType');
        expect(store.state.entity.accountType).toEqual(AccountType.UNKNOWN);
        store.setAccountType(AccountType.PILOT);
        expect(store.state.entity.accountType).toEqual(AccountType.PILOT);
    });

    it('should correctly change agency id', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.patchState('22', 'entity', 'agencyId');
        expect(store.state.entity.agencyId).toEqual('22');
        store.setAgency('11');
        expect(store.state.entity.agencyId).toEqual('11');
    });

    it('should correctly change salesforce url', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.patchState('http://salesforce.com', 'entity', 'salesforceUrl');
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

        store.patchState(Currency.USD, 'entity', 'currency');
        expect(store.state.entity.currency).toEqual(Currency.USD);
        store.setCurrency(Currency.EUR);
        expect(store.state.entity.currency).toEqual(Currency.EUR);
    });

    it('should correctly change frequency capping', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.patchState(22, 'entity', 'frequencyCapping');
        expect(store.state.entity.frequencyCapping).toEqual(22);
        store.setFrequencyCapping('30');
        expect(store.state.entity.frequencyCapping).toEqual(30);
    });

    it('should correctly change base64 encoded default icon', done => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.patchState('icon', 'entity', 'defaultIconBase64');
        expect(store.state.entity.defaultIconBase64).toEqual('icon');

        const blob = new Blob(['abcd'], {type: 'text/html'});

        store.setDefaultIcon([<File>blob]).then(result => {
            expect(store.state.entity.defaultIconBase64).toEqual(
                'data:text/html;base64,YWJjZA=='
            );
            done();
        });
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

        store.patchState(false, 'entity', 'autoAddNewSources');
        expect(store.state.entity.autoAddNewSources).toEqual(false);
        store.setAutoAddNewSources(true);
        expect(store.state.entity.autoAddNewSources).toEqual(true);
    });

    it('should correctly add to allowed media sources', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        const mockedAvailableMediaSources: AccountMediaSource[] = [
            {
                id: '1',
                name: 'Source 1',
                released: true,
                deprecated: false,
            },
            {
                id: '2',
                name: 'Source 2',
                released: true,
                deprecated: false,
            },
        ];
        const mockedAllowedMediaSources: AccountMediaSource[] = [];

        store.patchState(
            mockedAvailableMediaSources,
            'extras',
            'availableMediaSources'
        );
        store.patchState(
            mockedAllowedMediaSources,
            'entity',
            'allowedMediaSources'
        );
        expect(store.state.extras.availableMediaSources).toEqual(
            mockedAvailableMediaSources
        );
        expect(store.state.entity.allowedMediaSources).toEqual(
            mockedAllowedMediaSources
        );
        store.addToAllowedMediaSources(['1', '2']);
        expect(store.state.entity.allowedMediaSources).toEqual(
            mockedAvailableMediaSources
        );
    });

    it('should correctly remove from allowed media sources', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        const mockedAvailableMediaSources: AccountMediaSource[] = [
            {
                id: '1',
                name: 'Source 1',
                released: true,
                deprecated: false,
            },
            {
                id: '2',
                name: 'Source 2',
                released: true,
                deprecated: false,
            },
        ];
        const mockedAllowedMediaSources: AccountMediaSource[] = [
            {
                id: '1',
                name: 'Source 1',
                released: true,
                deprecated: false,
            },
            {
                id: '2',
                name: 'Source 2',
                released: true,
                deprecated: false,
            },
        ];

        store.patchState(
            mockedAvailableMediaSources,
            'extras',
            'availableMediaSources'
        );
        store.patchState(
            mockedAllowedMediaSources,
            'entity',
            'allowedMediaSources'
        );
        expect(store.state.extras.availableMediaSources).toEqual(
            mockedAvailableMediaSources
        );
        expect(store.state.entity.allowedMediaSources).toEqual(
            mockedAllowedMediaSources
        );
        store.removeFromAllowedMediaSources(['1', '2']);
        expect(store.state.entity.allowedMediaSources).toEqual([]);
    });

    it('should correctly load available deals via deals service', fakeAsync(() => {
        const mockedKeyword = 'bla';
        const mockedAvailableDeals: Deal[] = [];

        dealsServiceStub.list.and
            .returnValue(of(mockedAvailableDeals, asapScheduler))
            .calls.reset();

        store.loadAvailableDeals(mockedKeyword);
        tick();

        expect(dealsServiceStub.list).toHaveBeenCalledTimes(1);
        expect(store.state.availableDeals).toEqual(mockedAvailableDeals);
    }));

    it('should correctly add deal', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        const mockedDeal = {
            id: '10000000',
            dealId: '45345',
            description: 'test directDeal',
            name: 'test directDeal',
            source: 'urska',
            floorPrice: '0.0002',
            createdDt: new Date(),
            modifiedDt: new Date(),
            createdBy: 'test@test.com',
            numOfAccounts: 0,
            numOfCampaigns: 0,
            numOfAdgroups: 0,
        };
        store.addDeal(mockedDeal);

        expect(store.state.entity.deals).toEqual([mockedDeal]);
    });

    it('should correctly remove deal', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.state.entity.deals = [
            {
                id: '10000000',
                dealId: '45345',
                description: 'test directDeal',
                name: 'test directDeal',
                source: 'urska',
                floorPrice: '0.0002',
                createdDt: new Date(),
                modifiedDt: new Date(),
                createdBy: 'test@test.com',
                numOfAccounts: 0,
                numOfCampaigns: 0,
                numOfAdgroups: 0,
            },
        ];

        store.removeDeal(store.state.entity.deals[0]);
        expect(store.state.entity.deals).toEqual([]);
    });
});
