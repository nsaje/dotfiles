import {FieldErrors} from '../../../../../shared/types/field-errors';
import {NonFieldErrors} from '../../../../../shared/types/non-field-errors';

export class CreativesStoreFieldsErrorsState {
    id: FieldErrors = [];
    agencyId: FieldErrors = [];
    agencyName: FieldErrors = [];
    accountId: FieldErrors = [];
    accountName: FieldErrors = [];
    type: FieldErrors = [];
    url: FieldErrors = [];
    title: FieldErrors = [];
    displayUrl: FieldErrors = [];
    brandName: FieldErrors = [];
    description: FieldErrors = [];
    callToAction: FieldErrors = [];
    tags: FieldErrors = [];
    imageUrl: FieldErrors = [];
    iconUrl: FieldErrors = [];
    adTag: FieldErrors = [];
    videoAssetId: FieldErrors = [];
    trackers: FieldErrors = [];
    nonFieldErrors: NonFieldErrors = [];
}
