import './operating-system-list.component.less';
import {
    ChangeDetectionStrategy,
    Component,
    ContentChild,
    EventEmitter,
    Input,
    OnChanges,
    Output,
    TemplateRef,
    ViewChild,
} from '@angular/core';
import {TargetOperatingSystem} from '../../../../core/entities/types/common/target-operating-system';
import {OperatingSystem} from '../operating-system/types/operating-system';
import {DeviceType} from '../operating-system/types/device-type';
import * as arrayHelpers from '../../../../shared/helpers/array.helpers';
import {DropdownDirective} from '../../../../shared/components/dropdown/dropdown.directive';
import {OPERATING_SYSTEMS} from '../../entity-manager.config';

@Component({
    selector: 'zem-operating-system-list',
    templateUrl: './operating-system-list.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OperatingSystemListComponent implements OnChanges {
    @Input()
    oses: TargetOperatingSystem[];
    @Input()
    devices: DeviceType[];
    @Input()
    isDisabled: boolean;
    @Output()
    osAdded: EventEmitter<String> = new EventEmitter<String>();

    @ContentChild('osItemTemplate', {read: TemplateRef, static: false})
    osItemTemplate: TemplateRef<any>;

    @ViewChild('addOsDropdown', {static: false})
    addOsDropdown: DropdownDirective;

    filteredOses: OperatingSystem[] = [];

    ngOnChanges() {
        this.filteredOses = this.getFilteredOses();
    }

    addOs(os: OperatingSystem) {
        this.osAdded.emit(os.name);
        this.addOsDropdown.close();
    }

    private getFilteredOses(): OperatingSystem[] {
        // Allow OS to be selected if it is not selected yet and if appropriate device types are selected which support it
        return Object.values(OPERATING_SYSTEMS).filter(
            osType =>
                !this.oses.map(os => os.name).includes(osType.name) &&
                arrayHelpers.includesAny(osType.deviceTypes, this.devices)
        );
    }
}
