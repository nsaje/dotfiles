import {HttpParams} from '@angular/common/http';

export interface RequestProperties {
    method: string;
    params: HttpParams;
    body: any;
}
