import {Component, OnInit, OnDestroy, ChangeDetectorRef} from '@angular/core';
import {EntityType, RoutePathName} from '../../../../app.constants';
import {ENTITY_MANAGER_CONFIG} from '../../entity-manager.config';
import {ActivatedRoute, Router} from '@angular/router';
import {Subject} from 'rxjs';
import {takeUntil} from 'rxjs/operators';

@Component({
    selector: 'zem-entity-settings-router-outlet',
    templateUrl: './entity-settings.router-outlet.html',
})
// tslint:disable-next-line component-class-suffix
export class EntitySettingsRouterOutlet implements OnInit, OnDestroy {
    readonly EntityType = EntityType;
    entityId: string = null;
    newEntityParentId: string = null;
    entityType: EntityType = null;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        private router: Router,
        private outletRoute: ActivatedRoute,
        private changeDetectorRef: ChangeDetectorRef
    ) {}

    ngOnInit() {
        this.outletRoute.queryParams
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(queryParams => {
                this.entityId = null;
                this.newEntityParentId = null;
                this.entityType = null;

                if (this.router.url.includes(RoutePathName.ANALYTICS)) {
                    this.entityId =
                        queryParams[ENTITY_MANAGER_CONFIG.idQueryParam];
                } else if (
                    this.router.url.includes(
                        RoutePathName.NEW_ENTITY_ANALYTICS_MOCK
                    )
                ) {
                    this.newEntityParentId =
                        queryParams[ENTITY_MANAGER_CONFIG.idQueryParam];
                }

                this.entityType =
                    queryParams[ENTITY_MANAGER_CONFIG.typeQueryParam];

                this.changeDetectorRef.markForCheck();
            });
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }
}
