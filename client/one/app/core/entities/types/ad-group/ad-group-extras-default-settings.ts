import {TargetRegions} from '../common/target-regions';
import {OperatingSystem} from '../common/operating-system';

export interface AdGroupExtrasDefaultSettings {
    targetRegions: TargetRegions;
    exclusionTargetRegions: TargetRegions;
    targetDevices: string[];
    targetOs: OperatingSystem[];
    targetPlacements: string[];
}
