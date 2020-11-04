import {
    ContentAdApprovalStatus,
    Emoticon,
} from '../../../../../../app.constants';
import {BidModifier} from '../../../../../../core/bid-modifiers/types/bid-modifier';
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
    value: string | number | SubmissionStatus[] | BidModifier;
    popoverMessage?: string;
    url?: string;
    text?: string;
    overall?: Emoticon;
    list?: PerformanceItem[];
    image?: string;
    square?: string;
    landscape?: string;
    icon?: string;
    ad_tag?: string;
    editMessage?: string;
    isEditable?: boolean;
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
