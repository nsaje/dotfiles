import {
    ContentAdApprovalStatus,
    Emoticon,
} from '../../../../../../app.constants';
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
    value: string | number | SubmissionStatus[];
    popoverMessage?: string;
    url?: string;
    overall?: Emoticon;
    list?: PerformanceItem[];
}

export interface PerformanceItem {
    emoticon: Emoticon;
    text: string;
}

export interface SubmissionStatus {
    name: string;
    status: ContentAdApprovalStatus;
    source_state: string;
    text: string;
    source_link: string;
}
