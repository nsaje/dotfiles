import {Emoticon} from '../../../../../../app.constants';
import {GridRowEntity} from './grid-row-entity';

export interface GridRowData {
    archived?: boolean;
    breakdownId?: string;
    breakdown?: any;
    entity?: GridRowEntity;
    group?: boolean;
    stats: GridRowDataStats;
}

export interface GridRowDataStats {
    [key: string]: GridRowDataStatsValue;
}

export interface GridRowDataStatsValue {
    value: string | number;
    popoverMessage?: string;
    url?: string;
    overall?: Emoticon;
    list?: PerformanceItem[];
}

export interface PerformanceItem {
    emoticon: Emoticon;
    text: string;
}
