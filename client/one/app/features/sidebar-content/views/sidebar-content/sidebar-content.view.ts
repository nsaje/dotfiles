import './sidebar-content.view.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Inject,
    OnInit,
    OnDestroy,
} from '@angular/core';
import {SidebarContentStore} from '../../services/sidebar-content.store';
import {ListGroupItem} from '../../../../shared/components/list-group/types/list-group-item';
import {ListGroupIcon} from '../../../../shared/components/list-group/list-group.component.constants';
import * as routerHelpers from '../../../../shared/helpers/router.helpers';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {Subject, Observable, merge} from 'rxjs';
import {takeUntil, distinctUntilChanged, tap} from 'rxjs/operators';
import {RoutePathName} from '../../../../app.constants';
import {Router, UrlSerializer} from '@angular/router';

@Component({
    selector: 'zem-sidebar-content-view',
    templateUrl: './sidebar-content.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [SidebarContentStore],
})
export class SidebarContentView implements OnInit, OnDestroy {
    @Input()
    isOpen: boolean;

    items: ListGroupItem[] = [
        {
            value: RoutePathName.DEALS_LIBRARY,
            displayValue: 'Deals Library',
            icon: ListGroupIcon.Folder,
        },
    ];

    selectedItem: RoutePathName | string;
    hasAgencyScope: boolean;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: SidebarContentStore,
        private router: Router,
        private serializer: UrlSerializer,
        @Inject('zemPermissions') public zemPermissions: any
    ) {}

    ngOnInit(): void {
        this.subscribeToStoreStateUpdates();

        const route = routerHelpers.getActivatedRoute(this.router);
        const currentUrlTree = this.serializer.parse(this.router.url);
        this.selectedItem =
            currentUrlTree.root.children.primary.segments[1].path;

        const agencyId = route.snapshot.queryParamMap.get('agencyId');
        const accountId = route.snapshot.queryParamMap.get('accountId');
        if (
            agencyId !== this.store.state.selectedAgencyId ||
            accountId !== this.store.state.selectedAccountId ||
            (accountId === null && agencyId === null)
        ) {
            this.hasAgencyScope = this.zemPermissions.hasAgencyScope(agencyId);
            this.store.setStore(agencyId, accountId);
        }
    }

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    onRoutePathChange(routePathName: RoutePathName) {
        if (routePathName !== this.selectedItem) {
            this.selectedItem = routePathName;
            const route = routerHelpers.getActivatedRoute(this.router);
            this.router.navigate([RoutePathName.APP_BASE, routePathName], {
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
