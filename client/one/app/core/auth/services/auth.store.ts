import {Injectable, OnDestroy, Injector} from '@angular/core';
import {Store} from '../../../shared/services/store/store';
import {StoreProvider} from '../../../shared/services/store/store.provider';
import {StoreAction} from '../../../shared/services/store/store.action';
import {StoreReducer} from '../../../shared/services/store/store.reducer';
import {StoreEffect} from '../../../shared/services/store/store.effect';
import {
    FetchCurrentUserAction,
    FetchCurrentUserActionEffect,
} from './effects/fetch-current-user.effect';
import {
    SetCurrentUserAction,
    SetCurrentUserActionReducer,
} from './reducers/set-current-user.reducer';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import * as commonHelpers from '../../../shared/helpers/common.helpers';
import * as storeHelpers from '../../../shared/helpers/store.helpers';
import * as arrayHelpers from '../../../shared/helpers/array.helpers';
import {merge, Subject, Observable} from 'rxjs';
import {takeUntil, map, distinctUntilChanged, tap} from 'rxjs/operators';
import {AuthStoreState} from './auth.store.state';
import {User} from '../../users/types/user';
import {downgradeInjectable} from '@angular/upgrade/static';
import {EntityPermissionValue} from '../../users/users.constants';
import {isDefined} from '../../../shared/helpers/common.helpers';

@Injectable()
export class AuthStore extends Store<AuthStoreState> implements OnDestroy {
    private requestStateUpdater: RequestStateUpdater;
    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(injector: Injector) {
        super(new AuthStoreState(), injector);
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
        this.subscribeToStateUpdates();
    }

    provide(): StoreProvider<
        StoreAction<any>,
        | StoreReducer<AuthStoreState, StoreAction<any>>
        | StoreEffect<AuthStoreState, StoreAction<any>>
    >[] {
        return [
            {
                provide: FetchCurrentUserAction,
                useClass: FetchCurrentUserActionEffect,
            },
            {
                provide: SetCurrentUserAction,
                useClass: SetCurrentUserActionReducer,
            },
        ];
    }

    initStore(): Promise<boolean> {
        return this.dispatch(
            new FetchCurrentUserAction({
                requestStateUpdater: this.requestStateUpdater,
            })
        );
    }

    //
    // CURRENT USER
    //

    getCurrentUser(): User {
        return {...this.state.user};
    }

    getCurrentUserId(): string {
        return this.state.user.id;
    }

    //
    //  PERMISSIONS
    //

    hasPermission(permission: string | string[]): boolean {
        if (arrayHelpers.isEmpty(this.state.permissions)) {
            return false;
        }
        const permissions: string[] = this.mapToArray(permission);
        if (arrayHelpers.isEmpty(permissions)) {
            return false;
        }
        const intersection: string[] = arrayHelpers.intersect(
            permissions,
            this.state.permissions
        );
        return intersection.length === permissions.length;
    }

    isPermissionInternal(permission: string): boolean {
        if (arrayHelpers.isEmpty(this.state.internalPermissions)) {
            return false;
        }
        return this.state.internalPermissions.includes(permission);
    }

    canAccessPlatformCosts(): boolean {
        return this.hasPermission('zemauth.can_view_platform_cost_breakdown');
    }

    canAccessAgencyCosts(): boolean {
        return this.hasPermission('zemauth.can_view_agency_cost_breakdown');
    }

    //
    //  ENTITY PERMISSIONS
    //

    hasAgencyScope(agencyId: string) {
        // TODO (msuber): deleted after User Roles will be released.
        if (!this.hasPermission('zemauth.fea_use_entity_permission')) {
            if (this.hasPermission('zemauth.can_see_all_accounts')) {
                return true;
            }
            return this.state.user.agencies.includes(Number(agencyId));
        }
        return this.hasPermissionOn(
            agencyId,
            null,
            EntityPermissionValue.WRITE
        );
    }

    canCreateNewAccount(): boolean {
        // TODO (msuber): deleted after User Roles will be released.
        if (!this.hasPermission('zemauth.fea_use_entity_permission')) {
            if (this.hasPermission('zemauth.can_see_all_accounts')) {
                return true;
            }
            return !arrayHelpers.isEmpty(this.state.user.agencies);
        }
        if (arrayHelpers.isEmpty(this.state.user.entityPermissions)) {
            return false;
        }
        return this.state.user.entityPermissions.some(ep => {
            return (
                (commonHelpers.isDefined(ep.agencyId) &&
                    !commonHelpers.isDefined(ep.accountId) &&
                    ep.permission === EntityPermissionValue.WRITE) ||
                (!commonHelpers.isDefined(ep.agencyId) &&
                    !commonHelpers.isDefined(ep.accountId) &&
                    ep.permission === EntityPermissionValue.WRITE)
            );
        });
    }

