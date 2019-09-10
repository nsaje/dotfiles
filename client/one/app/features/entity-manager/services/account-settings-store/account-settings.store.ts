import {Injectable, OnDestroy} from '@angular/core';
import {Store} from 'rxjs-observable-store';
import {AccountSettingsStoreState} from './account-settings.store.state';
import {Subject} from 'rxjs';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import {Account} from '../../../../core/entities/types/account/account';
import {AccountService} from '../../../../core/entities/services/account/account.service';
import * as storeHelpers from '../../../../shared/helpers/store.helpers';
import {takeUntil} from 'rxjs/operators';
import * as clone from 'clone';
import {AccountSettingsStoreFieldsErrorsState} from './account-settings.store.fields-errors-state';
import {HttpErrorResponse} from '@angular/common/http';
import * as deepEqual from 'fast-deep-equal';
import {IncludedExcluded} from '../../../../core/entities/types/common/included-excluded';
import {AccountType, Currency} from '../../../../app.constants';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {AccountMediaSource} from '../../../../core/entities/types/account/account-media-source';

@Injectable()
export class AccountSettingsStore extends Store<AccountSettingsStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();
    private requestStateUpdater: RequestStateUpdater;
    private originalEntity: Account;

    constructor(private accountService: AccountService) {
        super(new AccountSettingsStoreState());
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
    }

    loadEntityDefaults() {
        this.accountService
            .defaults(this.requestStateUpdater)
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(
                accountWithExtras => {
                    this.setState({
                        ...this.state,
                        entity: accountWithExtras.account,
                        extras: accountWithExtras.extras,
                    });
                },
                error => {}
            );
    }

    loadEntity(id: string) {
        this.accountService
            .get(id, this.requestStateUpdater)
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(
                accountWithExtras => {
                    this.originalEntity = clone(accountWithExtras.account);
                    this.setState({
                        ...this.state,
                        entity: accountWithExtras.account,
                        extras: accountWithExtras.extras,
                    });
                },
                error => {}
            );
    }

    validateEntity() {
        this.accountService
            .validate(this.state.entity, this.requestStateUpdater)
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(
                () => {
                    this.patchState(
                        new AccountSettingsStoreFieldsErrorsState(),
                        'fieldsErrors'
                    );
                },
                (error: HttpErrorResponse) => {
                    const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                        new AccountSettingsStoreFieldsErrorsState(),
                        error
                    );
                    this.patchState(fieldsErrors, 'fieldsErrors');
                }
            );
    }

    saveEntity(): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            this.accountService
                .save(this.state.entity, this.requestStateUpdater)
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (account: Account) => {
                        this.setState({
                            ...this.state,
                            entity: account,
                            fieldsErrors: new AccountSettingsStoreFieldsErrorsState(),
                        });
                        resolve(true);
                    },
                    (error: HttpErrorResponse) => {
                        const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                            new AccountSettingsStoreFieldsErrorsState(),
                            error
                        );
                        this.patchState(fieldsErrors, 'fieldsErrors');
                        resolve(false);
                    }
                );
        });
    }

    archiveEntity(): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            this.accountService
                .archive(this.state.entity.id, this.requestStateUpdater)
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        resolve(true);
                    },
                    (error: HttpErrorResponse) => {
                        const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                            new AccountSettingsStoreFieldsErrorsState(),
                            error
                        );
                        this.patchState(fieldsErrors, 'fieldsErrors');
                        resolve(false);
                    }
                );
        });
    }

    doEntitySettingsHaveUnsavedChanges(): boolean {
        if (!this.originalEntity) {
            return false;
        }
        return !deepEqual(this.originalEntity, this.state.entity);
    }

    setName(name: string) {
        this.patchState(name, 'entity', 'name');
        this.validateEntity();
    }

    setAccountManager(accountManager: string) {
        this.patchState(accountManager, 'entity', 'defaultAccountManager');
        this.validateEntity();
    }

    setSalesRepresentative(salesRepresentative: string) {
        this.patchState(
            salesRepresentative,
            'entity',
            'defaultSalesRepresentative'
        );
        this.validateEntity();
    }

    setCustomerSuccessRepresentative(csRepresentative: string) {
        this.patchState(csRepresentative, 'entity', 'defaultCsRepresentative');
        this.validateEntity();
    }

    setOutbrainRepresentative(obRepresentative: string) {
        this.patchState(obRepresentative, 'entity', 'obRepresentative');
        this.validateEntity();
    }

    setAccountType(accountType: AccountType) {
        this.patchState(accountType, 'entity', 'accountType');
        this.validateEntity();
    }

    setAgency(agencyId: string) {
        this.patchState(agencyId, 'entity', 'agencyId');
        this.validateEntity();
    }

    setSalesforceUrl(salesforceUrl: string) {
        this.patchState(salesforceUrl, 'entity', 'salesforceUrl');
        this.validateEntity();
    }

    setCurrency(currency: Currency) {
        this.patchState(currency, 'entity', 'currency');
        this.validateEntity();
    }

    setFrequencyCapping(frequencyCapping: string) {
        let frequencyCappingNumber = null;
        if (commonHelpers.isNotEmpty(frequencyCapping)) {
            frequencyCappingNumber = parseInt(frequencyCapping, 10) || null;
        }
        this.patchState(frequencyCappingNumber, 'entity', 'frequencyCapping');
        this.validateEntity();
    }

    setPublisherGroupsTargeting(publisherGroupsTargeting: {
        whitelistedPublisherGroups?: number[];
        blacklistedPublisherGroups?: number[];
    }) {
        const newPublisherGroupsTargeting: IncludedExcluded<number[]> = {
            included: publisherGroupsTargeting.whitelistedPublisherGroups
                ? publisherGroupsTargeting.whitelistedPublisherGroups
                : this.state.entity.targeting.publisherGroups.included,
            excluded: publisherGroupsTargeting.blacklistedPublisherGroups
                ? publisherGroupsTargeting.blacklistedPublisherGroups
                : this.state.entity.targeting.publisherGroups.excluded,
        };

        this.patchState(
            newPublisherGroupsTargeting,
            'entity',
            'targeting',
            'publisherGroups'
        );
        this.validateEntity();
    }

    setAutoAddNewSources(autoAddNewSources: boolean) {
        this.patchState(autoAddNewSources, 'entity', 'autoAddNewSources');
        this.validateEntity();
    }

    addToAllowedMediaSources(mediaSourcesIds: string[]) {
        const mediaSources = this.state.entity.mediaSources.map(item => {
            if (mediaSourcesIds.indexOf(item.id) !== -1) {
                return {
                    ...item,
                    allowed: true,
                };
            }
            return item;
        });

        this.patchState(mediaSources, 'entity', 'mediaSources');
        this.validateEntity();
    }

    removeFromAllowedMediaSources(mediaSourcesIds: string[]) {
        const mediaSources = this.state.entity.mediaSources.map(item => {
            if (mediaSourcesIds.indexOf(item.id) !== -1) {
                return {
                    ...item,
                    allowed: false,
                };
            }
            return item;
        });

        this.patchState(mediaSources, 'entity', 'mediaSources');
        this.validateEntity();
    }

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }
}
