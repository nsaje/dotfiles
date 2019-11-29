export interface PixelData {
    field: string;
    attribution: 'Click attribution' | 'View attribution';
    window: number;
    pixel: string;
    name: string;
    help: string;
    performance: 'Conversions' | 'CPA' | 'ROAS';
}
