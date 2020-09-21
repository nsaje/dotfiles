import './connection-type-targeting.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';
import {ConnectionType} from '../../../../app.constants';
import {CONNECTION_TYPE_TARGETING_OPTIONS} from '../../entity-manager.config';

@Component({
    selector: 'zem-connection-type-targeting',
    templateUrl: './connection-type-targeting.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ConnectionTypeTargetingComponent {
    @Input()
    selectedConnectionTypes: ConnectionType[];
    @Input()
    isDisabled: boolean;
    @Output()
    connectionTypeToggle: EventEmitter<ConnectionType> = new EventEmitter<
        ConnectionType
    >();

    connectionTypeOptions = CONNECTION_TYPE_TARGETING_OPTIONS;
}
