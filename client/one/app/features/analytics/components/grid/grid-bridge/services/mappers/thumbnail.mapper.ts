import {SmartGridColDef} from '../../../../../../../shared/components/smart-grid/types/smart-grid-col-def';
import {ValueFormatterParams} from 'ag-grid-community';
import {GridColumnTypes} from '../../../../../analytics.constants';
import {THUMBNAIL_COLUMN_WIDTH} from '../../grid-bridge.component.constants';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {ColumnMapper} from './column.mapper';
import {ThumbnailData} from '../../../../../../../shared/components/thumbnail-cell/types/thumbnail-data';
import {GridRow} from '../../types/grid-row';
import {
    GridRowDataStats,
    GridRowDataStatsValue,
    SubmissionStatus,
} from '../../types/grid-row-data';
import {AdType} from '../../../../../../../app.constants';
import {APP_OPTIONS} from '../../../../../../../app.options';
import {ThumbnailCellComponent} from '../../../../../../../shared/components/thumbnail-cell/thumbnail-cell.component';
import {
    DEFAULT_CREATIVE_HEIGHT,
    DEFAULT_CREATIVE_WIDTH,
} from '../../../../../../../shared/components/thumbnail-cell/thumbnail-cell.component.constants';
import {
    getValueOrDefault,
    isDefined,
} from '../../../../../../../shared/helpers/common.helpers';

export class ThumbnailColumnMapper extends ColumnMapper {
    getColDef(grid: Grid, column: GridColumn): SmartGridColDef {
        return {
            colId: GridColumnTypes.THUMBNAIL,
            minWidth: THUMBNAIL_COLUMN_WIDTH,
            width: THUMBNAIL_COLUMN_WIDTH,
            cellRendererFramework: ThumbnailCellComponent,
            valueGetter: getThumbnailDataFromGridRow,
            valueFormatter: (params: ValueFormatterParams) => {
                return '';
            },
            pinnedRowValueFormatter: (params: ValueFormatterParams) => {
                return '';
            },
        };
    }
}

function getThumbnailDataFromGridRow(params: {data: GridRow}): ThumbnailData {
    const stats: GridRowDataStats = params.data.data.stats as GridRowDataStats;

    const creativeSize: number[] = parseCreativeSize(
        (stats.creative_size as GridRowDataStatsValue)?.value as string
    );

    return {
        type: getAdType(getStatsValue(stats.creative_type, 'value')),
        url: getStatsValue(stats.urlLink, 'url', ''),
        title: getStatsValue(stats.breakdown_name, 'text', ''),
        displayUrl: getStatsValue(stats.display_url, 'value', ''),
        brandName: getStatsValue(stats.brand_name, 'value', ''),
        description: getStatsValue(stats.description, 'value', ''),
        callToAction: getStatsValue(stats.call_to_action, 'value', ''),
        displayHostedImageUrl: getStatsValue(stats.image_urls, 'image', ''),
        hostedImageUrl: getStatsValue(stats.image_urls, 'square', ''),
        landscapeHostedImageUrl: getStatsValue(
            stats.image_urls,
            'landscape',
            ''
        ),
        portraitHostedImageUrl: getStatsValue(stats.image_urls, 'portrait', ''),
        hostedIconUrl: getStatsValue(stats.image_urls, 'icon', ''),
        imageWidth: creativeSize[0].toString(),
        imageHeight: creativeSize[1].toString(),
        adTag: getStatsValue(stats.image_urls, 'ad_tag', ''),
    };
}

function getStatsValue(
    statsValue: GridRowDataStatsValue | SubmissionStatus[],
    key: keyof GridRowDataStatsValue,
    defaultValue?: string
): string {
    return getValueOrDefault(
        (statsValue as GridRowDataStatsValue)?.[key] as string,
        defaultValue
    );
}

function getAdType(name: string): AdType {
    if (isDefined(name)) {
        return APP_OPTIONS.adTypes.find(item => item.name === name).value;
    }
    return null;
}

function parseCreativeSize(creativeSize: string): number[] {
    if (isDefined(creativeSize)) {
        return creativeSize.split('x').map(item => parseInt(item.trim(), 10));
    }
    return [DEFAULT_CREATIVE_WIDTH, DEFAULT_CREATIVE_HEIGHT];
}
