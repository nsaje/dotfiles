import './analytics.view.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnInit,
    OnDestroy,
    Inject,
    HostBinding,
    ChangeDetectorRef,
} from '@angular/core';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {
    Breakdown,
    Level,
    LevelParam,
    BreakdownParam,
} from '../../../../app.constants';
import {
    DEFAULT_BREAKDOWN,
    BREAKDOWN_STATE_PARAM_TO_BREAKDOWN_MAP,
} from '../../analytics.config';
import {
    LEVEL_PARAM_TO_LEVEL_MAP,
    LEVEL_TO_ENTITY_TYPE_MAP,
} from '../../../../app.constants';
import {ActivatedRoute, Params} from '@angular/router';
import {takeUntil} from 'rxjs/operators';
import {Subject} from 'rxjs';

@Component({
    selector: 'zem-analytics-view',
    templateUrl: './analytics.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AnalyticsView implements OnInit, OnDestroy {
    @HostBinding('class')
    cssClass = 'zem-analytics-view';

    level: Level;
    breakdown: Breakdown;
    chartBreakdown: Breakdown;
    entity: any;
    isInitialized: boolean = false;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        private route: ActivatedRoute,
        private changeDetectorRef: ChangeDetectorRef,
        @Inject('zemNavigationNewService') private zemNavigationNewService: any
    ) {}

    ngOnInit(): void {
        this.route.params
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe((params: Params) => {
                this.updateInternalState(
                    this.route.snapshot.data.level,
                    params.id,
                    params.breakdown
                );
            });
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    updateInternalState(
        levelParam: LevelParam,
        entityId: string | null,
        breakdownParam: BreakdownParam | null
    ) {
        this.level = this.getLevel(levelParam);
        this.breakdown = this.getBreakdown(this.level, breakdownParam);
        this.chartBreakdown = this.getChartBreakdown(
            this.level,
            this.breakdown
        );

        if (!commonHelpers.isDefined(entityId)) {
            this.entity = null;
            this.isInitialized = true;
            this.changeDetectorRef.markForCheck();
            return;
        }

        this.zemNavigationNewService
            .getEntityById(LEVEL_TO_ENTITY_TYPE_MAP[this.level], entityId)
            .then((entity: any) => {
                if (
                    !commonHelpers.isDefined(this.entity) ||
                    this.entity.id !== entity.id
                ) {
                    this.entity = entity;
                }

                this.isInitialized = true;
                this.changeDetectorRef.markForCheck();
            });
    }

    private getLevel(levelParam: LevelParam): Level {
        return LEVEL_PARAM_TO_LEVEL_MAP[levelParam];
    }

    private getBreakdown(
        level: Level,
        breakdownParam: BreakdownParam | null
    ): Breakdown {
        const breakdown =
            BREAKDOWN_STATE_PARAM_TO_BREAKDOWN_MAP[breakdownParam];
        if (commonHelpers.isDefined(breakdown)) {
            return breakdown;
        }
        return DEFAULT_BREAKDOWN[level];
    }

    private getChartBreakdown(level: Level, breakdown: Breakdown): Breakdown {
        return breakdown === Breakdown.INSIGHTS
            ? DEFAULT_BREAKDOWN[level]
            : breakdown;
    }
}
