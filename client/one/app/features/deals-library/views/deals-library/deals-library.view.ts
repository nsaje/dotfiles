import './deals-library.view.less';

import {
    Component,
    ChangeDetectionStrategy,
    Inject,
    OnInit,
    OnDestroy,
    ViewChild,
    HostBinding,
} from '@angular/core';
import {merge, Subject, Observable} from 'rxjs';
import {takeUntil, map, distinctUntilChanged, tap, take} from 'rxjs/operators';
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
import {ActivatedRoute, Router} from '@angular/router';
import {
    LEVEL_TO_ENTITY_TYPE_MAP,
    LevelParam,
    Level,
    LEVEL_PARAM_TO_LEVEL_MAP,
} from '../../../../app.constants';

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

    agencyId: string;
    accountId: string;

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

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: DealsLibraryStore,
        private route: ActivatedRoute,
        private router: Router,
        @Inject('zemNavigationNewService') private zemNavigationNewService: any
    ) {
        this.context = {
            componentParent: this,
        };
    }

    ngOnInit() {
        this.accountId = this.route.snapshot.params.id;
        const level = this.getLevel(this.route.snapshot.data.level);

        this.zemNavigationNewService
            .getEntityById(LEVEL_TO_ENTITY_TYPE_MAP[level], this.accountId)
            .then((account: any) => {
                this.agencyId = account.data.agencyId;
                this.accountId = account.data.id;
                this.updateInternalState();
            });
    }

    ngOnDestroy() {
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

    private getLevel(levelParam: LevelParam): Level {
        return LEVEL_PARAM_TO_LEVEL_MAP[levelParam];
    }

    private updateInternalState() {
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
                null, // this.accountId
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
        const queryParams = {};
        PAGINATION_URL_PARAMS.forEach(paramName => {
            const paramValue = selectedPagination[paramName];
            queryParams[paramName] = paramValue;
        });
        this.router.navigate([], {
            relativeTo: this.route,
            queryParams: queryParams,
            queryParamsHandling: 'merge',
            replaceUrl: true,
        });
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

    private updateUrlParamsWithKeyword(keyword: string | null): void {
        keyword = keyword ? keyword : null;
        this.router.navigate([], {
            relativeTo: this.route,
            queryParams: {keyword: keyword},
            queryParamsHandling: 'merge',
            replaceUrl: true,
        });
    }

    private getPreselectedKeyword(): string | null {
        const keyword = this.route.snapshot.queryParamMap.get('keyword');
        return commonHelpers.isDefined(keyword) ? keyword : null;
    }

    private formatDate(date: Date): string {
        if (commonHelpers.isDefined(date)) {
            return moment(date).format('MM/DD/YYYY');
        }
        return 'N/A';
    }
}
