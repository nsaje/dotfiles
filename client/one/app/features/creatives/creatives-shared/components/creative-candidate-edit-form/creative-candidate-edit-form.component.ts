import './creative-candidate-edit-form.component.less';

import {
    ChangeDetectionStrategy,
    Component,
    EventEmitter,
    Input,
    OnChanges,
    Output,
    SimpleChanges,
} from '@angular/core';
import {CreativeCandidate} from '../../../../../core/creatives/types/creative-candidate';
import {CreativeCandidateFieldsErrorsState} from '../../types/creative-candidate-fields-errors-state';
import {ChangeEvent} from '../../../../../shared/types/change-event';
import {
    AdType,
    CreativeBatchType,
    ImageCrop,
} from '../../../../../app.constants';
import {isDefined} from '../../../../../shared/helpers/common.helpers';
import {
    CREATIVE_TYPES,
    IMAGE_CROPS,
    CALLS_TO_ACTION,
    AD_SIZES,
} from '../../creatives-shared.config';
import {FIELDS_CONFIG} from './creative-candidate-edit-form.config';
import {CreativeBatch} from '../../../../../core/creatives/types/creative-batch';
import {AdSizeConfig} from '../../types/ad-size-config';

interface ImageCropOption {
    name: string;
    value: ImageCrop;
}

interface AdTypeOption {
    id: AdType;
    name: string;
    batchType: CreativeBatchType;
}

interface CallToActionOption {
    name: string;
    value: string;
}

@Component({
    selector: 'zem-creative-candidate-edit-form',
    templateUrl: './creative-candidate-edit-form.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreativeCandidateEditFormComponent implements OnChanges {
    @Input()
    candidate: CreativeCandidate;
    @Input()
    candidateErrors: CreativeCandidateFieldsErrorsState;
    @Input()
    availableTags: string[];
    @Input()
    isLoadingTags: boolean = false;
    @Input()
    canUseExtraTrackers: boolean = false;
    @Output()
    candidateChange: EventEmitter<
        ChangeEvent<CreativeCandidate>
    > = new EventEmitter<ChangeEvent<CreativeCandidate>>();
    @Output()
    defaultsChange: EventEmitter<Partial<CreativeBatch>> = new EventEmitter<
        Partial<CreativeBatch>
    >();
    @Output()
    tagSearch: EventEmitter<string> = new EventEmitter<string>();

    AdType: typeof AdType = AdType;

    FIELDS_CONFIG = FIELDS_CONFIG;
    AD_SIZES: AdSizeConfig[] = AD_SIZES;
    IMAGE_CROPS: ImageCropOption[] = IMAGE_CROPS;

    adTypes: AdTypeOption[] = [];
    callsToAction: CallToActionOption[] = [];
    adTitleFieldLabel: string;

    ngOnChanges(changes: SimpleChanges): void {
        this.adTypes = this.getAdTypeOptions(this.candidate);
        this.callsToAction = this.getCallsToAction(this.candidate);
        this.adTitleFieldLabel = this.getAdTitleFieldLabel(this.candidate);
    }

    onFieldChange(key: keyof CreativeCandidate, value: any) {
        this.candidateChange.emit({
            target: this.candidate,
            changes: {
                [key]: value,
            },
        });
    }

    createCallToActionItem(name: string): CallToActionOption {
        return {name, value: name};
    }

    useCurrentFieldValueAsDefault(
        fieldName: keyof CreativeCandidate & keyof CreativeBatch
    ) {
        this.defaultsChange.emit({
            [fieldName]: this.candidate[fieldName],
        });
    }

    private getAdTypeOptions(candidate: CreativeCandidate): AdTypeOption[] {
        if (isDefined(candidate?.type)) {
            const currentBatchType: CreativeBatchType = CREATIVE_TYPES.find(
                type => type.id === candidate.type
            ).batchType;
            return CREATIVE_TYPES.filter(
                type => type.batchType === currentBatchType
            );
        } else {
            return [];
        }
    }

    private getCallsToAction(
        candidate: CreativeCandidate
    ): CallToActionOption[] {
        const callsToAction: CallToActionOption[] = [...CALLS_TO_ACTION];
        if (
            isDefined(candidate?.callToAction) &&
            !callsToAction
                .map(callToAction => callToAction.name)
                .includes(candidate.callToAction)
        ) {
            callsToAction.push(
                this.createCallToActionItem(candidate.callToAction)
            );
        }
        return callsToAction;
    }

    private getAdTitleFieldLabel(candidate: CreativeCandidate) {
        return [AdType.CONTENT, AdType.VIDEO].includes(candidate.type)
            ? 'Ad Title'
            : 'Ad Name';
    }
}
