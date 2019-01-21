import './ad-group-settings-drawer.view.less';

import {Component, Input, Inject, AfterViewInit} from '@angular/core';
import {ENTITY_MANAGER_CONFIG} from '../../entity-manager.config';
import {AdGroupSettingsStore} from '../../services/ad-group-settings.store';

@Component({
    selector: 'zem-ad-group-settings-drawer',
    templateUrl: './ad-group-settings-drawer.view.html',
    providers: [AdGroupSettingsStore],
})
export class AdGroupSettingsDrawerView implements AfterViewInit {
    @Input()
    entityId: number;

    isOpen: boolean;

    constructor(
        public store: AdGroupSettingsStore,
        @Inject('ajs$location') private ajs$location: any
    ) {}

    ngAfterViewInit() {
        this.store.loadSettings(this.entityId);

        setTimeout(() => {
            this.open();
        });
    }

    open() {
        this.isOpen = true;
    }

    close() {
        this.isOpen = false;
        setTimeout(() => {
            this.ajs$location
                .search(ENTITY_MANAGER_CONFIG.settingsQueryParam, null)
                .replace();
        }, 250);
    }

    async saveSettings() {
        const shouldCloseDrawer = await this.store.saveSettings();
        if (shouldCloseDrawer) {
            this.close();
        }
    }

    async archive() {
        const shouldCloseDrawer = await this.store.archiveEntity();
        if (shouldCloseDrawer) {
            this.close();
        }
    }
}
