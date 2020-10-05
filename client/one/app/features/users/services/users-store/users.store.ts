import {Injectable, OnDestroy} from '@angular/core';
import {HttpErrorResponse} from '@angular/common/http';
import {Subject} from 'rxjs';
import {Store} from 'rxjs-observable-store';
import {takeUntil} from 'rxjs/operators';
import {ChangeEvent} from '../../../../shared/types/change-event';
import {User} from '../../../../core/users/types/user';
import {UsersStoreState} from './users.store.state';
import {UsersStoreFieldsErrorsState} from './users.store.fields-errors-state';
import {UsersService} from '../../../../core/users/services/users.service';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import * as storeHelpers from '../../../../shared/helpers/store.helpers';
import {AccountService} from '../../../../core/entities/services/account/account.service';
import {Account} from '../../../../core/entities/types/account/account';
import {ScopeSelectorState} from '../../../../shared/components/scope-selector/scope-selector.constants';
import {isDefined, isNotEmpty} from '../../../../shared/helpers/common.helpers';
import {EntityPermission} from '../../../../core/users/types/entity-permission';
import {
    arraysContainSameElements,
    arrayToObject,
    distinct,
    groupArray,
    isEmpty,
} from '../../../../shared/helpers/array.helpers';
import {EntityPermissionSelection} from '../../components/entity-permission-selector/types/entity-permission-selection';
import {AuthStore} from '../../../../core/auth/services/auth.store';
import {
    CONFIGURABLE_PERMISSIONS,
    GENERAL_PERMISSIONS,
    REPORTING_PERMISSIONS,
} from '../../users.config';
import {EntityPermissionCheckboxStates} from '../../components/entity-permission-selector/types/entity-permission-checkbox-states';
import {EntityPermissionValue} from '../../../../core/users/users.constants';
import {
    getHighestLevelEntityPermissions,
    isAccountManager,
    isAgencyManager,
    isInternalUser,
} from '../../helpers/users.helpers';

