import './deals-library.view.less';

import {
    Component,
    ChangeDetectionStrategy,
    Inject,
    Input,
    OnInit,
    OnDestroy,
    ViewChild,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import {ColDef} from 'ag-grid-community';
import * as moment from 'moment';
import {ModalComponent} from '../../../../shared/components/modal/modal.component';
import {Deal} from '../../../../core/deals/types/deal';
import {DealConnection} from '../../../../core/deals/types/deal-connection';
import {DealConnectionRowData} from '../../types/deal-connection-row-data';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {DealsLibraryStore} from '../../services/deals-library-store/deals-library.store';
import {PaginationChangeEvent} from '../../../../shared/components/smart-grid/types/pagination-change-event';
import {DealActionsCellComponent} from '../..//components/deal-actions-cell/deal-actions-cell.component';
import {ConnectionActionsCellComponent} from '../../components/connection-actions-cell/connection-actions-cell.component';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {merge, Subject, Observable} from 'rxjs';
import {takeUntil, map, distinctUntilChanged, tap} from 'rxjs/operators';

const PAGINATION_URL_PARAMS = ['page', 'pageSize'];

@Component({
    selector: 'zem-deals-library-view',
    templateUrl: './deals-library.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [DealsLibraryStore],
})
export class DealsLibraryView implements OnInit, OnDestroy {
    @Input()
    agencyId: string;

    @ViewChild('editDealModal', {static: false})
    editDealModal: ModalComponent;
    @ViewChild('connectionsModal', {static: false})
    connectionsModal: ModalComponent;

    private ngUnsubscribe$: Subject<void> = new Subject();

    context: any;

    DEFAULT_PAGINATION = {
        page: 1,
        pageSize: 20,
    };

    dealsPaginationOptions: PaginationOptions = {
        type: 'server',
    };

    dealsColumnDefs: ColDef[] = [
        {headerName: 'Id', field: 'id'},
        {headerName: 'Deal name', field: 'name'},
        {headerName: 'Deal Id', field: 'dealId'},
        {headerName: 'Source', field: 'source'},
        {headerName: 'Floor price', field: 'floorPrice'},
        {
            headerName: 'Valid from',
            field: 'validFromDate',
            valueFormatter: data => {
                return this.formatDate(data.value);
            },
        },
        {
            headerName: 'Valid to',
            field: 'validToDate',
            valueFormatter: data => {
                return this.formatDate(data.value);
            },
        },
        {
            headerName: 'Accounts',
            field: 'numOfAccounts',
            cellClass: ['zem-deals-library__grid-cell--clickable'],
            onCellClicked: $event => {
                this.openConnectionsModal($event.data, 'account');
            },
        },
        {
            headerName: 'Campaigns',
            field: 'numOfCampaigns',
            cellClass: ['zem-deals-library__grid-cell--clickable'],
            onCellClicked: $event => {
                this.openConnectionsModal($event.data, 'campaign');
            },
        },
        {
            headerName: 'Ad Groups',
            field: 'numOfAdgroups',
            cellClass: ['zem-deals-library__grid-cell--clickable'],
            onCellClicked: $event => {
                this.openConnectionsModal($event.data, 'adgroup');
            },
        },
        {headerName: 'Notes', field: 'description'},
        {headerName: 'Created by', field: 'createdBy'},
        {
            headerName: '',
            width: 80,
            suppressSizeToFit: true,
            cellRendererFramework: DealActionsCellComponent,
            pinned: 'right',
        },
    ];

    connectionsPaginationOptions: PaginationOptions = {
        type: 'client',
    };
    connectionsColumnDefs: ColDef[] = [
        {headerName: 'Connection name', field: 'name'},
        {
            headerName: '',
            width: 40,
            suppressSizeToFit: true,
            cellRendererFramework: ConnectionActionsCellComponent,
            pinned: 'right',
        },
    ];
    connectionsRowData: DealConnectionRowData[];
    connectionType: string;

    constructor(
        public store: DealsLibraryStore,
        @Inject('ajs$location') private ajs$location: any
    ) {
        this.context = {
            componentParent: this,
        };
    }

    ngOnInit() {
        if (commonHelpers.isDefined(this.agencyId)) {
            this.subscribeToStateUpdates();
            const preselectedPagination = this.getPreselectedPagination();
            this.dealsPaginationOptions = {
                ...this.dealsPaginationOptions,
                ...preselectedPagination,
            };
            this.store
                .initStore(
                    this.agencyId,
                    preselectedPagination.page,
                    preselectedPagination.pageSize
                )
                .then(() => {
                    this.updateUrlParamsWithSelectedPagination(
                        preselectedPagination
                    );
                });
        }
    }

    ngOnDestroy() {
        this.updateUrlParamsWithSelectedPagination({
            page: null,
            pageSize: null,
        });
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    onPaginationChange($event: PaginationChangeEvent) {
        this.store.loadEntities($event.page, $event.pageSize).then(() => {
            this.updateUrlParamsWithSelectedPagination($event);
        });
    }

    openEditDealModal(deal: Partial<Deal>) {
        this.store.setActiveEntity(deal);
        this.editDealModal.open();
    }

    removeDeal(deal: Deal) {
        const pagination = this.getPreselectedPagination();
        if (
            confirm(
                `Are you sure you wish to delete ${deal.name} for ${
                    deal.source
                } media source?`
            )
        ) {
            this.store
                .deleteEntity(deal.id)
                .then(() =>
                    this.store.loadEntities(
                        pagination.page,
                        pagination.pageSize
                    )
                );
        }
    }

    saveDeal() {
        const pagination = this.getPreselectedPagination();
        this.store.saveActiveEntity().then(() => {
            this.editDealModal.close();
            this.store.loadEntities(pagination.page, pagination.pageSize);
        });
    }

    openConnectionsModal(deal: Partial<Deal>, type: string) {
        this.connectionType = type;
        this.store.setActiveEntity(deal);
        this.store.loadActiveEntityConnections();
        this.connectionsModal.open();
    }

    closeConnectionsModal() {
        const pagination = this.getPreselectedPagination();
        this.store.loadEntities(pagination.page, pagination.pageSize);
    }

    removeConnection(connection: DealConnectionRowData) {
        if (
            confirm(
                `Are you sure you wish to delete ${connection.name} connection?`
            )
        ) {
            this.store
                .deleteActiveEntityConnection(connection.connectionId)
                .then(() => {
                    this.store.loadActiveEntityConnections();
                });
        }
    }

    private subscribeToStateUpdates() {
        merge(this.createConnectionsUpdater$())
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe();
    }

    private createConnectionsUpdater$(): Observable<DealConnection[]> {
        return this.store.state$.pipe(
            map(state => state.activeEntity.connections),
            distinctUntilChanged(),
            tap(connections => {
                const rowData = connections.filter(
                    (connection: DealConnection) => {
                        return commonHelpers.isNotEmpty(
                            connection[this.connectionType]
                        );
                    }
                );
                this.connectionsRowData = rowData.map(
                    (connection: DealConnection) => {
                        return {
                            ...connection[this.connectionType],
                            connectionId: connection.id,
                            connectionType: this.connectionType,
                        };
                    }
                );
            })
        );
    }

    private updateUrlParamsWithSelectedPagination(selectedPagination: {
        page: number;
        pageSize: number;
    }): void {
        PAGINATION_URL_PARAMS.forEach(paramName => {
            const paramValue = selectedPagination[paramName];
            this.ajs$location.search(paramName, paramValue).replace();
        });
    }

    private getPreselectedPagination(): {page: number; pageSize: number} {
        const pagination = this.DEFAULT_PAGINATION;
        PAGINATION_URL_PARAMS.forEach(paramName => {
            const value: string = this.ajs$location.search()[paramName];
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

declare var angular: angular.IAngularStatic;
angular
    .module('one.downgraded')
    .directive(
        'zemDealsLibraryView',
        downgradeComponent({component: DealsLibraryView})
    );
