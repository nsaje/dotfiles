import './sidebar-content.view.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Inject,
    OnInit,
    OnDestroy,
    OnChanges,
    SimpleChanges,
} from '@angular/core';
import {SidebarContentStore} from '../../services/sidebar-content.store';
import {ListGroupItem} from '../../../../shared/components/list-group/types/list-group-item';
import {ListGroupIcon} from '../../../../shared/components/list-group/list-group.component.constants';
import * as routerHelpers from '../../../../shared/helpers/router.helpers';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {Subject, Observable, merge} from 'rxjs';
import {takeUntil, distinctUntilChanged, tap, filter} from 'rxjs/operators';
import {RoutePathName} from '../../../../app.constants';
import {Router} from '@angular/router';

@Component({
    selector: 'zem-sidebar-content-view',
    templateUrl: './sidebar-content.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [SidebarContentStore],
})
export class SidebarContentView implements OnInit, OnChanges, OnDestroy {
    @Input()
    routePathName: RoutePathName;
    @Input()
    isOpen: boolean;

    items: ListGroupItem[] = [
        {
            value: RoutePathName.CREDITS,
            displayValue: 'Credits',
            icon: ListGroupIcon.Credit,
            isVisible: () => {
                return this.zemPermissions.hasPermission(
                    'zemauth.account_credit_view'
                );
            },
        },
        {
            value: RoutePathName.DEALS,
            displayValue: 'Deals',
            icon: ListGroupIcon.Folder,
            isVisible: () => {
                return this.zemPermissions.hasPermission(
                    'zemauth.can_see_deals_library'
                );
            },
        },
        {
            value: RoutePathName.PUBLISHER_GROUPS_LIBRARY,
            displayValue: 'Publisher Groups',
            icon: ListGroupIcon.PublisherGroups,
            isVisible: () => {
                return (
                    this.zemPermissions.hasPermission(
                        'zemauth.can_see_publisher_groups_ui'
                    ) &&
                    this.zemPermissions.hasPermission(
                        'zemauth.can_edit_publisher_groups'
                    )
                );
            },
        },
    ];

    hasAgencyScope: boolean;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: SidebarContentStore,
        private router: Router,
        @Inject('zemPermissions') public zemPermissions: any
    ) {}

    ngOnInit(): void {
        this.subscribeToStoreStateUpdates();
    }

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.routePathName) {
            const route = routerHelpers.getActivatedRoute(this.router);
            const agencyId = route.snapshot.queryParamMap.get('agencyId');
            const accountId = route.snapshot.queryParamMap.get('accountId');
            if (
                agencyId !== this.store.state.selectedAgencyId ||
                accountId !== this.store.state.selectedAccountId ||
                (accountId === null && agencyId === null)
            ) {
                this.hasAgencyScope = this.zemPermissions.hasAgencyScope(
                    agencyId
                );
                this.store.setStore(agencyId, accountId);
            }
        }
    }

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    onRoutePathChange($event: RoutePathName) {
        if (this.routePathName !== $event) {
            const route = routerHelpers.getActivatedRoute(this.router);
            this.router.navigate([RoutePathName.APP_BASE, $event], {
                queryParams: commonHelpers.getValueWithOnlyProps(
                    route.snapshot.queryParams,
                    ['agencyId', 'accountId']
                ),
            });
        }
    }

    private subscribeToStoreStateUpdates() {
        merge(this.stateUpdater$())
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe();
    }

    private stateUpdater$(): Observable<any> {
        return this.store.state$.pipe(
            filter(
                state =>
                    commonHelpers.isDefined(state.selectedAgencyId) ||
                    commonHelpers.isDefined(state.selectedAccountId)
            ),
            distinctUntilChanged(),
            tap(state => {
                const route = routerHelpers.getActivatedRoute(this.router);
                this.hasAgencyScope = this.zemPermissions.hasAgencyScope(
                    state.selectedAgencyId
                );

                this.router.navigate([], {
                    relativeTo: route,
                    queryParams: {
                        agencyId: state.selectedAgencyId,
                        accountId: state.selectedAccountId,
                    },
                    queryParamsHandling: 'merge',
                    replaceUrl: true,
                });
            })
        );
    }
}
