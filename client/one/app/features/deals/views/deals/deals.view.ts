import './deals.view.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnInit,
    OnDestroy,
    ViewChild,
    HostBinding,
} from '@angular/core';
import {merge, Subject, Observable} from 'rxjs';
import {
    takeUntil,
    map,
    distinctUntilChanged,
    tap,
    filter,
} from 'rxjs/operators';
import {DetailGridInfo, GridApi} from 'ag-grid-community';
import {ModalComponent} from '../../../../shared/components/modal/modal.component';
import {FieldErrors} from 'one/app/shared/types/field-errors';
import {Deal} from '../../../../core/deals/types/deal';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {DealsStore} from '../../services/deals-store/deals.store';
import {PaginationState} from '../../../../shared/components/smart-grid/types/pagination-state';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import * as arrayHelpers from '../../../../shared/helpers/array.helpers';
import {ActivatedRoute, Router} from '@angular/router';
import {AuthStore} from '../../../../core/auth/services/auth.store';
import {EntityPermissionValue} from '../../../../core/users/users.constants';
import {
    DEFAULT_PAGINATION,
    PAGINATION_URL_PARAMS,
    DEFAULT_PAGINATION_OPTIONS,
} from '../../deals.config';
import {FormattedDeal} from '../../types/formatted-deal';
import {DealConnectionType} from '../../types/deal-connection-type';

@Component({
    selector: 'zem-deals-view',
    templateUrl: './deals.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [DealsStore],
})
export class DealsView implements OnInit, OnDestroy {
    @HostBinding('class')
    cssClass = 'zem-deals-view';
    @ViewChild('editDealModal', {static: false})
    editDealModal: ModalComponent;
    @ViewChild('connectionsModal', {static: false})
    connectionsModal: ModalComponent;

    context: any;
    isReadOnly: boolean = true;

    keyword: string;
    paginationOptions: PaginationOptions = DEFAULT_PAGINATION_OPTIONS;

    connectionType: string;
    canSaveActiveEntity = false;

    formattedDeals: FormattedDeal[];

    private gridApi: GridApi;
    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: DealsStore,
        public authStore: AuthStore,
        private route: ActivatedRoute,
        private router: Router
    ) {
        this.context = {
            componentParent: this,
        };
    }

    ngOnInit() {
        this.subscribeToStoreStateUpdates();
        this.route.queryParams
            .pipe(takeUntil(this.ngUnsubscribe$))
            .pipe(
                filter(queryParams =>
                    commonHelpers.isDefined(queryParams.agencyId)
                )
            )
            .subscribe(queryParams => {
                this.updateInternalState(queryParams);
            });
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

    onGridReady($event: DetailGridInfo) {
        this.gridApi = $event.api;
    }

    openEditDealModal(deal: Partial<Deal>) {
        this.store.setActiveEntity(deal);
        this.editDealModal.open();
    }

    removeDeal(deal: Deal) {
        if (
            confirm(
                `Are you sure you wish to delete ${deal.name} for ${deal.source} media source?`
            )
        ) {
            this.store.deleteEntity(deal.id).then(() => {
                this.gridApi.showLoadingOverlay();
                this.store.loadEntities(
                    this.paginationOptions.page,
                    this.paginationOptions.pageSize,
                    this.keyword
                );
            });
        }
    }

    saveDeal() {
        this.store.saveActiveEntity().then(() => {
            this.editDealModal.close();
            this.gridApi.showLoadingOverlay();
            this.store.loadEntities(
                this.paginationOptions.page,
                this.paginationOptions.pageSize,
                this.keyword
            );
        });
    }

    searchDeals(keyword: string) {
        this.router.navigate([], {
            relativeTo: this.route,
            queryParams: {keyword: keyword},
            queryParamsHandling: 'merge',
            replaceUrl: true,
        });
    }

    openConnectionsModal(dealId: string, connectionType: DealConnectionType) {
        this.connectionType = connectionType;
        this.store.setActiveEntity(
            this.store.state.entities.find(deal => deal.id === dealId)
        );
        this.store.loadActiveEntityConnections();
        this.connectionsModal.open();
    }

    closeConnectionsModal() {
        this.store.loadEntities(
            this.paginationOptions.page,
            this.paginationOptions.pageSize,
            this.keyword
        );
    }

    removeConnection(connectionId: string) {
        this.store.deleteActiveEntityConnection(connectionId).then(() => {
            this.store.loadActiveEntityConnections();
        });
    }

    private updateInternalState(queryParams: any) {
        const agencyId: string = queryParams.agencyId;
        const accountId: string | null = queryParams.accountId || null;
        this.isReadOnly = this.authStore.hasReadOnlyAccessOn(
            agencyId,
            accountId
        );
        this.keyword = queryParams.keyword || null;
        this.paginationOptions = {
            ...this.paginationOptions,
            ...this.getPreselectedPagination(),
        };

        if (commonHelpers.isDefined(this.gridApi)) {
            this.gridApi.showLoadingOverlay();
        }

        if (
            agencyId !== this.store.state.agencyId ||
            accountId !== this.store.state.accountId
        ) {
            this.store.setStore(
                agencyId,
                accountId,
                this.paginationOptions.page,
                this.paginationOptions.pageSize,
                this.keyword
            );
        } else {
            this.store.loadEntities(
                this.paginationOptions.page,
                this.paginationOptions.pageSize,
                this.keyword
            );
        }
    }

    private subscribeToStoreStateUpdates() {
        merge(
            this.createActiveEntityErrorUpdater$(),
            this.createFormattedEntitesUpdater$()
        )
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

    private createFormattedEntitesUpdater$(): Observable<any> {
        return this.store.state$.pipe(
            map(state => state.entities),
            distinctUntilChanged(),
            tap(entities => {
                this.formattedDeals = entities.map((entity: Deal) => ({
                    ...entity,
                    canViewConnections: this.authStore.hasPermissionOn(
                        this.store.state.agencyId,
                        entity.accountId,
                        EntityPermissionValue.READ
                    ),
                }));
            })
        );
    }

    private getPreselectedPagination(): PaginationState {
        const pagination = {...DEFAULT_PAGINATION};
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
}
