import './ad-group-settings-drawer.view.less';

import {
    Component,
    Input,
    Inject,
    AfterViewInit,
    OnDestroy,
    OnInit,
} from '@angular/core';
import {ENTITY_MANAGER_CONFIG} from '../../entity-manager.config';
import {AdGroupSettingsStore} from '../../services/ad-group-settings-store/ad-group-settings.store';
import {LevelStateParam, EntityType, Currency} from '../../../../app.constants';
import {Subject, merge, Observable} from 'rxjs';
import {takeUntil, map, distinctUntilChanged, tap} from 'rxjs/operators';
import {APP_CONFIG} from '../../../../app.config';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import * as messagesHelpers from '../../helpers/messages.helpers';

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

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: AdGroupSettingsStore,
        @Inject('zemPermissions') public zemPermissions: any,
        @Inject('ajs$state') private ajs$state: any,
        @Inject('ajs$location') private ajs$location: any
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
        setTimeout(() => {
            this.ajs$location
                .search({
                    [ENTITY_MANAGER_CONFIG.settingsQueryParam]: null,
                    [ENTITY_MANAGER_CONFIG.levelQueryParam]: null,
                    [ENTITY_MANAGER_CONFIG.idQueryParam]: null,
                })
                .replace();
        });
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
                this.redirectToParentAnalyticsView(this.newEntityParentId);
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
                this.redirectToNewEntityAnalyticsView(
                    this.store.state.entity.id
                );
            } else {
                this.close();
            }
        }
    }

    async archive() {
        const shouldReload = await this.store.archiveEntity();
        if (shouldReload) {
            this.redirectToNewEntityAnalyticsView(this.store.state.entity.id);
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

    private redirectToNewEntityAnalyticsView(newEntityId: string) {
        this.redirectToEntityAnalyticsView(
            LevelStateParam.AD_GROUP,
            newEntityId
        );
    }

    private redirectToParentAnalyticsView(parentId: string) {
        this.redirectToEntityAnalyticsView(LevelStateParam.CAMPAIGN, parentId);
    }

    private redirectToEntityAnalyticsView(
        level: LevelStateParam,
        entityId: string
    ) {
        const url = this.ajs$state.href('v2.analytics', {
            level: level,
            id: entityId,
        });
        this.ajs$location.url(url);
    }
}
