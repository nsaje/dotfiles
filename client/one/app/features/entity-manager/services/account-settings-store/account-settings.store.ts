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
                    this.updateState(
                        new AccountSettingsStoreFieldsErrorsState(),
                        'fieldsErrors'
                    );
                },
                (error: HttpErrorResponse) => {
                    const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                        new AccountSettingsStoreFieldsErrorsState(),
                        error
                    );
                    this.updateState(fieldsErrors, 'fieldsErrors');
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
                        this.updateState(fieldsErrors, 'fieldsErrors');
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
                        this.updateState(fieldsErrors, 'fieldsErrors');
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
        this.updateState(name, 'entity', 'name');
        this.validateEntity();
    }

    setAccountManager(accountManager: string) {
        this.updateState(accountManager, 'entity', 'defaultAccountManager');
        this.validateEntity();
    }

    setSalesRepresentative(salesRepresentative: string) {
        this.updateState(
            salesRepresentative,
            'entity',
            'defaultSalesRepresentative'
        );
        this.validateEntity();
    }

    setCustomerSuccessRepresentative(csRepresentative: string) {
        this.updateState(csRepresentative, 'entity', 'defaultCsRepresentative');
        this.validateEntity();
    }

    setOutbrainRepresentative(obRepresentative: string) {
        this.updateState(obRepresentative, 'entity', 'obRepresentative');
        this.validateEntity();
    }

    setAccountType(accountType: AccountType) {
        this.updateState(accountType, 'entity', 'accountType');
        this.validateEntity();
    }

    setAgency(agencyId: string) {
        this.updateState(agencyId, 'entity', 'agencyId');
        this.validateEntity();
    }

    setSalesforceUrl(salesforceUrl: string) {
        this.updateState(salesforceUrl, 'entity', 'salesforceUrl');
        this.validateEntity();
    }

    setCurrency(currency: Currency) {
        this.updateState(currency, 'entity', 'currency');
        this.validateEntity();
    }

    setFrequencyCapping(frequencyCapping: string) {
        let frequencyCappingNumber = null;
        if (commonHelpers.isNotEmpty(frequencyCapping)) {
            frequencyCappingNumber = parseInt(frequencyCapping, 10) || null;
        }
        this.updateState(frequencyCappingNumber, 'entity', 'frequencyCapping');
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

        this.updateState(
            newPublisherGroupsTargeting,
            'entity',
            'targeting',
            'publisherGroups'
        );
        this.validateEntity();
    }

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }
}
