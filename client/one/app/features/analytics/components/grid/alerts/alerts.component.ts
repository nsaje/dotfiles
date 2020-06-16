import './alerts.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    OnChanges,
    SimpleChanges,
} from '@angular/core';
import {Alert} from '../../../../../core/alerts/types/alert';
import {AlertType} from '../../../../../app.constants';
import {AlertStyleClass} from '../../../../../shared/components/alert/alert.component.constants';

const ALERT_TYPE_TO_ALERT_STYLE_CLASS = {
    [AlertType.INFO]: AlertStyleClass.Info,
    [AlertType.SUCCESS]: AlertStyleClass.Success,
    [AlertType.DANGER]: AlertStyleClass.Error,
    [AlertType.WARNING]: AlertStyleClass.Warning,
};

interface FormattedAlert {
    styleClass: AlertStyleClass;
    alert: Alert;
}

@Component({
    selector: 'zem-alerts',
    templateUrl: './alerts.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AlertsComponent implements OnChanges {
    @Input()
    alerts: Alert[];
    @Output()
    closeAlert = new EventEmitter<Alert>();

    formattedAlerts: FormattedAlert[] = [];

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.alerts) {
            this.formattedAlerts = this.getFormattedAlerts(this.alerts);
        }
    }

    trackByIndex(index: number): string {
        return index.toString();
    }

    private getFormattedAlerts(alerts: Alert[]): FormattedAlert[] {
        return (alerts || []).map(alert => {
            return {
                styleClass: ALERT_TYPE_TO_ALERT_STYLE_CLASS[alert.type],
                alert: alert,
            };
        });
    }
}
