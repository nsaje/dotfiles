import './daily-budget-setting.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    Output,
    Input,
} from '@angular/core';

@Component({
    selector: 'zem-daily-budget-setting',
    templateUrl: './daily-budget-setting.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DailyBudgetSettingComponent {
    @Input()
    dailyBudget: string;
    @Input()
    isAdGroupAutopilotEnabled: boolean;
    @Input()
    isCampaignAutopilotEnabled: boolean;
    @Input()
    currencySymbol: string;
    @Input()
    errors: string[];
    @Output()
    valueChange = new EventEmitter<string>();
}
