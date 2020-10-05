import {GridBody} from './grid-body';
import {GridFooter} from './grid-footer';
import {GridHeader} from './grid-header';
import {GridMeta} from './grid-meta';

export interface Grid {
    header: GridHeader;
    body: GridBody;
    footer: GridFooter;
    meta: GridMeta;
}
