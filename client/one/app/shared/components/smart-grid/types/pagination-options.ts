import {PageSizeConfig} from './page-size-config';

export interface PaginationOptions {
    type: 'client' | 'server';
    page?: number;
    pageSize?: number;
    pageSizeOptions?: PageSizeConfig[];
}
