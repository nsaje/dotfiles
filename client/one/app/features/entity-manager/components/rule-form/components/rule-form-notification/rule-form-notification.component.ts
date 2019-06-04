import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    OnChanges,
    SimpleChanges,
} from '@angular/core';
import * as clone from 'clone';
import {RuleNotification} from '../../types/rule-notification';
import {RuleNotificationType} from '../../rule-form.constants';

@Component({
    selector: 'zem-rule-form-notification',
    templateUrl: './rule-form-notification.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RuleFormNotificationComponent implements OnChanges {
    @Input()
    value: RuleNotification;
    @Output()
    valueChange = new EventEmitter<RuleNotification>();

    model: RuleNotification = {};
    RuleNotificationType = RuleNotificationType;

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.value) {
            this.model = clone(this.value);
        }
    }

    setType(type: RuleNotificationType) {
        this.model.type = type;
        this.valueChange.emit(clone(this.model));
    }

    setRecipients(recipients: string) {
        this.model.recipients = recipients;
        this.valueChange.emit(clone(this.model));
    }
}
