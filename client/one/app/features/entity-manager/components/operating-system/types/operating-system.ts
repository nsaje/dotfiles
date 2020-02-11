import {OperatingSystemVersion} from './operating-system-version';
import {DeviceType} from './device-type';
import {OperatingSystemIcon} from '../operating-system.constants';

export interface OperatingSystem {
    deviceTypes: DeviceType[];
    name: string;
    displayName: string;
    icon: OperatingSystemIcon;
    versions: OperatingSystemVersion[] | null;
}
