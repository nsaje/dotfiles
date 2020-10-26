import {CellRole} from '../../../smart-grid.component.constants';
import {PinnedRowRendererParams} from './types/pinned-row.renderer-params';

export const DEFAULT_PINNED_ROW_PARAMS: Partial<PinnedRowRendererParams> = {
    role: CellRole.Dimension,
};
