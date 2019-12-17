import './rule-edit-form-notification.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';
import {RuleNotificationType} from '../../../../core/rules/rules.constants';
import {FieldErrors} from '../../../../shared/types/field-errors';

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
    @Input()
    notificationTypeErrors: FieldErrors;
    @Input()
    notificationRecipientsErrors: FieldErrors;
    @Output()
    notificationTypeChange = new EventEmitter<RuleNotificationType>();
    @Output()
    notificationRecipientsChange = new EventEmitter<string>();

    RuleNotificationType = RuleNotificationType;

    updateRuleNotificationType(notificationType: RuleNotificationType) {
        this.notificationTypeChange.emit(notificationType);
    }

    updateRecipients(recipients: string) {
        this.notificationRecipientsChange.emit(recipients);
    }
}
