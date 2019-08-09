import {AccountAgency} from './account-agency';
import {Hack} from '../common/hack';
import {Deal} from '../common/deal';
import {User} from '../common/user';

export interface AccountExtras {
    archived: boolean;
    canArchive: boolean;
    canRestore: boolean;
    isExternallyManaged: boolean;
    agencies: AccountAgency[];
    accountManagers: User[];
    salesRepresentatives: User[];
    csRepresentatives: User[];
    obRepresentatives: User[];
    hacks: Hack[];
    deals: Deal[];
}
