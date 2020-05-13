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
import {ActivatedRoute} from '@angular/router';
import {Subject} from 'rxjs';
import {filter, takeUntil} from 'rxjs/operators';
import {ColDef, DetailGridInfo, GridApi} from 'ag-grid-community';
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
import {ItemScopeCellComponent} from '../../../../shared/components/smart-grid/components/cell/item-scope-cell/item-scope-cell.component';
import {ItemScopeRendererParams} from '../../../../shared/components/smart-grid/components/cell/item-scope-cell/types/item-scope.renderer-params';
import {NotificationService} from '../../../../core/notification/services/notification.service';

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

    columnDefs: ColDef[] = [];
    systemColumnDefs: ColDef[] = [];

    context: any;

    showNewLabels: boolean = false;
    addPublisherGroupModalTitle: string;
    editPublisherGroupModalTitle: string;
    private gridApi: GridApi;
    private systemGridApi: GridApi;
    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: PublisherGroupsStore,
        private route: ActivatedRoute,
        private service: PublisherGroupsService,
        private notificationService: NotificationService,
        @Inject('zemPermissions') private zemPermissions: any
    ) {
        this.context = {
            componentParent: this,
        };
    }

    ngOnInit(): void {
        this.showNewLabels = this.zemPermissions.hasPermission(
            'zemauth.can_see_new_publisher_library'
        );

        this.initColumnDefs();
        this.addPublisherGroupModalTitle = this.showNewLabels
            ? 'Create Publishers & Placement list'
            : 'Add new publisher group';
        this.editPublisherGroupModalTitle = this.showNewLabels
            ? 'Edit Publishers & Placement list'
            : 'Edit publisher group';

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

    onGridReady($event: DetailGridInfo) {
        this.gridApi = $event.api;
    }

    onSystemGridReady($event: DetailGridInfo) {
        this.systemGridApi = $event.api;
    }

    delete(publisherGroup: PublisherGroup) {
        if (
            confirm(`Are you sure you wish to delete ${publisherGroup.name}?`)
        ) {
            this.store
                .deleteEntity(publisherGroup.id)
                .then(() => {
                    this.gridApi.showLoadingOverlay();
                    this.store.loadEntities();
                })
                .catch(reason =>
                    this.notificationService.error(
                        reason,
                        'This publisher group can not be deleted'
                    )
                );
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
            this.showGridLoadingOverlays();
            this.store.loadEntities();
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

    private updateInternalState(queryParams: any) {
        const agencyId = queryParams.agencyId;
        const accountId = queryParams.accountId || null;

        this.showGridLoadingOverlays();
        this.store.setStore(agencyId, accountId);
    }

    private showGridLoadingOverlays() {
        if (commonHelpers.isDefined(this.gridApi)) {
            this.gridApi.showLoadingOverlay();
        }
        if (commonHelpers.isDefined(this.systemGridApi)) {
            this.systemGridApi.showLoadingOverlay();
        }
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
                headerName: this.showNewLabels
                    ? 'Number of publishers/placements'
                    : 'Number of publishers',
                field: 'size',
                width: 220,
                minWidth: this.showNewLabels ? 200 : 134,
            },
            {
                headerName: 'Modified',
                field: 'modified',
                width: 220,
                minWidth: 134,
                valueFormatter: dateTimeFormatter('M/D/YYYY h:mm A'),
            },
            {
                headerName: 'Created',
                field: 'created',
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
                width: 105,
                suppressSizeToFit: true,
                resizable: false,
                cellRendererFramework: PublisherGroupActionsCellComponent,
                pinned: 'right',
            },
        ];

        this.systemColumnDefs = [
            {headerName: 'ID', field: 'id', width: 60, minWidth: 60},
            {headerName: 'Name', field: 'levelName', width: 170, minWidth: 170},
            {headerName: 'Level', field: 'level', width: 75, minWidth: 75},
            {
                headerName: this.showNewLabels ? 'Status' : 'Type',
                field: 'type',
                width: 66,
                minWidth: 66,
                valueFormatter: this.showNewLabels
                    ? this.blacklistStatusFormatter
                    : null,
            },
            {
                headerName: 'Subdomains included',
                field: 'includeSubdomains',
                width: 134,
                minWidth: 134,
                valueFormatter: booleanFormatter,
            },
            {
                headerName: this.showNewLabels
                    ? 'Number of publishers/placements'
                    : 'Number of publishers',
                field: 'size',
                width: 134,
                minWidth: this.showNewLabels ? 200 : 134,
            },
            {
                headerName: 'Modified',
                field: 'modified',
                width: 134,
                minWidth: 134,
                valueFormatter: dateTimeFormatter('M/D/YYYY h:mm A'),
            },
            {
                headerName: 'Created',
                field: 'created',
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
}
