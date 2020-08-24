import './operating-system.component.less';

import {
    ChangeDetectionStrategy,
    Component,
    EventEmitter,
    Input,
    OnChanges,
    Output,
} from '@angular/core';
import {TargetOperatingSystem} from '../../../../core/entities/types/common/target-operating-system';
import {OperatingSystem} from './types/operating-system';
import {OperatingSystemVersion} from './types/operating-system-version';
import {OPERATING_SYSTEMS} from '../../entity-manager.config';
import {ChangeEvent} from '../../../../shared/types/change-event';
import {PlatformIcon} from './operating-system.constants';
import {safeGet} from '../../../../shared/helpers/common.helpers';

@Component({
    selector: 'zem-operating-system',
    templateUrl: './operating-system.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OperatingSystemComponent implements OnChanges {
    @Input()
    os: TargetOperatingSystem;
    @Input()
    isDisabled: boolean;
    @Output()
    osChange: EventEmitter<
        ChangeEvent<TargetOperatingSystem>
    > = new EventEmitter<ChangeEvent<TargetOperatingSystem>>();
    @Output()
    osDelete: EventEmitter<void> = new EventEmitter<void>();

    formattedOs: OperatingSystem;
    minVersion: OperatingSystemVersion;
    maxVersion: OperatingSystemVersion;
    platformIcon: PlatformIcon;

    ngOnChanges() {
        this.formattedOs = this.getFormattedOs(this.os.name);
        this.minVersion = this.getFormattedVersion(
            this.formattedOs,
            safeGet(this.os.version, x => x.min)
        );
        this.maxVersion = this.getFormattedVersion(
            this.formattedOs,
            safeGet(this.os.version, x => x.max)
        );
        this.platformIcon = this.getPlatformIcon(this.formattedOs);
    }

    onVersionChanged(versionName: string | null, which: 'min' | 'max') {
        const changes: Partial<TargetOperatingSystem> = {
            version: {...this.os.version},
        };

        if (which === 'min') {
            changes.version.min = versionName || undefined;
        } else {
            changes.version.max = versionName || undefined;
        }
        this.osChange.emit({target: this.os, changes: changes});
    }

    onOsDeleted() {
        this.osDelete.emit();
    }

    private getFormattedOs(osName: string): OperatingSystem {
        return OPERATING_SYSTEMS[osName];
    }

    private getFormattedVersion(
        formattedOs: OperatingSystem,
        versionName: string | undefined
    ): OperatingSystemVersion | undefined {
        let version: OperatingSystemVersion;

        if (formattedOs.versions && versionName) {
            version = formattedOs.versions.find(x => x.name === versionName);
        }

        return version;
    }

    private getPlatformIcon(formattedOs: OperatingSystem): PlatformIcon {
        let platformIcon: PlatformIcon;

        if (formattedOs.deviceTypes.includes('DESKTOP')) {
            platformIcon = PlatformIcon.DESKTOP;
        } else {
            platformIcon = PlatformIcon.TABLET_MOBILE;
        }

        return platformIcon;
    }
}
