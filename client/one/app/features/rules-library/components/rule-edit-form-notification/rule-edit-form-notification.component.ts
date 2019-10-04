import './rule-edit-form-notification.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';
import {RuleNotification} from '../../types/rule-notification';
import {RuleNotificationPolicy} from '../../rules-library.constants';

@Component({
    selector: 'zem-rule-edit-form-notification',
    templateUrl: './rule-edit-form-notification.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RuleEditFormNotificationComponent {
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
