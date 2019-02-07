import {Day} from '../../../../app.constants';

export interface AdGroupDayparting {
    [Day.Sunday]?: number[];
    [Day.Monday]?: number[];
    [Day.Tuesday]?: number[];
    [Day.Wednesday]?: number[];
    [Day.Thursday]?: number[];
    [Day.Friday]?: number[];
    [Day.Saturday]?: number[];
    timezone?: string;
}
