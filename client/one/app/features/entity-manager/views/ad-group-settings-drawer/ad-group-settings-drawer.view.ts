import './ad-group-settings-drawer.view.less';

import {
    AfterViewInit,
    Component,
    Inject,
    Input,
    OnDestroy,
    OnInit,
} from '@angular/core';
import {
    TARGETING_DEVICE_OPTIONS,
    TARGETING_ENVIRONMENT_OPTIONS,
    ENTITY_MANAGER_CONFIG,
} from '../../entity-manager.config';
import {AdGroupSettingsStore} from '../../services/ad-group-settings-store/ad-group-settings.store';
import {
    Currency,
    EntityType,
    LevelParam,
    RoutePathName,
} from '../../../../app.constants';
import {merge, Observable, Subject} from 'rxjs';
import {distinctUntilChanged, map, takeUntil, tap} from 'rxjs/operators';
import {APP_CONFIG} from '../../../../app.config';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import * as messagesHelpers from '../../helpers/messages.helpers';
import * as arrayHelpers from '../../../../shared/helpers/array.helpers';
import {ImageCheckboxInputGroupItem} from '../../../../shared/components/image-checkbox-input-group/types/image-checkbox-input-group-item';
import {Router} from '@angular/router';

@Component({
    selector: 'zem-ad-group-settings-drawer',
    templateUrl: './ad-group-settings-drawer.view.html',
    providers: [AdGroupSettingsStore],
})
export class AdGroupSettingsDrawerView
    implements OnInit, AfterViewInit, OnDestroy {
    @Input()
    entityId: string;
    @Input()
    newEntityParentId: string;

    EntityType = EntityType;

    isOpen = false;
    isNewEntity = false;
    minEndDate = new Date();
    currencySymbol = '';

    targetingDeviceOptions: ImageCheckboxInputGroupItem[] = TARGETING_DEVICE_OPTIONS;
    targetingEnvironmentOptions: ImageCheckboxInputGroupItem[] = TARGETING_ENVIRONMENT_OPTIONS;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: AdGroupSettingsStore,
        private router: Router,
        @Inject('zemPermissions') public zemPermissions: any
    ) {}

    ngOnInit() {
        this.isNewEntity = !this.entityId;

        this.subscribeToStateUpdates();
    }

    ngAfterViewInit() {
        if (this.isNewEntity) {
            this.store.loadEntityDefaults(this.newEntityParentId);
        } else {
            this.store.loadEntity(this.entityId);
        }

        setTimeout(() => {
            this.open();
        });
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    open() {
        this.isOpen = true;
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
                    LevelParam.CAMPAIGN,
                    this.newEntityParentId,
                ]);
            } else {
                this.close();
            }
        }
    }

    doesAnySettingHaveValue(...values: any[]): boolean {
        if (!commonHelpers.isDefined(values) || values.length < 1) {
            return false;
        }
        let settingHasValue = false;
        for (const value of values) {
            if (commonHelpers.isNotEmpty(value)) {
                settingHasValue = true;
                break;
            }
        }
        return settingHasValue;
    }

    async saveSettings() {
        const shouldCloseDrawer = await this.store.saveEntity();
        if (shouldCloseDrawer) {
            if (this.isNewEntity) {
                this.navigateToRoute([
                    RoutePathName.APP_BASE,
                    RoutePathName.ANALYTICS,
                    LevelParam.AD_GROUP,
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
                LevelParam.AD_GROUP,
                this.store.state.entity.id,
            ]);
        }
    }

    private subscribeToStateUpdates() {
        merge(this.createCurrencySymbolUpdater$())
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe();
    }

    private createCurrencySymbolUpdater$(): Observable<Currency> {
        return this.store.state$.pipe(
            map(state => state.extras.currency),
            distinctUntilChanged(),
            tap(currency => {
                this.currencySymbol = APP_CONFIG.currencySymbols[currency];
            })
        );
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
}
