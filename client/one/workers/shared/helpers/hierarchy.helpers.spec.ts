import {AccountEntity} from '../types/hierarchy';
import {EntityType} from '../workers.constants';
import * as hierarchyHelpers from './hierarchy.helpers';

describe('HierarchyHelpers', () => {
    it('should correctly build hierarchy', () => {
        const entities: AccountEntity[] = [
            {
                id: '123',
                name: 'Test account',
                campaigns: [],
            },
        ];

        expect(hierarchyHelpers.buildHierarchy(entities)).toEqual({
            ids: {
                accounts: {
                    '123': {
                        id: '123',
                        name: 'Test account',
                        parent: null,
                        type: EntityType.ACCOUNT,
                        data: {
                            id: '123',
                            name: 'Test account',
                            campaigns: [],
                        },
                        children: [],
                    },
                },
                campaigns: {},
                adGroups: {},
            },
            children: [
                {
                    id: '123',
                    name: 'Test account',
                    parent: null,
                    type: EntityType.ACCOUNT,
                    data: {
                        id: '123',
                        name: 'Test account',
                        campaigns: [],
                    },
                    children: [],
                },
            ],
        });
    });
});
