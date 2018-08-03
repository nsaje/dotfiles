import {HttpParams} from '@angular/common/http';
import {FilterPayload} from './filter-payload';

export interface RequestProperties {
    method: string;
    params: HttpParams;
    body: FilterPayload;
}
