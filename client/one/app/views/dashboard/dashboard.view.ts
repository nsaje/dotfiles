import './dashboard.view.less';

import {
    Component,
    ChangeDetectionStrategy,
    HostBinding,
    AfterViewInit,
    Inject,
} from '@angular/core';

@Component({
    selector: 'zem-dashboard-view',
    templateUrl: './dashboard.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DashboardView implements AfterViewInit {
    @HostBinding('class')
    cssClass = 'zem-dashboard-view';

    constructor(
        @Inject('zemDesignHelpersService') private zemDesignHelpersService: any
    ) {}

    ngAfterViewInit(): void {
        this.zemDesignHelpersService.init();
    }
}
