import './rule-form-notification.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';
import {RuleNotification} from '../../types/rule-notification';
import {RuleNotificationPolicy} from '../../rule-form.constants';

@Component({
    selector: 'zem-rule-form-notification',
    templateUrl: './rule-form-notification.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RuleFormNotificationComponent {
    @Input()
    ruleNotification: RuleNotification;
    @Output()
    ruleNotificationChange = new EventEmitter<RuleNotification>();

    RuleNotificationPolicy = RuleNotificationPolicy;

    updateRuleNotificationPolicy(policy: RuleNotificationPolicy) {
        this.ruleNotificationChange.emit({
            ...this.ruleNotification,
            policy: policy,
        });
    }

    updateRecipients(recipients: string) {
        this.ruleNotificationChange.emit({
            ...this.ruleNotification,
            recipients: recipients,
        });
    }
}
