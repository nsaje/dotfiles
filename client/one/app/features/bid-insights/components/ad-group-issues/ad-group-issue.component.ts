import './ad-group-issue.component.less';

import {
    Component,
    Input,
    ChangeDetectionStrategy,
    HostBinding,
    OnChanges,
} from '@angular/core';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {
    ELIGIBILITY_OK_LIMIT,
    ELIGIBILITY_PROBLEM_LIMIT,
} from './ad-group-issue.component.config';

@Component({
    selector: 'zem-ad-group-issue',
    templateUrl: './ad-group-issue.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AdGroupIssueComponent implements OnChanges {
    @Input()
    issueText: string;
    @Input()
    eligibleRate: number;

    @HostBinding('class.zem-ad-group-issue--green') get green() {
        return this.eligibleRate >= ELIGIBILITY_OK_LIMIT;
    }
    @HostBinding('class.zem-ad-group-issue--orange') get orange() {
        return (
            this.eligibleRate >= ELIGIBILITY_PROBLEM_LIMIT &&
            this.eligibleRate < ELIGIBILITY_OK_LIMIT - 1
        );
    }
    @HostBinding('class.zem-ad-group-issue--red') get red() {
        return (
            commonHelpers.isDefined(this.eligibleRate) &&
            this.eligibleRate < ELIGIBILITY_PROBLEM_LIMIT
        );
    }
    @HostBinding('class.zem-ad-group-issue--grey') get grey() {
        return !commonHelpers.isDefined(this.eligibleRate);
    }

    lostRate: number;
    showArrow: boolean;

    ngOnChanges() {
        this.lostRate = 100 - this.eligibleRate;
        this.showArrow = commonHelpers.isDefined(this.eligibleRate);
    }
}
