import {Item} from './item';

export interface Category {
    name: string;
    key: string;
    items: Item[];
}