    hasReadOnlyAccessOn(
        agencyId: string | number,
        accountId: string | number
    ): boolean {
        // TODO (msuber): deleted after User Roles will be released.
        if (!this.hasPermission('zemauth.fea_use_entity_permission')) {
            if (isDefined(agencyId) && !isDefined(accountId)) {
                return !this.hasAgencyScope(`${agencyId}`);
            }
            return false;
        }
        return !this.hasPermissionOn(
            agencyId,
            accountId,
            EntityPermissionValue.WRITE
        );
    }

    hasReadOnlyAccessOnAnyEntity(): boolean {
        // TODO (msuber): deleted after User Roles will be released.
        if (!this.hasPermission('zemauth.fea_use_entity_permission')) {
            return false;
        }
        if (arrayHelpers.isEmpty(this.state.user.entityPermissions)) {
            return false;
        }

        if (
            this.hasPermissionOnAllEntities(EntityPermissionValue.READ) &&
            !this.hasPermissionOnAllEntities(EntityPermissionValue.WRITE)
        ) {
            return true;
        }

        const accountIds: Set<string> = new Set(
            this.state.user.entityPermissions
                .filter(ep => commonHelpers.isDefined(ep.accountId))
                .map(ep => ep.accountId)
        );
        if (accountIds.size > 0) {
            return Array.from(accountIds).some(accountId =>
                this.hasReadOnlyAccessOn(null, accountId)
            );
        }

        const agencyIds: Set<string> = new Set(
            this.state.user.entityPermissions
                .filter(ep => commonHelpers.isDefined(ep.agencyId))
                .map(ep => ep.agencyId)
        );
        if (agencyIds.size > 0) {
            return Array.from(agencyIds).some(agencyId =>
                this.hasReadOnlyAccessOn(agencyId, null)
            );
        }

        return false;
    }

    hasPermissionOn(
        agencyId: string | number,
        accountId: string | number,
        permission: EntityPermissionValue,
        fallbackPermission?: string | string[]
    ): boolean {
        // TODO (msuber): deleted after User Roles will be released.
        if (!this.hasPermission('zemauth.fea_use_entity_permission')) {
            return this.hasPermission(fallbackPermission);
        }

        if (
            !commonHelpers.isDefined(permission) ||
            arrayHelpers.isEmpty(this.state.user.entityPermissions)
        ) {
            return false;
        }

        const parsedAgencyId: string = commonHelpers.isDefined(agencyId)
            ? agencyId.toString()
            : null;
        const parsedAccountId: string = commonHelpers.isDefined(accountId)
            ? accountId.toString()
            : null;

        return this.state.user.entityPermissions.some(ep => {
            return (
                [parsedAgencyId, null].includes(ep.agencyId) &&
                [parsedAccountId, null].includes(ep.accountId) &&
                ep.permission === permission
            );
        });
    }

    hasPermissionOnAllEntities(
        permission: EntityPermissionValue,
        fallbackPermission?: string | string[]
    ): boolean {
        return this.hasPermissionOn(null, null, permission, fallbackPermission);
    }

    hasPermissionOnAnyEntity(permission: EntityPermissionValue): boolean {
        if (
            !commonHelpers.isDefined(permission) ||
            arrayHelpers.isEmpty(this.state.user.entityPermissions)
        ) {
            return false;
        }

        return this.state.user.entityPermissions.some(ep => {
            return ep.permission === permission;
        });
    }

    ngOnDestroy(): void {
        super.ngOnDestroy();
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    private mapToArray(value: string | string[]): string[] {
        if (typeof value === 'string') {
            return [value];
        }
        if (Array.isArray(value)) {
            return [...value];
        }
        return [];
    }

    private subscribeToStateUpdates() {
        merge(this.createUserUpdater$())
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe();
    }

    private createUserUpdater$(): Observable<User> {
        return this.state$.pipe(
            map(state => state.user),
            distinctUntilChanged(),
            tap(user => {
                // Configure Raven/Sentry user context
                (<any>window).Raven.setUserContext({
                    username: user.name,
                    email: user.email,
                });
            })
        );
    }
}

declare var angular: angular.IAngularStatic;
angular
    .module('one.downgraded')
    .factory('zemAuthStore', downgradeInjectable(AuthStore));
