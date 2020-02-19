import {TargetRegions} from '../common/target-regions';
import {TargetOperatingSystem} from '../common/target-operating-system';

export interface AdGroupExtrasDefaultSettings {
    targetRegions: TargetRegions;
    exclusionTargetRegions: TargetRegions;
    targetDevices: string[];
    targetOs: TargetOperatingSystem[];
    targetEnvironments: string[];
}
