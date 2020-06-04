import {AccountAgency} from './account-agency';
import {Hack} from '../common/hack';
import {Deal} from '../common/deal';
import {User} from '../common/user';
import {AccountMediaSource} from './account-media-source';

export interface AccountExtras {
    archived: boolean;
    canRestore: boolean;
    isExternallyManaged: boolean;
    agencies: AccountAgency[];
    accountManagers: User[];
    salesRepresentatives: User[];
    csRepresentatives: User[];
    obRepresentatives: User[];
    hacks: Hack[];
    deals: Deal[];
    availableMediaSources: AccountMediaSource[];
}
