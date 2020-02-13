import './archived.view.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnInit,
    OnDestroy,
    Inject,
    HostBinding,
    ChangeDetectorRef,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {LevelStateParam, Level} from '../../../../app.constants';
import {
    LEVEL_STATE_PARAM_TO_LEVEL_MAP,
    LEVEL_TO_ENTITY_TYPE_MAP,
} from '../../analytics.config';

@Component({
    selector: 'zem-archived-view',
    templateUrl: './archived.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ArchivedView implements OnInit, OnDestroy {
    @HostBinding('class')
    cssClass = 'zem-archived-view';

    entity: any;

    private stateChangeListener$: Function;

    constructor(
        private changeDetectorRef: ChangeDetectorRef,
        @Inject('ajs$rootScope') private ajs$rootScope: any,
        @Inject('ajs$state') private ajs$state: any,
        @Inject('zemPermissions') public zemPermissions: any,
        @Inject('zemNavigationNewService') private zemNavigationNewService: any
    ) {}

    ngOnInit(): void {
        this.updateInternalState();
        this.stateChangeListener$ = this.ajs$rootScope.$on(
            '$zemStateChangeSuccess',
            () => {
                this.updateInternalState();
            }
        );
    }

    ngOnDestroy(): void {
        if (commonHelpers.isDefined(this.stateChangeListener$)) {
            this.stateChangeListener$();
        }
    }

    updateInternalState() {
        const level = this.getLevel(this.ajs$state.params.level);
        if (!commonHelpers.isDefined(level)) {
            this.entity = null;
            this.changeDetectorRef.markForCheck();
            return;
        }

        const entityId = this.ajs$state.params.id;
        if (!commonHelpers.isDefined(entityId)) {
            this.entity = null;
            this.changeDetectorRef.markForCheck();
            return;
        }

        this.zemNavigationNewService
            .getEntityById(LEVEL_TO_ENTITY_TYPE_MAP[level], entityId)
            .then((entity: any) => {
                this.entity = entity;
                this.changeDetectorRef.markForCheck();
            });
    }

    private getLevel(levelStateParam: LevelStateParam): Level {
        return LEVEL_STATE_PARAM_TO_LEVEL_MAP[levelStateParam];
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemArchivedView',
    downgradeComponent({
        component: ArchivedView,
        propagateDigest: false,
    })
);
