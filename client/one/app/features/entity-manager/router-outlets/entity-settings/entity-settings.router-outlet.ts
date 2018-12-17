import {Component, Inject, OnInit} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import {EntityType} from '../../../../app.constants';
import {ENTITY_MANAGER_CONFIG} from '../../entity-manager.config';

@Component({
    selector: 'zem-entity-settings-router-outlet',
    templateUrl: './entity-settings.router-outlet.html',
})
// tslint:disable-next-line component-class-suffix
export class EntitySettingsRouterOutlet implements OnInit {
    readonly EntityType = EntityType;
    entityId: number = null;
    entityType: EntityType = null;

    constructor(
        @Inject('ajs$rootScope') private ajs$rootScope: any,
        @Inject('ajs$location') private ajs$location: any,
        @Inject('ajs$state') private ajs$state: any,
        @Inject('zemPermissions') private zemPermissions: any
    ) {}

    ngOnInit() {
        if (
            !this.zemPermissions.hasPermission(
                'zemauth.can_use_new_entity_settings_drawers'
            )
        ) {
            return;
        }
        this.updateActiveSettingsEntity();
        this.ajs$rootScope.$on('$zemStateChangeSuccess', () => {
            this.updateActiveSettingsEntity();
        });
        this.ajs$rootScope.$on('$locationChangeSuccess', () => {
            this.updateActiveSettingsEntity();
        });
    }

    private updateActiveSettingsEntity() {
        if (
            this.ajs$state.includes('v2.analytics') &&
            this.isSettingsQueryParamSet()
        ) {
            this.entityId = this.ajs$state.params[
                ENTITY_MANAGER_CONFIG.idStateParam
            ];
            this.entityType = this.getEntityTypeFromStateParams();
        } else {
            this.entityId = null;
            this.entityType = null;
        }
    }

    private isSettingsQueryParamSet(): boolean {
        return this.ajs$location.search()[
            ENTITY_MANAGER_CONFIG.settingsQueryParam
        ];
    }

    private getEntityTypeFromStateParams(): EntityType {
        return ENTITY_MANAGER_CONFIG.levelToEntityTypeMap[
            this.ajs$state.params[ENTITY_MANAGER_CONFIG.levelStateParam]
        ];
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemEntitySettingsRouterOutlet',
    downgradeComponent({
        component: EntitySettingsRouterOutlet,
    })
);
