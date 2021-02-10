import {CreativeBatchStatus} from './creative-batch-status';
import {CreativeBatchMode, CreativeBatchType} from '../../../app.constants';

export interface CreativeBatch {
    id?: string;
    agencyId: string | null;
    accountId: string | null;
    type: CreativeBatchType;
    mode: CreativeBatchMode;
    name?: string;
    status?: CreativeBatchStatus;
    tags?: string[];
    imageCrop?: string;
    displayUrl?: string;
    brandName?: string;
    description?: string;
    callToAction?: string;
    createdBy?: string;
    createdDt?: Date;
}
