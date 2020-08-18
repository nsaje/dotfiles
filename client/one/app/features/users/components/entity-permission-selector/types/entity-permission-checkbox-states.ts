import {DisplayedEntityPermissionValue} from '../../../types/displayed-entity-permission-value';

export type EntityPermissionCheckboxStates = {
    [key in DisplayedEntityPermissionValue]?: 'enabled' | 'disabled' | 'hidden';
};
