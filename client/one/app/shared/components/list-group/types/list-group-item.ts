import {ListGroupItemIcon} from '../components/list-group-item/list-group-item.component.constants';

export interface ListGroupItem {
    value: string;
    displayValue: string;
    icon?: ListGroupItemIcon;
    isVisible: () => boolean;
    isNewFeature?: boolean;
    subItems?: ListGroupItem[];
}
