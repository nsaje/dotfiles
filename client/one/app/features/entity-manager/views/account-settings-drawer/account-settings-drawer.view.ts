import './account-settings-drawer.view.less';

import {
    Component,
    Input,
    Inject,
    AfterViewInit,
    OnInit,
    OnDestroy,
    ChangeDetectorRef,
} from '@angular/core';
import {
    ACCOUNT_TYPES,
    ENTITY_MANAGER_CONFIG,
} from '../../entity-manager.config';
import {CURRENCIES} from '../../../../app.config';
import {AccountSettingsStore} from '../../services/account-settings-store/account-settings.store';
import {Subject, merge, Observable} from 'rxjs';
import * as messagesHelpers from '../../helpers/messages.helpers';
import {LevelParam, EntityType, RoutePathName} from '../../../../app.constants';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import * as arrayHelpers from '../../../../shared/helpers/array.helpers';
import {takeUntil, map, distinctUntilChanged, tap} from 'rxjs/operators';
import {Router} from '@angular/router';

@Component({
    selector: 'zem-account-settings-drawer',
    templateUrl: './account-settings-drawer.view.html',
    providers: [AccountSettingsStore],
})
export class AccountSettingsDrawerView
    implements OnInit, OnDestroy, AfterViewInit {
    @Input()
    entityId: string;

    EntityType = EntityType;
    ACCOUNT_TYPES = ACCOUNT_TYPES;
    CURRENCIES = CURRENCIES;

    isOpen: boolean;
    isNewEntity: boolean;
    isDefaultIconPreviewVisible: boolean;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: AccountSettingsStore,
        private router: Router,
        private changeDetectorRef: ChangeDetectorRef,
        @Inject('zemPermissions') public zemPermissions: any
    ) {}

    ngOnInit(): void {
        this.isNewEntity = !this.entityId;
        this.subscribeToStateUpdates();
    }

    ngAfterViewInit() {
        setTimeout(() => {
            this.open();
            if (this.isNewEntity) {
                this.store.loadEntityDefaults();
            } else {
                this.store.loadEntity(this.entityId);
            }
        }, 250);
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    open() {
        this.isOpen = true;
        this.changeDetectorRef.detectChanges();
    }

    close() {
        this.isOpen = false;
        this.navigateToRoute([]);
    }

    cancel() {
        let shouldCloseDrawer = true;
        if (this.store.doEntitySettingsHaveUnsavedChanges()) {
            shouldCloseDrawer = confirm(
                messagesHelpers.getClosingUnsavedChangesConfirmMessage()
            );
        }
        if (shouldCloseDrawer) {
            if (this.isNewEntity) {
                this.navigateToRoute([
                    RoutePathName.APP_BASE,
                    RoutePathName.ANALYTICS,
                    LevelParam.ACCOUNTS,
                ]);
            } else {
                this.close();
            }
        }
    }

    toggleDefaultIconPreview() {
        this.isDefaultIconPreviewVisible = !this.isDefaultIconPreviewVisible;
    }

    async saveSettings() {
        const shouldCloseDrawer = await this.store.saveEntity();
        if (shouldCloseDrawer) {
            if (this.isNewEntity) {
                this.navigateToRoute([
                    RoutePathName.APP_BASE,
                    RoutePathName.ANALYTICS,
                    LevelParam.ACCOUNT,
                    this.store.state.entity.id,
                ]);
            } else {
                this.close();
            }
        }
    }

    async archive() {
        const shouldReload = await this.store.archiveEntity();
        if (shouldReload) {
            this.navigateToRoute([
                RoutePathName.APP_BASE,
                RoutePathName.ARCHIVED,
                LevelParam.ACCOUNT,
                this.store.state.entity.id,
            ]);
        }
    }

    private navigateToRoute(routePath: string[]) {
        this.isOpen = false;
        this.router
            .navigate(
                [
                    {
                        outlets: {drawer: null},
                    },
                ],
                {
                    queryParams: commonHelpers.getValueWithoutProps(
                        this.router.routerState.root.snapshot.queryParams,
                        [
                            ENTITY_MANAGER_CONFIG.idQueryParam,
                            ENTITY_MANAGER_CONFIG.typeQueryParam,
                        ]
                    ),
                }
            )
            .then(() => {
                if (!arrayHelpers.isEmpty(routePath)) {
                    this.router.navigate(routePath, {
                        queryParamsHandling: 'preserve',
                    });
                }
            });
    }

    private subscribeToStateUpdates() {
        merge(this.createDefaultIconPreviewUpdater$())
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe();
    }

    private createDefaultIconPreviewUpdater$(): Observable<string> {
        return this.store.state$.pipe(
            map(state => state.entity.defaultIconUrl),
            distinctUntilChanged(),
            tap(defaultIconUrl => {
                this.isDefaultIconPreviewVisible = commonHelpers.isDefined(
                    defaultIconUrl
                );
            })
        );
    }
}
