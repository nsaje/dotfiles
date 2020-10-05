import {GridRowLevel, GridRowType} from '../../../../analytics.constants';
import {GridRowData} from './grid-row-data';
import {GridRowEntity} from './grid-row-entity';

export interface GridRow {
    id: string; // Row id
    type: GridRowType; // Type of a row (STATS, BREAKDOWN)
    entity: GridRowEntity; // Which entity's stats does row display (account, campaign, ad_group, content_ad)
    data: GridRowData; // Data that corresponds to this row (stats or breakdown object - see DataSource)
    level: GridRowLevel; // Level of data in breakdown tree which this row represents
    parent: GridRow; // Parent row - row on which breakdown has been made
    collapsed: boolean; // Collapse flag used by collapsing feature
    visible: boolean; // Visibility flag - row can be hidden for different reasons (e.g. collapsed parent)
}
