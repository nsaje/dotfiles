import './publisher-groups-library.view.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnInit,
    HostBinding,
    ChangeDetectorRef,
    OnDestroy,
    ViewChild,
    Inject,
} from '@angular/core';
import {Level} from '../../../../app.constants';
import {ActivatedRoute} from '@angular/router';
import {Subject} from 'rxjs';
import {filter, takeUntil} from 'rxjs/operators';
import {ColDef, DetailGridInfo, GridApi} from 'ag-grid-community';
import {PublisherGroupsLibraryStore} from '../../services/publisher-groups-library-store/publisher-groups-library.store';
import {PublisherGroupsService} from '../../../../core/publisher-groups/services/publisher-groups.service';
import {PublisherGroupActionsCellComponent} from '../../components/publisher-group-actions-cell/publisher-group-actions-cell.component';
import {PublisherGroup} from '../../../../core/publisher-groups/types/publisher-group';
import {ModalComponent} from '../../../../shared/components/modal/modal.component';
import {isDefined} from '../../../../shared/helpers/common.helpers';
import {
    booleanFormatter,
    dateTimeFormatter,
} from '../../../../shared/helpers/grid.helpers';

@Component({
    selector: 'zem-publisher-groups-library-view',
    templateUrl: './publisher-groups-library.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [PublisherGroupsLibraryStore],
})
export class PublisherGroupsLibraryView implements OnInit, OnDestroy {
    @HostBinding('class')
    cssClass = 'zem-publisher-groups-library-view';
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
        private route: ActivatedRoute,
        private changeDetectorRef: ChangeDetectorRef,
        public store: PublisherGroupsLibraryStore,
        private service: PublisherGroupsService,
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

        this.route.params
            .pipe(takeUntil(this.ngUnsubscribe$))
            .pipe(filter(params => isDefined(params.id)))
            .subscribe(params => {
                this.updateInternalState(params);
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
            this.store.deleteEntity(publisherGroup.id).then(() => {
                this.gridApi.showLoadingOverlay();
                this.store.loadEntities();
            });
        }
    }

    download(publisherGroup: PublisherGroup) {
        this.service.download(publisherGroup);
    }

    downloadErrors() {
        const activeEntity = this.store.state.activeEntity;
        const csvKey: string = activeEntity.fieldErrors.errorsCsvKey;
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
            accountId: this.store.state.accountId,
            includeSubdomains: true,
        });
    }

    private updateInternalState(params: any) {
        const accountId: string = params.id;

        this.showGridLoadingOverlays();

        this.store.setStore(accountId);
    }

    private showGridLoadingOverlays() {
        if (isDefined(this.gridApi)) {
            this.gridApi.showLoadingOverlay();
        }
        if (isDefined(this.systemGridApi)) {
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
                headerName: '',
                width: 100,
                minWidth: 100,
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
                    ? 'Number of placements'
                    : 'Number of publishers',
                field: 'size',
                width: 134,
                minWidth: 134,
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
            {headerName: '', width: 160},
            {
                headerName: '',
                maxWidth: 70,
                minWidth: 70,
                cellRendererFramework: PublisherGroupActionsCellComponent,
                pinned: 'right',
            },
        ];
    }
}
