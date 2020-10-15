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
    id?: GridRowDataStatsValue;
    [key: string]: GridRowDataStatsValue;
}

export interface GridRowDataStatsValue {
    value: string | number;
}
