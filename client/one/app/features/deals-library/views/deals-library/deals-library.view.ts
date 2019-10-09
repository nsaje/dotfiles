import './deals-library.view.less';

import {
    Component,
    ChangeDetectionStrategy,
    Inject,
    Input,
    OnInit,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import {Subject} from 'rxjs';
import {takeUntil, map, distinctUntilChanged} from 'rxjs/operators';
import {ColDef} from 'ag-grid-community';
import * as moment from 'moment';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {DealsLibraryStore} from '../../services/deals-library-store/deals-library.store';
import {PaginationChangeEvent} from '../../../../shared/components/smart-grid/types/pagination-change-event';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';

const PAGINATION_URL_PARAMS = ['page', 'pageSize'];

@Component({
    selector: 'zem-deals-library-view',
    templateUrl: './deals-library.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [DealsLibraryStore],
})
export class DealsLibraryView implements OnInit {
    @Input()
    agencyId: string;

    DEFAULT_PAGINATION = {
        page: 1,
        pageSize: 10,
    };

    paginationOptions: PaginationOptions = {
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
        {headerName: 'Accounts', field: 'numOfAccounts'},
        {headerName: 'Campaigns', field: 'numOfCampaigns'},
        {headerName: 'Ad Groups', field: 'numOfAdgroups'},
        {headerName: 'Notes', field: 'description'},
        {headerName: 'Created by', field: 'createdBy'},
    ];

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: DealsLibraryStore,
        @Inject('ajs$location') private ajs$location: any
    ) {}

    ngOnInit() {
        if (commonHelpers.isDefined(this.agencyId)) {
            const preselectedPagination = this.getPreselectedPagination();
            this.paginationOptions = {
                ...this.paginationOptions,
                ...preselectedPagination,
            };
            this.store
                .loadEntities(
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

    onPaginationChange($event: PaginationChangeEvent) {
        this.store
            .loadEntities(this.agencyId, $event.page, $event.pageSize)
            .then(() => {
                this.updateUrlParamsWithSelectedPagination($event);
            });
    }

    private updateUrlParamsWithSelectedPagination(selectedPagination: {
        page: number;
        pageSize: number;
    }) {
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
