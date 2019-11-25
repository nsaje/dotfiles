import './rule-edit-form-notification.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';
import {RuleNotificationType} from '../../../../core/rules/rules.constants';

@Component({
    selector: 'zem-rule-edit-form-notification',
    templateUrl: './rule-edit-form-notification.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RuleEditFormNotificationComponent {
    @Input()
    notificationType: RuleNotificationType;
    @Input()
    notificationRecipients: string;
    @Output()
    notificationTypeChange = new EventEmitter<RuleNotificationType>();
    @Output()
    notificationRecipientsChange = new EventEmitter<string[]>();

    RuleNotificationType = RuleNotificationType;

    updateRuleNotificationType(notificationType: RuleNotificationType) {
        this.notificationTypeChange.emit(notificationType);
    }

    updateRecipients(recipients: string) {
        let recipientsList: string[] = [];
        if (recipients.length > 0) {
            recipientsList = recipients.split(',');
        }
        this.notificationRecipientsChange.emit(recipientsList);
    }
}
