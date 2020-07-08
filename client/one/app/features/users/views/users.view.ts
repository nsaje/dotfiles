import './users.view.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnInit,
    OnDestroy,
    HostBinding,
    Inject,
    ViewChild,
} from '@angular/core';
import {merge, Observable, Subject} from 'rxjs';
import {
    takeUntil,
    filter,
    map,
    distinctUntilChanged,
    tap,
} from 'rxjs/operators';
import {ActivatedRoute, Router} from '@angular/router';
import {UsersStore} from '../services/users-store/users.store';
import {PaginationOptions} from '../../../shared/components/smart-grid/types/pagination-options';
import {isDefined} from '../../../shared/helpers/common.helpers';
import {PaginationState} from '../../../shared/components/smart-grid/types/pagination-state';
import {
    DEFAULT_PAGINATION,
    DEFAULT_PAGINATION_OPTIONS,
    PAGINATION_URL_PARAMS,
} from '../users.config';
import {ModalComponent} from '../../../shared/components/modal/modal.component';
import {FieldErrors} from '../../../shared/types/field-errors';
import * as arrayHelpers from '../../../shared/helpers/array.helpers';
import {User} from '../../../core/users/types/user';
import {Account} from '../../../core/entities/types/account/account';
import {ScopeSelectorState} from '../../../shared/components/scope-selector/scope-selector.constants';

@Component({
    selector: 'zem-users-view',
    templateUrl: './users.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [UsersStore],
})
export class UsersView implements OnInit, OnDestroy {
    @HostBinding('class')
    cssClass = 'zem-users-view';
    @ViewChild('editUserModal', {static: false})
    editUserModal: ModalComponent;

    context: any;

    keyword: string;
    showInternal: boolean = false;
    paginationOptions: PaginationOptions = DEFAULT_PAGINATION_OPTIONS;
    canSaveActiveEntity: boolean = false;

    availableAccounts: Account[] = [];
    addAccountId: string;
    isAddAccountVisible: boolean = false;

    readonly ScopeSelectorState = ScopeSelectorState;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: UsersStore,
        private route: ActivatedRoute,
        private router: Router,
        @Inject('zemPermissions') public zemPermissions: any
    ) {
        this.context = {
            componentParent: this,
        };
    }

    ngOnInit() {
        this.subscribeToStoreStateUpdates();
        this.route.queryParams
            .pipe(takeUntil(this.ngUnsubscribe$))
            .pipe(filter(queryParams => isDefined(queryParams.agencyId)))
            .subscribe(queryParams => {
                this.updateInternalState(queryParams);
            });

        this.store.state$
            .pipe(
                map(state => state.activeEntity.entityAccounts),
                distinctUntilChanged(),
                takeUntil(this.ngUnsubscribe$)
            )
            .subscribe(this.updateAvailableAccounts.bind(this));
    }

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    onPaginationChange($event: PaginationState) {
        this.router.navigate([], {
            relativeTo: this.route,
            queryParams: $event,
            queryParamsHandling: 'merge',
            replaceUrl: true,
        });
    }

    searchUsers(keyword: string) {
        this.router.navigate([], {
            relativeTo: this.route,
            queryParams: {keyword},
            queryParamsHandling: 'merge',
            replaceUrl: true,
        });
    }

    changeShowInternal(showInternal: boolean) {
        this.router.navigate([], {
            relativeTo: this.route,
            queryParams: {showInternal},
            queryParamsHandling: 'merge',
            replaceUrl: true,
        });
    }

    removeUser(user: User) {
        if (
            confirm(
                `Are you sure you wish to delete user ${user.firstName} ${user.lastName} from this agency?`
            )
        ) {
            this.store.deleteEntity(user.id).then(() => {
                this.store.loadEntities(
                    this.paginationOptions.page,
                    this.paginationOptions.pageSize,
                    this.keyword
                );
            });
        }
    }

    openEditUserModal(user: Partial<User>) {
        this.clearAddAccountData();
        this.store.setActiveEntity(user);
        this.editUserModal.open();
    }

    saveUser() {
        this.store.saveActiveEntity().then(() => {
            this.editUserModal.close();
            this.store.loadEntities(
                this.paginationOptions.page,
                this.paginationOptions.pageSize,
                this.keyword
            );
        });
    }

    addAccountById($event: string) {
        this.store.addActiveEntityAccount(
            this.store.state.accounts.find(account => account.id === $event)
        );
        this.clearAddAccountData();
    }

    updateAvailableAccounts(entityAccounts: Account[]) {
        this.availableAccounts = this.store.state.accounts.filter(
            account => !entityAccounts.includes(account)
        );
    }

    private clearAddAccountData() {
        this.addAccountId = undefined;
        this.isAddAccountVisible = false;
    }

    private updateInternalState(queryParams: any) {
        const agencyId = queryParams.agencyId;
        const accountId = queryParams.accountId || null;
        this.keyword = queryParams.keyword || null;
        this.showInternal = queryParams?.showInternal === 'true' || null;
        this.paginationOptions = {
            ...this.paginationOptions,
            ...this.getPreselectedPagination(),
        };

        if (
            agencyId !== this.store.state.agencyId ||
            accountId !== this.store.state.accountId
        ) {
            this.store.setStore(
                agencyId,
                accountId,
                this.paginationOptions.page,
                this.paginationOptions.pageSize,
                this.keyword,
                this.showInternal
            );
        } else {
            this.store.loadEntities(
                this.paginationOptions.page,
                this.paginationOptions.pageSize,
                this.keyword,
                this.showInternal
            );
        }
    }

    private getPreselectedPagination(): PaginationState {
        const pagination: PaginationState = {...DEFAULT_PAGINATION};
        PAGINATION_URL_PARAMS.forEach(paramName => {
            const value: string = this.route.snapshot.queryParamMap.get(
                paramName
            );
            if (value) {
                pagination[paramName] = Number(value);
            }
        });
        return pagination;
    }

    private subscribeToStoreStateUpdates() {
        merge(this.createActiveEntityErrorUpdater$())
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe();
    }

    private createActiveEntityErrorUpdater$(): Observable<any> {
        return this.store.state$.pipe(
            map(state => state.activeEntity.fieldsErrors),
            distinctUntilChanged(),
            tap(fieldsErrors => {
                this.canSaveActiveEntity = Object.values(
                    fieldsErrors
                ).every((fieldValue: FieldErrors) =>
                    arrayHelpers.isEmpty(fieldValue)
                );
            })
        );
    }
}
