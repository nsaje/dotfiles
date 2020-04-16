import './user-permissions.view.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnInit,
    Inject,
    HostBinding,
    ChangeDetectorRef,
    OnDestroy,
} from '@angular/core';
import {LevelParam, Level} from '../../../../app.constants';
import {
    LEVEL_PARAM_TO_LEVEL_MAP,
    LEVEL_TO_ENTITY_TYPE_MAP,
} from '../../../../app.constants';
import {ActivatedRoute, Params} from '@angular/router';
import {Subject} from 'rxjs';
import {takeUntil} from 'rxjs/operators';

@Component({
    selector: 'zem-user-permissions-view',
    templateUrl: './user-permissions.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class UserPermissionsView implements OnInit, OnDestroy {
    @HostBinding('class')
    cssClass = 'zem-user-permissions-view';

    entity: any;

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
                    params.id
                );
            });
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    updateInternalState(levelParam: LevelParam, entityId: string) {
        const level = this.getLevel(levelParam);

        this.zemNavigationNewService
            .getEntityById(LEVEL_TO_ENTITY_TYPE_MAP[level], entityId)
            .then((entity: any) => {
                this.entity = entity;
                this.changeDetectorRef.markForCheck();
            });
    }

    private getLevel(levelParam: LevelParam): Level {
        return LEVEL_PARAM_TO_LEVEL_MAP[levelParam];
    }
}
