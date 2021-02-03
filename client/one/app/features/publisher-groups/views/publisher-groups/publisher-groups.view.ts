import './publisher-groups.view.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnInit,
    HostBinding,
    OnDestroy,
    ViewChild,
    Inject,
} from '@angular/core';
import {ActivatedRoute, ParamMap, Router} from '@angular/router';
import {merge, Observable, Subject} from 'rxjs';
import {
    distinctUntilChanged,
    filter,
    map,
    takeUntil,
    tap,
} from 'rxjs/operators';
import {SmartGridColDef} from '../../../../shared/components/smart-grid/types/smart-grid-col-def';
import {DetailGridInfo, GridApi} from 'ag-grid-community';
import {PublisherGroupsStore} from '../../services/publisher-groups-store/publisher-groups.store';
import {PublisherGroupsService} from '../../../../core/publisher-groups/services/publisher-groups.service';
import {PublisherGroupActionsCellComponent} from '../../components/publisher-group-actions-cell/publisher-group-actions-cell.component';
import {PublisherGroup} from '../../../../core/publisher-groups/types/publisher-group';
import {ModalComponent} from '../../../../shared/components/modal/modal.component';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {
    booleanFormatter,
    dateTimeFormatter,
} from '../../../../shared/helpers/grid.helpers';
import {ItemScopeCellComponent} from '../../../../shared/components/smart-grid/components/cells/item-scope-cell/item-scope-cell.component';
import {ItemScopeRendererParams} from '../../../../shared/components/smart-grid/components/cells/item-scope-cell/types/item-scope.renderer-params';
import {PublisherGroupConnection} from '../../../../core/publisher-groups/types/publisher-group-connection';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {PageSizeConfig} from '../../../../shared/components/smart-grid/types/page-size-config';
import {PublisherGroupsStoreState} from '../../services/publisher-groups-store/publisher-groups.store.state';
import {RequestState} from '../../../../shared/types/request-state';
import {PaginationState} from '../../../../shared/components/smart-grid/types/pagination-state';
import {AuthStore} from '../../../../core/auth/services/auth.store';
import {ViewportBreakpoint} from '../../../../app.constants';

const EXPLICIT_PAGINATION_URL_PARAMS: {
    [key: string]: keyof PaginationState;
} = {page: 'page', pageSize: 'pageSize'};
const IMPLICIT_PAGINATION_URL_PARAMS: {
    [key: string]: keyof PaginationState;
} = {implicitPage: 'page', implicitPageSize: 'pageSize'};
const DEFAULT_PAGINATION: PaginationState = {
    page: 1,
    pageSize: 20,
};

@Component({
    selector: 'zem-publisher-groups-view',
    templateUrl: './publisher-groups.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [PublisherGroupsStore],
})
export class PublisherGroupsView implements OnInit, OnDestroy {
    @HostBinding('class')
    cssClass = 'zem-publisher-groups-view';
    @ViewChild('editPublisherGroupModal', {static: false})
    editPublisherGroupModal: ModalComponent;
    @ViewChild('connectionsModal', {static: false})
    connectionsModal: ModalComponent;
    @ViewChild('deleteFailedModal', {static: false})
    deleteFailedModal: ModalComponent;

    columnDefs: SmartGridColDef[] = [];
    implicitColumnDefs: SmartGridColDef[] = [];

    context: any;
    isReadOnly: boolean = true;

    PAGE_SIZE_OPTIONS: PageSizeConfig[] = [
        {name: '10', value: 10},
        {name: '20', value: 20},
        {name: '50', value: 50},
    ];

    explicitPaginationOptions: PaginationOptions = {
        type: 'server',
        pageSizeOptions: this.PAGE_SIZE_OPTIONS,
        ...DEFAULT_PAGINATION,
    };

    implicitPaginationOptions: PaginationOptions = {
        type: 'server',
        pageSizeOptions: this.PAGE_SIZE_OPTIONS,
        ...DEFAULT_PAGINATION,
    };

