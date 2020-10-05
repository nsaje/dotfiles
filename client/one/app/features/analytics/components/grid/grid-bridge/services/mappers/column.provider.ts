import {Type} from '@angular/core';
import {GridColumnTypes} from '../../../../../analytics.constants';
import {ColumnMapper} from './column.mapper';

export abstract class ColumnMapperProvider<
    T1 extends GridColumnTypes,
    T2 extends ColumnMapper
> {
    provide: T1;
    useClass: Type<T2>;
}
