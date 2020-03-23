import './deals-library.view.less';

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
import {ColDef, DetailGridInfo, GridApi} from 'ag-grid-community';
import * as moment from 'moment';
import {ModalComponent} from '../../../../shared/components/modal/modal.component';
import {FieldErrors} from 'one/app/shared/types/field-errors';
import {Deal} from '../../../../core/deals/types/deal';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {DealsLibraryStore} from '../../services/deals-library-store/deals-library.store';
import {PaginationChangeEvent} from '../../../../shared/components/smart-grid/types/pagination-change-event';
import {DealActionsCellComponent} from '../..//components/deal-actions-cell/deal-actions-cell.component';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import * as arrayHelpers from '../../../../shared/helpers/array.helpers';
import {ActivatedRoute, Router} from '@angular/router';

const PAGINATION_URL_PARAMS = ['page', 'pageSize'];

@Component({
    selector: 'zem-deals-library-view',
    templateUrl: './deals-library.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [DealsLibraryStore],
})
export class DealsLibraryView implements OnInit, OnDestroy {
    @HostBinding('class')
    cssClass = 'zem-deals-library-view';
    @ViewChild('editDealModal', {static: false})
    editDealModal: ModalComponent;
    @ViewChild('connectionsModal', {static: false})
    connectionsModal: ModalComponent;

    context: any;

    DEFAULT_PAGINATION = {
        page: 1,
        pageSize: 20,
    };

    keyword: string;
    paginationOptions: PaginationOptions = {
        type: 'server',
        ...this.DEFAULT_PAGINATION,
    };

    columnDefs: ColDef[] = [
        {
            headerName: 'Id',
            field: 'id',
            width: 80,
            resizable: false,
            suppressSizeToFit: true,
        },
        {
            headerName: 'Deal name',
            field: 'name',
            minWidth: 250,
        },
        {
            headerName: 'Deal Id',
            field: 'dealId',
            minWidth: 150,
        },
        {
            headerName: 'Source',
            field: 'source',
            minWidth: 90,
        },
        {
            headerName: 'Floor price',
            field: 'floorPrice',
            width: 90,
            suppressSizeToFit: true,
            resizable: false,
        },
        {
            headerName: 'Valid from',
            field: 'validFromDate',
            valueFormatter: data => {
                return this.formatDate(data.value);
            },
            width: 110,
            suppressSizeToFit: true,
            resizable: false,
        },
        {
            headerName: 'Valid to',
            field: 'validToDate',
            valueFormatter: data => {
                return this.formatDate(data.value);
            },
            width: 110,
            suppressSizeToFit: true,
            resizable: false,
        },
        {
            headerName: 'Scope',
            field: 'agencyId',
            valueFormatter: data => {
                if (commonHelpers.isDefined(data.value)) {
                    return 'Agency';
                } else {
                    return 'Account';
                }
            },
            width: 90,
            suppressSizeToFit: true,
            resizable: false,
        },
        {
            headerName: 'Accounts',
            field: 'numOfAccounts',
            cellClassRules: {
                'zem-deals-library-view__grid-cell--clickable': 'x>=1',
            },
            onCellClicked: $event => {
                if ($event.value >= 1) {
                    this.openConnectionsModal($event.data, 'account');
                }
            },
            width: 70,
            suppressSizeToFit: true,
            resizable: false,
        },
        {
            headerName: 'Campaigns',
            field: 'numOfCampaigns',
            cellClassRules: {
                'zem-deals-library-view__grid-cell--clickable': 'x>=1',
            },
            onCellClicked: $event => {
                if ($event.value >= 1) {
                    this.openConnectionsModal($event.data, 'campaign');
                }
            },
            width: 80,
            suppressSizeToFit: true,
            resizable: false,
        },
        {
            headerName: 'Ad Groups',
            field: 'numOfAdgroups',
            cellClassRules: {
                'zem-deals-library-view__grid-cell--clickable': 'x>=1',
            },
            onCellClicked: $event => {
                if ($event.value >= 1) {
                    this.openConnectionsModal($event.data, 'adgroup');
                }
            },
            width: 80,
            suppressSizeToFit: true,
            resizable: false,
        },
        {
            headerName: 'Notes',
            field: 'description',
            minWidth: 90,
        },
        {
            headerName: 'Created by',
            field: 'createdBy',
            minWidth: 180,
        },
        {
            headerName: '',
            cellRendererFramework: DealActionsCellComponent,
            pinned: 'right',
            width: 75,
            suppressSizeToFit: true,
            resizable: false,
        },
    ];

    connectionType: string;
    canSaveActiveEntity = false;

    private gridApi: GridApi;
    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: DealsLibraryStore,
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

    onPaginationChange($event: PaginationChangeEvent) {
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
                `Are you sure you wish to delete ${deal.name} for ${
                    deal.source
                } media source?`
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

    openConnectionsModal(deal: Partial<Deal>, type: string) {
        this.connectionType = type;
        this.store.setActiveEntity(deal);
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
        const agencyId = queryParams.agencyId;
        const accountId = queryParams.accountId || null;
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
        merge(this.createActiveEntityErrorUpdater$())
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe();
    }

    private createActiveEntityErrorUpdater$(): Observable<any> {
        return this.store.state$.pipe(
            map(state => state.activeEntity.fieldsErrors),
            distinctUntilChanged(),
            tap(fieldsErrors => {
                this.canSaveActiveEntity = Object.values(fieldsErrors).every(
                    (fieldValue: FieldErrors) =>
                        arrayHelpers.isEmpty(fieldValue)
                );
            })
        );
    }

    private getPreselectedPagination(): {page: number; pageSize: number} {
        const pagination = this.DEFAULT_PAGINATION;
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

    private formatDate(date: Date): string {
        if (commonHelpers.isDefined(date)) {
            return moment(date).format('MM/DD/YYYY');
        }
        return 'N/A';
    }
}