@Injectable()
export class UsersStore extends Store<UsersStoreState> implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();
    private requestStateUpdater: RequestStateUpdater;
    private accountsRequestStateUpdater: RequestStateUpdater;

    constructor(
        private usersService: UsersService,
        private accountsService: AccountService,
        private authStore: AuthStore
    ) {
        super(new UsersStoreState());
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
        this.accountsRequestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this,
            'accountsRequests'
        );
    }

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    setStore(
        agencyId: string | null,
        accountId: string | null,
        page: number,
        pageSize: number,
        keyword: string | null,
        showInternal: boolean | null
    ): Promise<boolean> {
        const canEditUsers: boolean = this.authStore.hasPermissionOn(
            agencyId,
            accountId,
            EntityPermissionValue.USER
        );
        if (canEditUsers) {
            return new Promise<boolean>(resolve => {
                Promise.all([
                    this.loadUsers(
                        agencyId,
                        accountId,
                        page,
                        pageSize,
                        keyword,
                        showInternal
                    ),
                    this.loadAccounts(agencyId),
                ])
                    .then((values: [User[], Account[]]) => {
                        this.setState({
                            ...this.state,
                            agencyId: agencyId,
                            accountId: accountId,
                            hasAgencyScope: this.authStore.hasPermissionOn(
                                agencyId,
                                null,
                                EntityPermissionValue.USER
                            ),
                            hasAllAccountsScope: this.authStore.hasPermissionOn(
                                null,
                                null,
                                EntityPermissionValue.USER
                            ),
                            canEditUsers,
                            currentUserId: this.authStore.getCurrentUserId(),
                            entities: values[0],
                            accounts: values[1],
                        });
                        resolve(true);
                    })
                    .catch(() => resolve(false));
            });
        } else {
            this.setState({...new UsersStoreState(), canEditUsers});
            return new Promise<boolean>(resolve => {
                resolve(false);
            });
        }
    }

    loadEntities(
        page: number,
        pageSize: number,
        keyword: string | null,
        showInternal: boolean | null
    ): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.loadUsers(
                this.state.agencyId,
                this.state.accountId,
                page,
                pageSize,
                keyword,
                showInternal
            ).then(
                (users: User[]) => {
                    this.patchState(users, 'entities');
                    resolve();
                },
                () => {
                    reject();
                }
            );
        });
    }

    saveActiveEntity(): Promise<void> {
        if (isDefined(this.state.activeEntity.entity.id)) {
            return this.editActiveEntity();
        } else {
            return this.createActiveEntity();
        }
    }

    validateActiveEntity(): void {
        const entity = storeHelpers.getNewStateWithoutNull(
            this.state.activeEntity.entity
        );
        this.usersService
            .validate(
                !isDefined(entity.id) && isDefined(entity.email)
                    ? this.splitUsersByEmail(entity)
                    : entity,
                this.state.agencyId,
                this.state.accountId,
                this.requestStateUpdater
            )
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(
                () => {
                    this.patchState(
                        new UsersStoreFieldsErrorsState(),
                        'activeEntity',
                        'fieldsErrors'
                    );
                },
                (error: HttpErrorResponse) => {
                    const fieldsErrors = arrayToObject(
                        storeHelpers.getStoreFieldsErrorsState(
                            new UsersStoreFieldsErrorsState(),
                            error
                        )
                    );
                    this.patchState(
                        fieldsErrors,
                        'activeEntity',
                        'fieldsErrors'
                    );
                }
            );
    }

    deleteEntity(userId: string): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.usersService
                .remove(
                    userId,
                    this.state.agencyId,
                    this.state.accountId,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        resolve();
                    },
                    error => {
                        reject();
                    }
                );
        });
    }

    resendEmail(userId: string): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.usersService
                .resendEmail(
                    userId,
                    this.state.agencyId,
                    this.state.accountId,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        resolve();
                    },
                    error => {
                        reject();
                    }
                );
        });
    }

    setActiveEntity(entity: Partial<User>): void {
        const userPatches: Partial<User> = {
            ...entity,
        };

        if (!isDefined(entity.id) && isEmpty(entity.entityPermissions)) {
            userPatches.entityPermissions = this.getDefaultEntityPermissions();
        } else {
            userPatches.entityPermissions = getHighestLevelEntityPermissions(
                entity
            );
        }

        this.recalculateActiveEntityState(userPatches, undefined, true);
    }

    addActiveEntityAccount(account: Account) {
        if (!isDefined(account)) {
            return;
        }
        if (
            this.state.activeEntity.entity.entityPermissions.some(
                ep => isDefined(ep.accountId) && ep.accountId === account.id
            )
        ) {
            return; // Account has already been added
        }

        let newEntityPermissions: EntityPermission[];

        if (isNotEmpty(this.state.activeEntity.selectedAccounts)) {
            // If any accounts are selected, copy currently selected permissions to the new account
            // But do not copy the ones, for which the current app user hasn't got permission
            const currentlySelectedPermissions: EntityPermissionSelection = this.calculateSelectedEntityPermissions(
                this.state.activeEntity.entity,
                this.state.activeEntity.selectedAccounts
            );

            newEntityPermissions = Object.keys(currentlySelectedPermissions)
                .map(permission => <EntityPermissionValue>permission)
                .filter(
                    permission =>
                        currentlySelectedPermissions[permission] &&
                        this.currentUserHasPermissionInScope(
                            permission,
                            ScopeSelectorState.ACCOUNT_SCOPE,
                            [account]
                        )
                )
                .map(permission => ({
                    accountId: account.id,
                    permission,
                }));
        } else {
            // Otherwise just add a read permission
            newEntityPermissions = [
                {
                    accountId: account.id,
                    permission: EntityPermissionValue.READ,
                },
            ];
        }

        const entityPermissions: EntityPermission[] = this.state.activeEntity.entity.entityPermissions.concat(
            newEntityPermissions
        );

        this.recalculateActiveEntityState(
            {entityPermissions},
            this.state.activeEntity.selectedAccounts.concat(account)
        );
        this.validateActiveEntity();
    }

    removeActiveEntityAccounts(accounts: Account[]) {
        const accountIds: string[] = accounts.map(account => account.id);
        const entityPermissions: EntityPermission[] = this.state.activeEntity.entity.entityPermissions.filter(
            ep => !accountIds.includes(ep.accountId)
        );

        this.recalculateActiveEntityState({entityPermissions});
        this.validateActiveEntity();
    }

    setActiveEntityScope(scopeState: ScopeSelectorState) {
        if (this.state.activeEntity.scopeState === scopeState) {
            return;
        }
        if (
            scopeState === ScopeSelectorState.AGENCY_SCOPE &&
            !this.state.hasAgencyScope
        ) {
            return;
        }
        if (
            scopeState === ScopeSelectorState.ALL_ACCOUNTS_SCOPE &&
            !this.state.hasAllAccountsScope
        ) {
            return;
        }
        const entityPermissions: EntityPermission[] = [];
        if (scopeState === ScopeSelectorState.AGENCY_SCOPE) {
            entityPermissions.push({
                agencyId: this.state.agencyId,
                permission: EntityPermissionValue.READ,
            });
        } else if (scopeState === ScopeSelectorState.ALL_ACCOUNTS_SCOPE) {
            entityPermissions.push({
                permission: EntityPermissionValue.READ,
            });
        }

        this.recalculateActiveEntityState({entityPermissions});
        this.validateActiveEntity();
    }

    changeActiveEntity(event: ChangeEvent<User>): void {
        this.recalculateActiveEntityState(event.changes);
        this.validateActiveEntity();
    }

    setSelectedAccounts(selectedAccounts: Account[]) {
        this.recalculateActiveEntityState({}, selectedAccounts);
    }

    updateSelectedEntityPermissions(
        selectedPermissions: EntityPermissionSelection
    ) {
        if (this.haveDisabledOrHiddenCheckboxesChanged(selectedPermissions)) {
            // This should never be thrown during normal UI operations, but is relevant if anybody ever calls the store directly
            throw new Error('Disabled or hidden checkbox cannot be changed!');
        }

        const readonlyPermissionScopes: {
            accountId: string | null;
            agencyId: string | null;
        }[] = this.getReadonlyPermissionScopes(
            this.state.activeEntity.entity.entityPermissions
        );

        let newEntityPermissions: EntityPermission[];
        if (
            this.state.activeEntity.scopeState ===
            ScopeSelectorState.ALL_ACCOUNTS_SCOPE
        ) {
            newEntityPermissions = Object.keys(selectedPermissions)
                .filter(permission => selectedPermissions[permission])
                .map(permission => ({
                    permission: <EntityPermissionValue>permission,
                }));
        } else if (
            this.state.activeEntity.scopeState ===
            ScopeSelectorState.AGENCY_SCOPE
        ) {
            const agencyId: string = this.state.agencyId;
            newEntityPermissions = Object.keys(selectedPermissions)
                .filter(permission => selectedPermissions[permission])
                .map(permission => ({
                    agencyId,
                    permission: <EntityPermissionValue>permission,
                }));
        } else {
            if (isEmpty(this.state.activeEntity.selectedAccounts)) {
                return;
            }

            const selectedAccountIds: string[] = this.state.activeEntity.selectedAccounts.map(
                account => account.id
            );

            // Preserve all permissions on accounts that are not selected in the current view
            const permissionsOnDeselectedAccounts: EntityPermission[] = this.state.activeEntity.entity.entityPermissions.filter(
                ep => !selectedAccountIds.includes(ep.accountId)
            );

            // Preserve all permissions on currently selected accounts that are marked with an indeterminate (undefined) checkbox
            const unchangedPermissionsOnSelectedAccounts: EntityPermission[] = this.state.activeEntity.entity.entityPermissions.filter(
                ep =>
                    selectedAccountIds.includes(ep.accountId) &&
                    selectedPermissions[ep.permission] === undefined
            );

            // Override all permissions on currently selected accounts that are marked with a checked (add them) or unchecked (do not add them) checkbox
            const changedPermissionsOnSelectedAccounts: EntityPermission[] = [];
            selectedAccountIds.forEach(accountId => {
                changedPermissionsOnSelectedAccounts.push(
                    ...Object.keys(selectedPermissions)
                        .filter(permission => selectedPermissions[permission])
                        .map(permission => ({
                            accountId,
                            permission: <EntityPermissionValue>permission,
                        }))
                );
            });

            newEntityPermissions = [
                ...permissionsOnDeselectedAccounts,
                ...unchangedPermissionsOnSelectedAccounts,
                ...changedPermissionsOnSelectedAccounts,
            ];
        }

        // Restore the readonly setting on reporting permissions on entities that had this setting before.
        newEntityPermissions.forEach(ep => {
            if (
                REPORTING_PERMISSIONS.includes(ep.permission) &&
                readonlyPermissionScopes.some(
                    s =>
                        s.accountId === (ep.accountId || null) &&
                        s.agencyId === (ep.agencyId || null)
                )
            ) {
                ep.readonly = true;
            }
        });

        this.recalculateActiveEntityState({
            entityPermissions: newEntityPermissions,
        });
    }

    isUserReadOnly(user: User): boolean {
        if (isInternalUser(user)) {
            return !this.state.hasAllAccountsScope;
        } else if (isAgencyManager(user)) {
            return (
                !this.state.hasAllAccountsScope && !this.state.hasAgencyScope
            );
        } else {
            return false;
        }
    }

    isCurrentUser(user: User): boolean {
        return user.id === this.state.currentUserId;
    }

    private editActiveEntity(): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.usersService
                .edit(
                    this.state.activeEntity.entity,
                    this.state.agencyId,
                    this.state.accountId,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        this.patchState(
                            new UsersStoreState().activeEntity.entity,
                            'activeEntity',
                            'entity'
                        );
                        resolve();
                    },
                    (error: HttpErrorResponse) => {
                        const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                            new UsersStoreFieldsErrorsState(),
                            error
                        );
                        this.patchState(
                            fieldsErrors,
                            'activeEntity',
                            'fieldsErrors'
                        );
                        reject();
                    }
                );
        });
    }

    private createActiveEntity(): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.usersService
                .create(
                    this.splitUsersByEmail(
                        this.state.activeEntity.entity
                    ) as User[],
                    this.state.agencyId,
                    this.state.accountId,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        resolve();
                    },
                    (error: HttpErrorResponse) => {
                        const fieldsErrors = arrayToObject(
                            storeHelpers.getStoreFieldsErrorsState(
                                new UsersStoreFieldsErrorsState(),
                                error
                            )
                        );
                        this.patchState(
                            fieldsErrors,
                            'activeEntity',
                            'fieldsErrors'
                        );
                        reject();
                    }
                );
        });
    }

    private splitUsersByEmail(
        user: User | Partial<User>
    ): User[] | Partial<User>[] {
        const splitEmails: string[] = user.email.split(',').map(x => x.trim());
        return splitEmails.map(email => ({
            ...user,
            email,
        }));
    }

    private loadUsers(
        agencyId: string | null,
        accountId: string | null,
        page: number,
        pageSize: number,
        keyword: string | null = null,
        showInternal: boolean | null = null
    ): Promise<User[]> {
        return new Promise<User[]>((resolve, reject) => {
            const offset = this.getOffset(page, pageSize);
            this.usersService
                .list(
                    agencyId,
                    accountId,
                    offset,
                    pageSize,
                    keyword,
                    showInternal,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (users: User[]) => {
                        resolve(users);
                    },
                    error => {
                        reject();
                    }
                );
        });
    }

    private loadAccounts(agencyId: string): Promise<Account[]> {
        return new Promise<Account[]>((resolve, reject) => {
            const offset = 0;
            const limit = 500;
            this.accountsService
                .list(
                    agencyId,
                    offset,
                    limit,
                    null,
                    true,
                    this.accountsRequestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    accounts => {
                        resolve(accounts);
                    },
                    () => {
                        reject();
                    }
                );
        });
    }

    private getOffset(page: number, pageSize: number): number {
        return (page - 1) * pageSize;
    }

    private getDefaultEntityPermissions(): EntityPermission[] {
        if (this.state.accountId !== null) {
            return [
                {
                    accountId: this.state.accountId,
                    permission: EntityPermissionValue.READ,
                },
            ];
        } else if (this.state.hasAgencyScope === true) {
            return [
                {
                    agencyId: this.state.agencyId,
                    permission: EntityPermissionValue.READ,
                },
            ];
        } else {
            return [];
        }
    }

    private recalculateActiveEntityState(
        userPatches: Partial<User>,
        proposedSelectedAccounts?: Account[],
        initialize: boolean = false
    ) {
        let activeEntity: UsersStoreState['activeEntity'] = initialize
            ? new UsersStoreState().activeEntity
            : this.state.activeEntity;

        const patchedUser: User = {
            ...activeEntity.entity,
            ...userPatches,
        };

        const scopeState: ScopeSelectorState = this.calculateScopeState(
            patchedUser
        );

        activeEntity = {
            ...activeEntity,
            entity: patchedUser,
            scopeState,
        };

        if (Object.keys(userPatches).includes('entityPermissions')) {
            activeEntity = {
                ...activeEntity,
                entityAccounts: this.calculateEntityAccounts(patchedUser),
                isReadOnly: this.isUserReadOnly(patchedUser),
                isCurrentUser: this.isCurrentUser(patchedUser),
            };
        }

        if (
            Object.keys(userPatches).includes('entityPermissions') ||
            isDefined(proposedSelectedAccounts) ||
            initialize
        ) {
            const selectedAccounts: Account[] = this.calculateSelectedAccounts(
                activeEntity,
                proposedSelectedAccounts,
                initialize
            );

            // Gets the list of reporting permissions, whose state is unknown because they are visible on some selected accounts, but not on others
            const unknownReportingPermissions: EntityPermissionValue[] = this.getUnknownReportingPermissions(
                scopeState,
                selectedAccounts
            );

            // Gets the list of reporting permissions which are disabled because the edited user has some higher reporting permissions that the current user can't see
            const disabledReportingPermissions: EntityPermissionValue[] = this.getDisabledReportingPermissions(
                patchedUser,
                scopeState,
                selectedAccounts,
                unknownReportingPermissions
            );

            const selectedEntityPermissions: EntityPermissionSelection = this.calculateSelectedEntityPermissions(
                patchedUser,
                selectedAccounts,
                unknownReportingPermissions
            );

            const checkboxStates: EntityPermissionCheckboxStates = this.calculateCheckboxStates(
                scopeState,
                selectedAccounts,
                disabledReportingPermissions,
                unknownReportingPermissions
            );

            activeEntity = {
                ...activeEntity,
                selectedAccounts,
                selectedEntityPermissions,
                checkboxStates,
            };
        }

        this.patchState(activeEntity, 'activeEntity');
    }

    private getDisabledReportingPermissions(
        patchedUser: User,
        scopeState: ScopeSelectorState,
        selectedAccounts: Account[],
        unknownReportingPermissions: EntityPermissionValue[]
    ): EntityPermissionValue[] {
        if (!isEmpty(unknownReportingPermissions)) {
            // If any reporting permissions are unknown, ALL reporting permissions should be disabled
            return <EntityPermissionValue[]>(
                REPORTING_PERMISSIONS.filter(
                    permission => permission !== 'total_spend'
                )
            );
        }

        const entityPermissions: EntityPermission[] =
            patchedUser.entityPermissions || [];
        const selectedAccountIds: string[] = selectedAccounts.map(
            account => account.id
        );
        return distinct(
            entityPermissions
                .filter(
                    ep =>
                        ep.readonly &&
                        REPORTING_PERMISSIONS.includes(ep.permission) &&
                        (scopeState !== ScopeSelectorState.ACCOUNT_SCOPE ||
                            selectedAccountIds.includes(ep.accountId))
                )
                .map(ep => ep.permission)
        );
    }

    private getUnknownReportingPermissions(
        scopeState: ScopeSelectorState,
        selectedAccounts: Account[]
    ): EntityPermissionValue[] {
        if (scopeState !== ScopeSelectorState.ACCOUNT_SCOPE) {
            return [];
        }

        const selectedAccountIds: string[] = selectedAccounts.map(
            account => account.id
        );
        return REPORTING_PERMISSIONS.filter(
            permission =>
                permission !== 'total_spend' &&
                selectedAccountIds.some(
                    accountId =>
                        !this.authStore.hasPermissionOn(
                            this.state.agencyId,
                            accountId,
                            permission
                        )
                ) &&
                selectedAccountIds.some(accountId =>
                    this.authStore.hasPermissionOn(
                        this.state.agencyId,
                        accountId,
                        permission
                    )
                )
        ).map(permission => <EntityPermissionValue>permission);
    }

    private calculateScopeState(user: User): ScopeSelectorState {
        if (isInternalUser(user)) {
            return ScopeSelectorState.ALL_ACCOUNTS_SCOPE;
        } else if (isAgencyManager(user)) {
            return ScopeSelectorState.AGENCY_SCOPE;
        } else {
            return ScopeSelectorState.ACCOUNT_SCOPE;
        }
    }

    private calculateEntityAccounts(user: User): Account[] {
        const accountIds: string[] = distinct(
            user.entityPermissions
                .filter(ep => isDefined(ep.accountId))
                .map(ep => ep.accountId)
        );
        return accountIds
            .map(id => this.state.accounts.find(account => account.id === id))
            .filter(account => isDefined(account))
            .sort((a, b) => parseInt(a.id, 10) - parseInt(b.id, 10));
    }

    private calculateSelectedAccounts(
        activeEntity: UsersStoreState['activeEntity'],
        proposedSelectedAccounts: Account[],
        initialize: boolean
    ): Account[] {
        if (activeEntity.scopeState !== ScopeSelectorState.ACCOUNT_SCOPE) {
            return [];
        }

        let selectedAccounts: Account[] = [];
        if (!initialize) {
            if (isDefined(proposedSelectedAccounts)) {
                selectedAccounts = proposedSelectedAccounts;
            } else {
                selectedAccounts = activeEntity.selectedAccounts;
            }

            selectedAccounts = selectedAccounts.filter(account =>
                activeEntity.entityAccounts.includes(account)
            );
        }

        if (isEmpty(selectedAccounts)) {
            selectedAccounts = this.getDefaultSelectedAccounts(activeEntity);
        }

        return selectedAccounts;
    }

    private getDefaultSelectedAccounts(
        activeEntity: UsersStoreState['activeEntity']
    ): Account[] {
        if (
            activeEntity.scopeState !== ScopeSelectorState.ACCOUNT_SCOPE ||
            isEmpty(activeEntity.entityAccounts)
        ) {
            return [];
        } else if (
            this.userHasSamePermissionsOnAllAccounts(activeEntity.entity)
        ) {
            return [...activeEntity.entityAccounts];
        } else if (
            this.userHasPermissionsOnCurrentAccount(activeEntity.entity)
        ) {
            const currentAccount: Account = activeEntity.entityAccounts.find(
                account => account.id === this.state.accountId
            );
            return currentAccount
                ? [currentAccount]
                : [activeEntity.entityAccounts[0]];
        } else {
            return [activeEntity.entityAccounts[0]];
        }
    }

    private userHasPermissionsOnCurrentAccount(user: User): boolean {
        return (
            isDefined(this.state.accountId) &&
            user.entityPermissions.some(
                ep => ep.accountId === this.state.accountId
            )
        );
    }

    private userHasSamePermissionsOnAllAccounts(user: User): boolean {
        if (!isAccountManager(user)) {
            return false;
        }
        const permissionsByAccount: EntityPermission[][] = groupArray(
            user.entityPermissions,
            ep => ep.accountId
        );

        return permissionsByAccount
            .slice(1)
            .every(eps =>
                this.arePermissionsTheSame(permissionsByAccount[0], eps)
            );
    }

    private arePermissionsTheSame(
        epsA: EntityPermission[],
        epsB: EntityPermission[]
    ): boolean {
        const permissionValuesA: EntityPermissionValue[] = (epsA || []).map(
            ep => ep.permission
        );
        const permissionValuesB: EntityPermissionValue[] = (epsB || []).map(
            ep => ep.permission
        );

        return arraysContainSameElements(permissionValuesA, permissionValuesB);
    }

    private calculateSelectedEntityPermissions(
        user: User,
        selectedAccounts: Account[],
        unknownReportingPermissions: EntityPermissionValue[] = []
    ): EntityPermissionSelection {
        if (
            isEmpty(user.entityPermissions) ||
            (isAccountManager(user) && isEmpty(selectedAccounts))
        ) {
            return {};
        }

        const selectedPermissions: EntityPermissionSelection = {read: true};

        CONFIGURABLE_PERMISSIONS.forEach(permission => {
            selectedPermissions[permission] = this.isPermissionSelected(
                user,
                permission,
                selectedAccounts,
                unknownReportingPermissions
            );
        });

        return selectedPermissions;
    }

    private isPermissionSelected(
        user: User,
        permission: EntityPermissionValue,
        selectedAccounts: Account[],
        unknownReportingPermissions: EntityPermissionValue[]
    ): boolean {
        if (unknownReportingPermissions.includes(permission)) {
            return undefined;
        }

        const allPermissions: EntityPermission[] = user.entityPermissions || [];

        if (isInternalUser(user) || isAgencyManager(user)) {
            return allPermissions.some(ep => ep.permission === permission);
        } else {
            const selectedAccountIds: string[] = selectedAccounts.map(
                account => account.id
            );
            const permissionsOnSelectedAccounts: EntityPermission[] = allPermissions.filter(
                ep => selectedAccountIds.includes(ep.accountId)
            );
            const selectedAccountsCount: number = selectedAccountIds.length;
            const selectedAccountsWithThisPermissionCount: number = distinct(
                permissionsOnSelectedAccounts
                    .filter(ep => ep.permission === permission)
                    .map(ep => ep.accountId)
            ).length;

            if (selectedAccountsWithThisPermissionCount === 0) {
                return false;
            } else if (
                selectedAccountsWithThisPermissionCount < selectedAccountsCount
            ) {
                return undefined;
            } else {
                return true;
            }
        }
    }

    private calculateCheckboxStates(
        scopeState: ScopeSelectorState,
        selectedAccounts: Account[],
        disabledReportingPermissions: EntityPermissionValue[],
        unknownReportingPermissions: EntityPermissionValue[]
    ): EntityPermissionCheckboxStates {
        const checkboxStates: EntityPermissionCheckboxStates = {};

        GENERAL_PERMISSIONS.forEach(permission => {
            checkboxStates[permission] = this.currentUserHasPermissionInScope(
                permission,
                scopeState,
                selectedAccounts
            )
                ? 'enabled'
                : 'disabled';
        });

        REPORTING_PERMISSIONS.forEach(permission => {
            if (permission === 'total_spend') {
                checkboxStates[permission] = 'disabled';
            } else {
                const canUseCheckbox:
                    | boolean
                    | undefined = this.currentUserHasPermissionInScope(
                    permission,
                    scopeState,
                    selectedAccounts
                );

                if (canUseCheckbox === false) {
                    checkboxStates[permission] = 'hidden';
                } else if (
                    canUseCheckbox === undefined ||
                    unknownReportingPermissions.includes(permission) ||
                    disabledReportingPermissions.includes(permission)
                ) {
                    checkboxStates[permission] = 'disabled';
                } else {
                    checkboxStates[permission] = 'enabled';
                }
            }
        });
        return checkboxStates;
    }

    private currentUserHasPermissionInScope(
        permission: EntityPermissionValue,
        scopeState: ScopeSelectorState,
        selectedAccounts: Account[]
    ): boolean | undefined {
        if (scopeState === ScopeSelectorState.ALL_ACCOUNTS_SCOPE) {
            return this.authStore.hasPermissionOnAllEntities(permission);
        } else if (scopeState === ScopeSelectorState.AGENCY_SCOPE) {
            return this.authStore.hasPermissionOn(
                this.state.agencyId,
                null,
                permission
            );
        } else {
            const hasAccountPermissions: boolean[] = selectedAccounts.map(
                account =>
                    this.authStore.hasPermissionOn(
                        this.state.agencyId,
                        account.id,
                        permission
                    )
            );

            if (hasAccountPermissions.every(x => x)) {
                return true;
            } else if (hasAccountPermissions.some(x => x)) {
                return undefined;
            } else {
                return false;
            }
        }
    }

    private haveDisabledOrHiddenCheckboxesChanged(
        newSelection: EntityPermissionSelection
    ): boolean {
        const oldSelection: EntityPermissionSelection = this.state.activeEntity
            .selectedEntityPermissions;
        const checkboxStates: EntityPermissionCheckboxStates = this.state
            .activeEntity.checkboxStates;

        return Object.keys(checkboxStates).some(
            permission =>
                permission !== 'total_spend' &&
                checkboxStates[permission] !== 'enabled' &&
                newSelection[permission] !== oldSelection[permission]
        );
    }

    private getReadonlyPermissionScopes(
        entityPermissions: EntityPermission[]
    ): {accountId: string | null; agencyId: string | null}[] {
        return distinct(
            (entityPermissions || [])
                .filter(ep => ep.readonly)
                .map(ep => ({
                    accountId: ep.accountId || null,
                    agencyId: ep.agencyId || null,
                }))
        );
    }
}
