import {CreativeBatchStatus} from './creative-batch-status';

export interface CreativeBatch {
    id?: string;
    agencyId: string | null;
    accountId: string | null;
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
