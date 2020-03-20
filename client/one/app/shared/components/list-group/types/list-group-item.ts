import {ListGroupIcon} from '../list-group.component.constants';

export interface ListGroupItem {
    value: string;
    displayValue: string;
    icon: ListGroupIcon;
    isVisible: () => boolean;
}
