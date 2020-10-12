import {ChartMetricData} from './chart-metric-data';

export interface ChartCategory {
    name: string;
    description?: string;
    metrics: ChartMetricData[] | [];
    subcategories: ChartCategory | [];
    isNewFeature?: boolean;
}