    addPublisherGroupModalTitle: string;
    editPublisherGroupModalTitle: string;
    private explicitGridApi: GridApi;
    private implicitGridApi: GridApi;
    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: PublisherGroupsStore,
        private route: ActivatedRoute,
        private router: Router,
        private service: PublisherGroupsService,
        private authStore: AuthStore
    ) {
        this.context = {
            componentParent: this,
        };
    }

    ngOnInit(): void {
        this.subscribeToStateUpdates();

        this.initColumnDefs();
        this.addPublisherGroupModalTitle = 'Create Publishers & Placement list';
        this.editPublisherGroupModalTitle = 'Edit Publishers & Placement list';

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

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    onExplicitGridReady($event: DetailGridInfo) {
        this.explicitGridApi = $event.api;
        this.toggleLoadingOverlay(
            this.store.state.requests.listExplicit.inProgress,
            this.explicitGridApi
        );
    }

    onImplicitGridReady($event: DetailGridInfo) {
        this.implicitGridApi = $event.api;
        this.toggleLoadingOverlay(
            this.store.state.requests.listImplicit.inProgress,
            this.implicitGridApi
        );
    }

    onPaginationChange($event: PaginationState, implicit: boolean) {
        if (implicit) {
            $event = {
                implicitPage: $event.page,
                implicitPageSize: $event.pageSize,
            } as any;
        }
        this.router.navigate([], {
            relativeTo: this.route,
            queryParams: $event,
            queryParamsHandling: 'merge',
            replaceUrl: true,
        });
    }

    delete(publisherGroup: PublisherGroup) {
        if (
            confirm(`Are you sure you wish to delete ${publisherGroup.name}?`)
        ) {
            this.store
                .deleteEntity(publisherGroup.id)
                .then(() => {
                    this.store.loadEntities(
                        false,
                        this.explicitPaginationOptions
                    );
                })
                .catch(reason => {
                    this.store.setActiveEntity(publisherGroup);
                    this.deleteFailedModal.open();
                });
        }
    }

    download(publisherGroup: PublisherGroup) {
        this.service.download(publisherGroup.id);
    }

    downloadErrors() {
        const activeEntity = this.store.state.activeEntity;
        const csvKey: string = activeEntity.fieldsErrors.errorsCsvKey;
        const publisherGroup: PublisherGroup = activeEntity.entity;
        this.service.downloadErrors(publisherGroup, csvKey);
    }

    downloadExample() {
        this.service.downloadExample();
    }

    openEditPublisherGroupModal(publisherGroup: Partial<PublisherGroup>) {
        this.store.setActiveEntity(publisherGroup);
        this.editPublisherGroupModal.open();
    }

    savePublisherGroup() {
        this.store.saveActiveEntity().then(() => {
            this.editPublisherGroupModal.close();
            this.store.loadEntities(false, this.explicitPaginationOptions);
        });
    }

    addPublisherGroup() {
        this.openEditPublisherGroupModal({
            agencyId: this.store.state.accountId
                ? null
                : this.store.state.agencyId,
            accountId: this.store.state.accountId,
            includeSubdomains: true,
        });
    }

    openConnectionsModal(publisherGroup: Partial<PublisherGroup>) {
        this.store.setActiveEntity(publisherGroup);
        this.store.loadActiveEntityConnections();
        this.connectionsModal.open();
    }

    removeConnection(connection: PublisherGroupConnection) {
        this.store.deleteActiveEntityConnection(connection).then(() => {
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
        this.explicitPaginationOptions = {
            ...this.explicitPaginationOptions,
            ...this.getPreselectedPagination(EXPLICIT_PAGINATION_URL_PARAMS),
        };
        this.implicitPaginationOptions = {
            ...this.implicitPaginationOptions,
            ...this.getPreselectedPagination(IMPLICIT_PAGINATION_URL_PARAMS),
        };

        this.store.setStore(
            agencyId,
            accountId,
            this.explicitPaginationOptions,
            this.implicitPaginationOptions
        );
    }

    private initColumnDefs() {
        this.columnDefs = [
            {headerName: 'ID', field: 'id', width: 120, minWidth: 80},
            {headerName: 'Name', field: 'name', width: 180, minWidth: 110},
            {
                headerName: 'Subdomains included',
                field: 'includeSubdomains',
                width: 220,
                minWidth: 134,
                valueFormatter: booleanFormatter,
            },
            {
                headerName: 'Number of publishers/placements',
                field: 'size',
                width: 220,
                minWidth: 200,
            },
            {
                headerName: 'Modified',
                field: 'modifiedDt',
                width: 220,
                minWidth: 134,
                valueFormatter: dateTimeFormatter('M/D/YYYY h:mm A'),
            },
            {
                headerName: 'Created',
                field: 'createdDt',
                width: 220,
                minWidth: 134,
                valueFormatter: dateTimeFormatter('M/D/YYYY h:mm A'),
            },
            {
                headerName: 'Scope',
                cellRendererFramework: ItemScopeCellComponent,
                cellRendererParams: {
                    getAgencyLink: item => {
                        return `/v2/analytics/accounts?filtered_agencies=${item.agencyId}`;
                    },
                    getAccountLink: item => {
                        return `/v2/analytics/account/${item.accountId}`;
                    },
                } as ItemScopeRendererParams<PublisherGroup>,
                minWidth: 200,
                resizable: true,
            },
            {
                headerName: '',
                width: 135,
                suppressSizeToFit: true,
                resizable: false,
                cellRendererFramework: PublisherGroupActionsCellComponent,
                pinned: 'right',
                unpinBelowGridWidth: ViewportBreakpoint.Tablet,
            },
        ];

        this.implicitColumnDefs = [
            {headerName: 'ID', field: 'id', width: 60, minWidth: 60},
            {headerName: 'Name', field: 'levelName', width: 170, minWidth: 170},
            {headerName: 'Level', field: 'level', width: 75, minWidth: 75},
            {
                headerName: 'Status',
                field: 'type',
                width: 66,
                minWidth: 66,
                valueFormatter: this.blacklistStatusFormatter,
            },
            {
                headerName: 'Subdomains included',
                field: 'includeSubdomains',
                width: 134,
                minWidth: 134,
                valueFormatter: booleanFormatter,
            },
            {
                headerName: 'Number of publishers/placements',
                field: 'size',
                width: 134,
                minWidth: 200,
            },
            {
                headerName: 'Modified',
                field: 'modifiedDt',
                width: 134,
                minWidth: 134,
                valueFormatter: dateTimeFormatter('M/D/YYYY h:mm A'),
            },
            {
                headerName: 'Created',
                field: 'createdDt',
                width: 134,
                minWidth: 134,
                valueFormatter: dateTimeFormatter('M/D/YYYY h:mm A'),
            },
            {
                headerName: 'Scope',
                cellRendererFramework: ItemScopeCellComponent,
                cellRendererParams: {
                    getAgencyLink: item => {
                        return `/v2/analytics/accounts?filtered_agencies=${item.agencyId}`;
                    },
                    getAccountLink: item => {
                        return `/v2/analytics/account/${item.accountId}`;
                    },
                } as ItemScopeRendererParams<PublisherGroup>,
                minWidth: 200,
                resizable: true,
            },
            {
                headerName: '',
                width: 45,
                suppressSizeToFit: true,
                resizable: false,
                cellRendererFramework: PublisherGroupActionsCellComponent,
                pinned: 'right',
                unpinBelowGridWidth: ViewportBreakpoint.Tablet,
            },
        ];
    }

    private blacklistStatusFormatter(params: {value: string}): string {
        const value: string = params.value;

        switch (value) {
            case 'Blacklist':
                return 'Blacklisted';
            case 'Whitelist':
                return 'Whitelisted';
            default:
                return value;
        }
    }

    private getPreselectedPagination(paginationParams: {
        [key: string]: keyof PaginationState;
    }): PaginationState {
        const pagination: PaginationState = {...DEFAULT_PAGINATION};
        Object.keys(paginationParams).forEach(paramName => {
            const queryParams: ParamMap = this.route.snapshot.queryParamMap;
            const paramValue: string = queryParams.get(paramName);
            if (paramValue) {
                const paramKey: keyof PaginationState =
                    paginationParams[paramName];
                pagination[paramKey] = Number(paramValue);
            }
        });
        return pagination;
    }

    private subscribeToStateUpdates() {
        merge(
            this.getGridProgressUpdater(
                state => [state.requests.listExplicit, state.requests.remove],
                () => this.explicitGridApi
            ),
            this.getGridProgressUpdater(
                state => [state.requests.listImplicit],
                () => this.implicitGridApi
            )
        )
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe();
    }

    private getGridProgressUpdater(
        requestStatesGetter: (x: PublisherGroupsStoreState) => RequestState[],
        gridApiGetter: () => GridApi
    ): Observable<boolean> {
        return this.store.state$.pipe(
            map(state =>
                requestStatesGetter(state).some(
                    requestState => requestState.inProgress
                )
            ),
            distinctUntilChanged(),
            tap(inProgress =>
                this.toggleLoadingOverlay(inProgress, gridApiGetter())
            )
        );
    }

    private toggleLoadingOverlay(show: boolean, gridApi: GridApi) {
        if (gridApi) {
            if (show) {
                gridApi.showLoadingOverlay();
            } else {
                gridApi.hideOverlay();
            }
        }
    }
}
