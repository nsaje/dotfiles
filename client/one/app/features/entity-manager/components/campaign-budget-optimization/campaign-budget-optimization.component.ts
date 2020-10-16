import './campaign-budget-optimization.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';

@Component({
    selector: 'zem-campaign-budget-optimization',
    templateUrl: './campaign-budget-optimization.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CampaignBudgetOptimizationComponent {
    @Input()
    autopilot: boolean;
    @Input()
    isDisabled: boolean;
    @Input()
    agencyUsesRealtimeAutopilot: boolean;
    @Output()
    autopilotChange = new EventEmitter<boolean>();
}
