export interface DeepCleanConfig {
    cleanKeys?: string[];
    cleanValues?: any[];
    emptyArrays?: boolean;
    emptyObjects?: boolean;
    emptyStrings?: boolean;
    nullValues?: boolean;
    undefinedValues?: boolean;
}
