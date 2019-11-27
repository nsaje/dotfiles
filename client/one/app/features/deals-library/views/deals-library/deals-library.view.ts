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
import {merge, Subject, Observable} from 'rxjs';
import {takeUntil, map, distinctUntilChanged, tap} from 'rxjs/operators';
import {ColDef} from 'ag-grid-community';
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

    paginationOptions: PaginationOptions = {
        type: 'server',
    };

    columnDefs: ColDef[] = [
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
            cellClassRules: {'zem-deals-library__grid-cell--clickable': 'x>=1'},
            onCellClicked: $event => {
                if ($event.value >= 1) {
                    this.openConnectionsModal($event.data, 'account');
                }
            },
        },
        {
            headerName: 'Campaigns',
            field: 'numOfCampaigns',
            cellClassRules: {'zem-deals-library__grid-cell--clickable': 'x>=1'},
            onCellClicked: $event => {
                if ($event.value >= 1) {
                    this.openConnectionsModal($event.data, 'campaign');
                }
            },
        },
        {
            headerName: 'Ad Groups',
            field: 'numOfAdgroups',
            cellClassRules: {'zem-deals-library__grid-cell--clickable': 'x>=1'},
            onCellClicked: $event => {
                if ($event.value >= 1) {
                    this.openConnectionsModal($event.data, 'adgroup');
                }
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

    connectionType: string;
    canSaveActiveEntity = false;

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
            const keyword = this.getPreselectedKeyword();
            this.paginationOptions = {
                ...this.paginationOptions,
                ...preselectedPagination,
            };
            this.store
                .initStore(
                    this.agencyId,
                    preselectedPagination.page,
                    preselectedPagination.pageSize,
                    keyword
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
        this.updateUrlParamsWithKeyword(null);
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    onPaginationChange($event: PaginationChangeEvent) {
        const keyword = this.getPreselectedKeyword();
        this.store
            .loadEntities($event.page, $event.pageSize, keyword)
            .then(() => {
                this.updateUrlParamsWithSelectedPagination($event);
            });
    }

    openEditDealModal(deal: Partial<Deal>) {
        this.store.setActiveEntity(deal);
        this.editDealModal.open();
    }

    removeDeal(deal: Deal) {
        const pagination = this.getPreselectedPagination();
        const keyword = this.getPreselectedKeyword();
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
                        pagination.pageSize,
                        keyword
                    )
                );
        }
    }

    saveDeal() {
        const pagination = this.getPreselectedPagination();
        const keyword = this.getPreselectedKeyword();
        this.store.saveActiveEntity().then(() => {
            this.editDealModal.close();
            this.store.loadEntities(
                pagination.page,
                pagination.pageSize,
                keyword
            );
        });
    }

    searchDeals(keyword: string) {
        const pagination = this.getPreselectedPagination();
        this.store
            .loadEntities(pagination.page, pagination.pageSize, keyword)
            .then(() => {
                this.updateUrlParamsWithKeyword(keyword);
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
        const keyword = this.getPreselectedKeyword();
        this.store.loadEntities(pagination.page, pagination.pageSize, keyword);
    }

    removeConnection(connectionId: string) {
        this.store.deleteActiveEntityConnection(connectionId).then(() => {
            this.store.loadActiveEntityConnections();
        });
    }

    private subscribeToStateUpdates() {
        merge(this.createActiveEntityErrorUpdater$())
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe();
    }

    private createActiveEntityErrorUpdater$(): Observable<any> {
        return this.store.state$.pipe(
            map(state => state.activeEntity.fieldsErrors),
            distinctUntilChanged(),
            tap(fieldsErrors => {
                // @ts-ignore
                this.canSaveActiveEntity = Object.values(fieldsErrors).every(
                    (fieldValue: FieldErrors) =>
                        arrayHelpers.isEmpty(fieldValue)
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

    private updateUrlParamsWithKeyword(keyword: string | null): void {
        keyword = keyword ? keyword : null;
        this.ajs$location.search('keyword', keyword).replace();
    }

    private getPreselectedKeyword(): string | null {
        const keyword = this.ajs$location.search().keyword;
        return commonHelpers.isDefined(keyword) ? keyword : null;
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
