import {Inject, Injectable, OnDestroy} from '@angular/core';
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
    distinct,
    intersect,
    isEmpty,
    groupArray,
} from '../../../../shared/helpers/array.helpers';
import {EntityPermissionSelection} from '../../components/entity-permission-selector/types/entity-permission-selection';
import {EntityPermissionValue} from '../../../../core/users/types/entity-permission-value';
import {CONFIGURABLE_PERMISSIONS} from '../../users.config';

@Injectable()
export class UsersStore extends Store<UsersStoreState> implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();
    private requestStateUpdater: RequestStateUpdater;
    private accountsRequestStateUpdater: RequestStateUpdater;

    constructor(
        private usersService: UsersService,
        private accountsService: AccountService,
        @Inject('zemPermissions') private zemPermissions: any
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
        const canEditUsers: boolean = this.zemPermissions.canEditUsersOnEntity(
            agencyId,
            accountId
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
                            hasAgencyScope: this.zemPermissions.canEditUsersOnAgency(
                                agencyId
                            ),
                            hasAllAccountsScope: this.zemPermissions.canEditUsersOnAllAccounts(),
                            canEditUsers,
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
        keyword: string | null = null,
        showInternal: boolean | null = null
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
                entity,
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
                    const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                        new UsersStoreFieldsErrorsState(),
                        error
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

    setActiveEntity(entity: Partial<User>): void {
        const userPatches: Partial<User> = {
            ...entity,
        };

        if (!isDefined(entity.id) && isEmpty(entity.entityPermissions)) {
            userPatches.entityPermissions = this.getDefaultEntityPermissions();
        }

        this.recalculateActiveEntityState(userPatches, undefined, true);
    }

    addActiveEntityAccount(account: Account) {
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
            const currentlySelectedPermissions: EntityPermissionSelection = this.calculateSelectedEntityPermissions(
                this.state.activeEntity.entity,
                this.state.activeEntity.selectedAccounts
            );
            newEntityPermissions = Object.keys(currentlySelectedPermissions)
                .filter(permission => currentlySelectedPermissions[permission])
                .map(permission => ({
                    accountId: account.id,
                    permission: <EntityPermissionValue>permission,
                }));
        } else {
            // Otherwise just add a read permission
            newEntityPermissions = [
                {
                    accountId: account.id,
                    permission: 'read',
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
                permission: 'read',
            });
        } else if (scopeState === ScopeSelectorState.ALL_ACCOUNTS_SCOPE) {
            entityPermissions.push({
                permission: 'read',
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

        this.recalculateActiveEntityState({
            entityPermissions: newEntityPermissions,
        });
    }

    isUserReadOnly(user: User): boolean {
        if (this.isInternalUser(user)) {
            return !this.state.hasAllAccountsScope;
        } else if (this.isAgencyManager(user)) {
            return (
                !this.state.hasAllAccountsScope && !this.state.hasAgencyScope
            );
        } else {
            return false;
        }
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
                    this.splitUsersByEmail(this.state.activeEntity.entity),
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

    private splitUsersByEmail(user: User): User[] {
        const splitEmails: string[] = user.email.split(',').map(x => x.trim());
        return splitEmails.map(email => ({
            ...user,
            email,
        }));
    }

    private isAccountManager(user: Partial<User>): boolean {
        return user.entityPermissions.some(ep => isNotEmpty(ep.accountId));
    }

    private isAgencyManager(user: Partial<User>): boolean {
        return user.entityPermissions.some(ep => isNotEmpty(ep.agencyId));
    }

    private isInternalUser(user: Partial<User>): boolean {
        return user.entityPermissions.some(
            ep => !isDefined(ep.agencyId) && !isDefined(ep.accountId)
        );
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
            this.accountsService
                .list(agencyId, this.accountsRequestStateUpdater)
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
            return [{accountId: this.state.accountId, permission: 'read'}];
        } else if (this.state.hasAgencyScope === true) {
            return [{agencyId: this.state.agencyId, permission: 'read'}];
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

        activeEntity = {
            ...activeEntity,
            entity: patchedUser,
        };

        if (Object.keys(userPatches).includes('entityPermissions')) {
            activeEntity = {
                ...activeEntity,
                scopeState: this.calculateScopeState(patchedUser),
                entityAccounts: this.calculateEntityAccounts(patchedUser),
                isReadOnly: this.isUserReadOnly(patchedUser),
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

            const selectedEntityPermissions: EntityPermissionSelection = this.calculateSelectedEntityPermissions(
                patchedUser,
                selectedAccounts
            );

            activeEntity = {
                ...activeEntity,
                selectedAccounts,
                selectedEntityPermissions,
            };
        }

        this.patchState(activeEntity, 'activeEntity');
    }

    private calculateScopeState(user: User): ScopeSelectorState {
        if (this.isInternalUser(user)) {
            return ScopeSelectorState.ALL_ACCOUNTS_SCOPE;
        } else if (this.isAgencyManager(user)) {
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
        if (!this.isAccountManager(user)) {
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
        selectedAccounts: Account[]
    ): EntityPermissionSelection {
        if (
            isEmpty(user.entityPermissions) ||
            (this.isAccountManager(user) && isEmpty(selectedAccounts))
        ) {
            return {};
        }

        const selectedPermissions: EntityPermissionSelection = {read: true};

        CONFIGURABLE_PERMISSIONS.forEach(permission => {
            selectedPermissions[permission] = this.isPermissionSelected(
                user,
                permission,
                selectedAccounts
            );
        });

        return selectedPermissions;
    }

    private isPermissionSelected(
        user: User,
        permission: EntityPermissionValue,
        selectedAccounts: Account[]
    ): boolean {
        const allPermissions: EntityPermission[] = user.entityPermissions || [];

        if (this.isInternalUser(user) || this.isAgencyManager(user)) {
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
}
