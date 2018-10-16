import {Day} from '../../../app.constants';

export interface DaypartingSetting {
    [Day.Monday]?: number[];
    [Day.Tuesday]?: number[];
    [Day.Wednesday]?: number[];
    [Day.Thursday]?: number[];
    [Day.Friday]?: number[];
    [Day.Saturday]?: number[];
    [Day.Sunday]?: number[];
    timezone?: string;
}
